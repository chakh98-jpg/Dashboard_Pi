"""
SQLAlchemy models for metrics storage
"""
from sqlalchemy import Column, Integer, Float, DateTime, String
from sqlalchemy.sql import func
from app.database import Base


class Metric(Base):
    """Model for storing historical metrics"""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # System metrics
    cpu_percent = Column(Float, nullable=False)
    ram_percent = Column(Float, nullable=False)
    ram_used_gb = Column(Float, nullable=False)
    ram_total_gb = Column(Float, nullable=False)
    
    # Disk metrics
    disk_percent = Column(Float, nullable=False)
    disk_used_gb = Column(Float, nullable=False)
    disk_total_gb = Column(Float, nullable=False)
    
    # Temperature (Raspberry Pi specific)
    cpu_temp = Column(Float, nullable=True)
    
    # System info
    uptime_seconds = Column(Integer, nullable=False)


class Alert(Base):
    """Model for storing alerts history"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    metric_type = Column(String(50), nullable=False)  # cpu, ram, disk, temp
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    message = Column(String(255), nullable=False)
    acknowledged = Column(Integer, default=0)  # 0 = not ack, 1 = ack
