"""FastAPI application entry point."""

from fastapi import FastAPI

from app import __version__

app = FastAPI(
    title="Headless Studio API",
    description="Automated digital product discovery, validation, and publishing system",
    version=__version__,
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": __version__}


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {"message": "Headless Studio API", "version": __version__}
