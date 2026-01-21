"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
import os
from contextlib import asynccontextmanager

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings
from backend.api.routes import chat_router, auth_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting AarthikAI Backend API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Max memory: {settings.max_memory_mb}MB")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AarthikAI Backend API")


# Create FastAPI app
app = FastAPI(
    title="AarthikAI Backend API",
    description="Backend API for AarthikAI Financial Intelligence Chatbot",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AarthikAI Backend API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for AWS/Docker.
    
    Returns:
        Health status with basic system info
    """
    import psutil
    
    # Get memory usage
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    return {
        "status": "healthy",
        "memory_mb": round(memory_mb, 2),
        "max_memory_mb": settings.max_memory_mb,
        "environment": settings.environment
    }


@app.get("/metrics")
async def metrics():
    """
    Metrics endpoint for monitoring.
    
    Returns:
        System metrics in Prometheus-compatible format
    """
    import psutil
    
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_percent = process.cpu_percent(interval=0.1)
    
    return {
        "memory_mb": round(memory_mb, 2),
        "memory_percent": round((memory_mb / settings.max_memory_mb) * 100, 2),
        "cpu_percent": round(cpu_percent, 2),
        "environment": settings.environment
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.environment == "development" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
