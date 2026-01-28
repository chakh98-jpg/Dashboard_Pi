"""
History API routes for accessing stored metrics
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from typing import List
from app.database import get_db
from app.models import Metric
from app.schemas import MetricResponse

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/metrics/history", response_model=List[MetricResponse])
async def get_metrics_history(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to retrieve"),
    limit: int = Query(default=500, ge=1, le=5000, description="Maximum records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical metrics from database
    
    - **hours**: Number of hours to look back (default: 24, max: 168)
    - **limit**: Maximum number of records (default: 500, max: 5000)
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    query = (
        select(Metric)
        .where(Metric.timestamp >= cutoff_time)
        .order_by(desc(Metric.timestamp))
        .limit(limit)
    )
    
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    return metrics


@router.get("/metrics/latest", response_model=MetricResponse)
async def get_latest_metric(db: AsyncSession = Depends(get_db)):
    """Get the most recent stored metric"""
    query = select(Metric).order_by(desc(Metric.timestamp)).limit(1)
    result = await db.execute(query)
    metric = result.scalar_one_or_none()
    
    if not metric:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No metrics found")
    
    return metric


@router.get("/metrics/stats")
async def get_metrics_stats(
    hours: int = Query(default=1, ge=1, le=24),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated statistics for the last N hours"""
    from sqlalchemy import func
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    query = select(
        func.avg(Metric.cpu_percent).label("avg_cpu"),
        func.max(Metric.cpu_percent).label("max_cpu"),
        func.min(Metric.cpu_percent).label("min_cpu"),
        func.avg(Metric.ram_percent).label("avg_ram"),
        func.max(Metric.ram_percent).label("max_ram"),
        func.avg(Metric.cpu_temp).label("avg_temp"),
        func.max(Metric.cpu_temp).label("max_temp"),
        func.count(Metric.id).label("sample_count")
    ).where(Metric.timestamp >= cutoff_time)
    
    result = await db.execute(query)
    row = result.one()
    
    return {
        "period_hours": hours,
        "sample_count": row.sample_count,
        "cpu": {
            "avg": round(row.avg_cpu, 1) if row.avg_cpu else 0,
            "max": round(row.max_cpu, 1) if row.max_cpu else 0,
            "min": round(row.min_cpu, 1) if row.min_cpu else 0,
        },
        "ram": {
            "avg": round(row.avg_ram, 1) if row.avg_ram else 0,
            "max": round(row.max_ram, 1) if row.max_ram else 0,
        },
        "temperature": {
            "avg": round(row.avg_temp, 1) if row.avg_temp else None,
            "max": round(row.max_temp, 1) if row.max_temp else None,
        }
    }
