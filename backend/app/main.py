"""
Headless Studio - FastAPI Application
AI-powered digital product factory
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import discovery, landing_pages, validation, gates

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    logger.info(f"Starting Headless Studio API (Phase {settings.current_phase})")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Features: organic_validation={settings.enable_organic_validation}, "
                f"paid_validation={settings.enable_paid_validation}")
    yield
    # Shutdown
    logger.info("Shutting down Headless Studio API")


app = FastAPI(
    title="Headless Studio API",
    description="AI-powered digital product factory - Discovery, Validation, Manufacturing, Sales",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred" if settings.is_production else str(exc),
        },
    )


# =============================================================================
# Health & Status Endpoints
# =============================================================================


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information."""
    return {
        "name": "Headless Studio API",
        "version": "0.1.0",
        "phase": settings.current_phase,
        "status": "operational",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "phase": settings.current_phase,
    }


@app.get("/config", tags=["Health"])
async def get_config():
    """Get current configuration (non-sensitive)."""
    return {
        "environment": settings.environment,
        "phase": settings.current_phase,
        "features": {
            "organic_validation": settings.enable_organic_validation,
            "paid_validation": settings.enable_paid_validation,
            "pinterest_auto": settings.enable_pinterest_auto,
            "seo_clustering": settings.enable_seo_clustering,
        },
        "limits": {
            "max_concurrent_llm_requests": settings.max_concurrent_llm_requests,
            "max_opportunities_per_run": settings.max_opportunities_per_run,
            "duplicate_lookback_days": settings.duplicate_lookback_days,
        },
    }


# =============================================================================
# Router Registration (Add as implemented)
# =============================================================================

# Phase 0.2: Discovery (X/Grok primary, Reddit supplementary)
app.include_router(discovery.router, prefix="/api/discovery", tags=["Discovery"])

# Phase 0.5: Landing Pages (served from FastAPI, not Supabase Edge Functions)
app.include_router(landing_pages.router, tags=["Landing Pages"])

# Phase 0.4: Scoring
# from app.routers import scoring
# app.include_router(scoring.router, prefix="/api/scoring", tags=["Scoring"])

# Phase 0.7: Validation
app.include_router(validation.router, prefix="/api/validation", tags=["Validation"])

# Phase 0.8: Gates
app.include_router(gates.router, prefix="/api/gates", tags=["Gates"])

# Phase 1: Manufacturing
# from app.routers import manufacturing
# app.include_router(manufacturing.router, prefix="/api/manufacturing", tags=["Manufacturing"])

# Phase 1: Sales
# from app.routers import sales
# app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
    )
