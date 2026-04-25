"""
FastAPI Server Configuration
Production-ready FastAPI application with middleware, error handling, and lifecycle management
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from datetime import datetime

from logger import logger
from config import API_DEBUG, API_HOST, API_PORT
from app.routers import (
    audit_router,
    batch_router,
    results_router,
    health_router,
)
from app.dependencies import cleanup


# ===================== Lifecycle Management =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events
    
    Startup:
        - Initialize logger
        - Log startup message
        
    Shutdown:
        - Clean up resources (pipeline, database)
        - Log shutdown message
    """
    # Startup event
    logger.info("=" * 80)
    logger.info("🚀 NeuralAudit API Starting")
    logger.info(f"📍 Server: {API_HOST}:{API_PORT}")
    logger.info(f"🔧 Debug Mode: {API_DEBUG}")
    logger.info("=" * 80)
    
    yield
    
    # Shutdown event
    logger.info("=" * 80)
    logger.info("🛑 NeuralAudit API Shutting Down")
    cleanup()
    logger.info("✅ Cleanup complete")
    logger.info("=" * 80)


# ===================== FastAPI App Creation =====================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application
    
    This function:
    1. Creates the FastAPI app instance
    2. Sets up CORS middleware for cross-origin requests
    3. Adds all routers (audit, batch, results, health)
    4. Sets up error handlers
    5. Adds middleware for request logging and performance monitoring
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    
    app = FastAPI(
        title="NeuralAudit API",
        description="🤖 AI-driven e-commerce product variant integrity system\n\n"
                   "Automatically audits product color variants on e-commerce platforms using "
                   "computer vision and machine learning.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # ===================== CORS Middleware =====================
    # Allow cross-origin requests from any domain
    # In production, restrict to specific domains
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Change to specific domains in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    
    # ===================== Request Logging Middleware =====================
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """
        Middleware to log all HTTP requests and responses
        Useful for debugging and monitoring
        """
        start_time = time.time()
        
        # Log incoming request
        logger.debug(
            f"📨 {request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.debug(
                f"📤 {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.3f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing {request.method} {request.url.path}: {e}")
            raise
    
    # ===================== Register Routers =====================
    # Health and utility endpoints
    app.include_router(health_router)
    
    # Audit endpoints (manual audits, single product)
    app.include_router(audit_router)
    
    # Batch processing endpoints
    app.include_router(batch_router)
    
    # Results endpoints
    app.include_router(results_router)
    
    # ===================== Global Exception Handler =====================
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Handle unhandled exceptions globally
        Returns JSON response with error details
        """
        logger.error(f"💥 Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": "Internal server error. Please check server logs.",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    # ===================== Root Endpoint =====================
    @app.get(
        "/",
        summary="API Root",
        description="Welcome message and API information"
    )
    async def root():
        """
        Root endpoint that provides API information
        
        Returns:
            JSONResponse: Welcome message and links to documentation
        """
        return JSONResponse({
            "status": "ok",
            "message": "NeuralAudit API",
            "version": "1.0.0",
            "documentation": {
                "swagger": "http://localhost:8000/docs",
                "redoc": "http://localhost:8000/redoc",
                "openapi": "http://localhost:8000/openapi.json",
            },
            "quick_start": {
                "health_check": "GET /health",
                "statistics": "GET /stats",
                "manual_audit": "POST /api/audit",
                "process_product": "POST /api/process-product",
                "batch_process": "POST /api/process-batch",
            },
        })
    
    logger.info("✅ FastAPI application created successfully")
    return app


# ===================== Application Instance =====================
# Create the FastAPI app instance to be imported and run
app = create_app()
