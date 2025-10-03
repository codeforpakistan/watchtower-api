import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings, setup_logging
from app.api.api import api_router
from app.services.scheduler import get_scheduler

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting Watchtower API...")

    # Start the scheduler
    try:
        scheduler = get_scheduler()
        scheduler.start()
        logger.info("✅ Scheduler initialized and started")
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")

    logger.info("🎉 Watchtower API is ready!")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Watchtower API...")

    try:
        scheduler = get_scheduler()
        scheduler.stop()
        logger.info("✅ Scheduler stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {e}")

    logger.info("👋 Watchtower API shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Government website monitoring and accountability platform",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Watchtower API",
        "version": "0.1.0",
        "docs": f"{settings.API_V1_STR}/docs",
        "description": "Government website monitoring and accountability platform"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    scheduler = get_scheduler()
    scheduler_status = scheduler.get_status()

    return {
        "status": "healthy",
        "version": "0.1.0",
        "scheduler": scheduler_status
    }