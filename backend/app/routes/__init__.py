"""Routes package"""
from app.routes.metrics import router as metrics_router
from app.routes.history import router as history_router

__all__ = ["metrics_router", "history_router"]
