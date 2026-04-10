"""FastAPI application entry point."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Ensure data directories exist
    for directory in [settings.UPLOAD_DIR, settings.RAW_DIR, settings.PROCESSED_DIR]:
        os.makedirs(directory, exist_ok=True)

    logger.info("Baoyan recommendation system starting up...")

    # Initialize DB tables (in development mode)
    if settings.APP_ENV == "development":
        from app.db.session import engine
        from app.db.base import Base
        # Import all models to register them
        import app.models.user       # noqa
        import app.models.document   # noqa
        import app.models.knowledge  # noqa
        import app.models.recommendation  # noqa

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")

    yield

    logger.info("Baoyan recommendation system shutting down...")


app = FastAPI(
    title="保研推免定位器 API",
    description="CS Graduate School Recommendation System for Chinese undergraduate students",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for public access via tunnel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "baoyan-backend"}


@app.get("/")
async def root():
    return {
        "message": "保研推免定位器 API",
        "docs": "/docs",
        "health": "/health",
    }
