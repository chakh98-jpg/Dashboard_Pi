"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class MetricBase(BaseModel):
    """Base metric schema"""
    cpu_percent: float
    ram_percent: float
    ram_used_gb: float
    ram_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    cpu_temp: Optional[float] = None
    uptime_seconds: int


class MetricResponse(MetricBase):
    """Metric response with timestamp"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class CurrentMetrics(MetricBase):
    """Current system metrics"""
    uptime_formatted: str
    alerts: List[str] = []


class SystemInfo(BaseModel):
    """System information"""
    hostname: str
    platform: str
    platform_version: str
    architecture: str
    processor: str
    python_version: str
    boot_time: datetime
    

class AlertResponse(BaseModel):
    """Alert response schema"""
    id: int
    timestamp: datetime
    metric_type: str
    value: float
    threshold: float
    message: str
    acknowledged: bool
    
    class Config:
        from_attributes = True


class HistoryParams(BaseModel):
    """Query parameters for history endpoint"""
    hours: int = 24
    limit: int = 1000
