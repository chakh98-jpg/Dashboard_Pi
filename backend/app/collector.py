"""
System metrics collector using psutil
"""
import psutil
import platform
import os
from datetime import datetime, timedelta
from typing import Optional, List
from app.config import get_settings

settings = get_settings()


def get_cpu_temperature() -> Optional[float]:
    """
    Get CPU temperature (Raspberry Pi specific)
    Returns None if not available
    """
    try:
        # Try Raspberry Pi thermal zone
        if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = float(f.read().strip()) / 1000.0
                return round(temp, 1)
        
        # Try psutil sensors (Linux)
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                if entries:
                    return round(entries[0].current, 1)
        
        return None
    except Exception:
        return None


def format_uptime(seconds: int) -> str:
    """Format uptime in human readable format"""
    delta = timedelta(seconds=seconds)
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}j")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    
    return " ".join(parts)


def check_alerts(metrics: dict) -> List[str]:
    """Check metrics against thresholds and return alerts"""
    alerts = []
    
    if metrics["cpu_percent"] >= settings.cpu_alert_threshold:
        alerts.append(f"⚠️ CPU élevé: {metrics['cpu_percent']:.1f}%")
    
    if metrics["ram_percent"] >= settings.ram_alert_threshold:
        alerts.append(f"⚠️ RAM élevée: {metrics['ram_percent']:.1f}%")
    
    if metrics["disk_percent"] >= settings.disk_alert_threshold:
        alerts.append(f"⚠️ Disque presque plein: {metrics['disk_percent']:.1f}%")
    
    if metrics["cpu_temp"] and metrics["cpu_temp"] >= settings.temp_alert_threshold:
        alerts.append(f"🌡️ Température élevée: {metrics['cpu_temp']:.1f}°C")
    
    return alerts


def collect_metrics() -> dict:
    """
    Collect all system metrics
    Returns a dictionary with current system state
    """
    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # Memory
    memory = psutil.virtual_memory()
    ram_percent = memory.percent
    ram_used_gb = round(memory.used / (1024 ** 3), 2)
    ram_total_gb = round(memory.total / (1024 ** 3), 2)
    
    # Disk
    disk = psutil.disk_usage("/")
    disk_percent = disk.percent
    disk_used_gb = round(disk.used / (1024 ** 3), 2)
    disk_total_gb = round(disk.total / (1024 ** 3), 2)
    
    # Temperature
    cpu_temp = get_cpu_temperature()
    
    # Uptime
    boot_time = psutil.boot_time()
    uptime_seconds = int(datetime.now().timestamp() - boot_time)
    uptime_formatted = format_uptime(uptime_seconds)
    
    metrics = {
        "cpu_percent": round(cpu_percent, 1),
        "ram_percent": round(ram_percent, 1),
        "ram_used_gb": ram_used_gb,
        "ram_total_gb": ram_total_gb,
        "disk_percent": round(disk_percent, 1),
        "disk_used_gb": disk_used_gb,
        "disk_total_gb": disk_total_gb,
        "cpu_temp": cpu_temp,
        "uptime_seconds": uptime_seconds,
        "uptime_formatted": uptime_formatted,
    }
    
    # Check for alerts
    metrics["alerts"] = check_alerts(metrics)
    
    return metrics


def get_system_info() -> dict:
    """Get static system information"""
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    
    return {
        "hostname": platform.node(),
        "platform": platform.system(),
        "platform_version": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor() or "Unknown",
        "python_version": platform.python_version(),
        "boot_time": boot_time.isoformat(),
    }
