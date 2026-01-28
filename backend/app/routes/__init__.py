"""Routes package"""
from app.routes.metrics import router as metrics_router
from app.routes.history import router as history_router
from app.routes.files import router as files_router
from app.routes.system import router as system_router
from app.routes.docker import router as docker_router
from app.routes.processes import router as processes_router

__all__ = [
    "metrics_router", 
    "history_router",
    "files_router",
    "system_router",
    "docker_router",
    "processes_router"
]

