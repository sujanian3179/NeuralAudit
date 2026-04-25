"""
API routers for NeuralAudit
Each router handles a specific category of endpoints
"""
from .audit import router as audit_router
from .batch import router as batch_router
from .results import router as results_router
from .health import router as health_router

__all__ = [
    "audit_router",
    "batch_router",
    "results_router",
    "health_router",
]
