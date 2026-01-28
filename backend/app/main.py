"""
Main FastAPI application for Raspberry Pi Dashboard
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import delete

from app.config import get_settings
from app.database import init_db, async_session
from app.models import Metric
from app.collector import collect_metrics
from app.websocket import manager
from app.routes import (
    metrics_router, 
    history_router, 
    files_router, 
    system_router,
    docker_router,
    processes_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Background task flag
background_task_running = False


async def collect_and_store_metrics():
    """Background task to collect and store metrics periodically"""
    global background_task_running
    background_task_running = True
    
    logger.info("Starting metrics collection background task")
    
    while background_task_running:
        try:
            # Collect metrics
            metrics = collect_metrics()
            
            # Store in database
            async with async_session() as session:
                metric = Metric(
                    cpu_percent=metrics["cpu_percent"],
                    ram_percent=metrics["ram_percent"],
                    ram_used_gb=metrics["ram_used_gb"],
                    ram_total_gb=metrics["ram_total_gb"],
                    disk_percent=metrics["disk_percent"],
                    disk_used_gb=metrics["disk_used_gb"],
                    disk_total_gb=metrics["disk_total_gb"],
                    cpu_temp=metrics["cpu_temp"],
                    uptime_seconds=metrics["uptime_seconds"]
                )
                session.add(metric)
                await session.commit()
            
            # Broadcast to WebSocket clients
            await manager.broadcast({
                "type": "metrics",
                "data": metrics,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Log occasionally
            if manager.connection_count > 0:
                logger.debug(f"Broadcast to {manager.connection_count} clients")
            
        except Exception as e:
            logger.error(f"Error in metrics collection: {e}")
        
        await asyncio.sleep(settings.collection_interval)


async def cleanup_old_metrics():
    """Background task to clean up old metrics"""
    while background_task_running:
        try:
            cutoff = datetime.utcnow() - timedelta(hours=settings.history_retention_hours)
            
            async with async_session() as session:
                stmt = delete(Metric).where(Metric.timestamp < cutoff)
                result = await session.execute(stmt)
                await session.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Cleaned up {result.rowcount} old metrics")
        
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
        
        # Run cleanup every hour
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global background_task_running
    
    # Startup
    logger.info("Starting Dashboard API...")
    await init_db()
    logger.info("Database initialized")
    
    # Start background tasks
    collector_task = asyncio.create_task(collect_and_store_metrics())
    cleanup_task = asyncio.create_task(cleanup_old_metrics())
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    background_task_running = False
    collector_task.cancel()
    cleanup_task.cancel()
    
    try:
        await collector_task
    except asyncio.CancelledError:
        pass
    
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Real-time monitoring dashboard for Raspberry Pi",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(metrics_router)
app.include_router(history_router)
app.include_router(files_router)
app.include_router(system_router)
app.include_router(docker_router)
app.include_router(processes_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await manager.connect(websocket)
    try:
        # Send initial metrics immediately
        metrics = collect_metrics()
        await websocket.send_json({
            "type": "metrics",
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive
        while True:
            try:
                # Wait for client messages (heartbeat)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=settings.ws_heartbeat_interval
                )
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send ping to check if client is alive
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


@app.get("/")
async def root():
    """Serve frontend (if mounted)"""
    return {"message": "Dashboard API running", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
