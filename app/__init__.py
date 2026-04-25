"""
NeuralAudit FastAPI Application Package

This package contains the production-ready FastAPI application with:
- Server configuration (server.py)
- API routers (routers/)
- Request/response schemas (schemas/)
- Dependency injection (dependencies/)

Usage:
    from app.server import app
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

from .server import app, create_app

__all__ = ["app", "create_app"]
