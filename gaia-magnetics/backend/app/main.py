"""
Gaia Geophysics API - Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings, ensure_temp_dir
from .database import init_db, engine, Base
from .routes import jobs_router, health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Runs on startup and shutdown.
    """
    # Startup
    print("Starting Gaia Geophysics API...")
    
    # Ensure temp directory exists
    ensure_temp_dir()
    
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized")
    
    yield
    
    # Shutdown
    print("Shutting down Gaia Geophysics API...")


# Create FastAPI application
app = FastAPI(
    title="Gaia Geophysics API",
    description="Automated geophysical survey prediction platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        f"https://{settings.domain}",
        f"http://{settings.domain}"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs_router, prefix="/api")
app.include_router(health_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "Gaia Geophysics API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Gaia Geophysics API",
        "endpoints": {
            "jobs": "/api/jobs",
            "health": "/api/health"
        }
    }
