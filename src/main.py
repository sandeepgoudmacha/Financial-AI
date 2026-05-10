"""
Valura AI — Application Entry Point.

FastAPI application factory with lifespan management,
router registration, and service initialization.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.dependencies import get_session_manager, get_tool_registry, get_llm_service
from src.api.middleware import setup_middleware
from src.api.router import router
from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    settings = get_settings()
    setup_logging(level=settings.log_level, json_format=not settings.debug)

    logger = get_logger("main")
    logger.info("🚀 Valura AI starting up...")

    # Initialize services
    session_mgr = get_session_manager()
    await session_mgr.initialize()
    logger.info("✅ Session database initialized")

    tool_registry = get_tool_registry()
    logger.info(f"✅ Tool registry loaded: {tool_registry.count} tools")

    logger.info("✅ Valura AI is ready!")

    yield

    # Shutdown
    logger.info("👋 Valura AI shutting down...")
    llm = get_llm_service()
    await llm.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Financial AI",
        description="Production-grade multi-agent financial intelligence platform",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Setup middleware
    setup_middleware(app)

    # Register routers
    app.include_router(router, prefix="/api/v1", tags=["chat"])

    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
