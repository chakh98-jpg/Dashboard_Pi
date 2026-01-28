"""
Metrics API routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.collector import collect_metrics, get_system_info
from app.schemas import CurrentMetrics, SystemInfo

router = APIRouter(prefix="/api", tags=["metrics"])


@router.get("/metrics", response_model=CurrentMetrics)
async def get_current_metrics():
    """Get current system metrics"""
    metrics = collect_metrics()
    return CurrentMetrics(**metrics)


@router.get("/system", response_model=SystemInfo)
async def get_system():
    """Get system information"""
    info = get_system_info()
    return SystemInfo(**info)


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "dashboard-api"}
