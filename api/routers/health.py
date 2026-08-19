"""Health and info endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.version import APP_VERSION


router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to anyplot API", "version": APP_VERSION, "docs": "/docs", "health": "/health"}


@router.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return JSONResponse(
        content={"status": "healthy", "service": "anyplot-api", "version": APP_VERSION}, status_code=200
    )


@router.get("/hello/{name}")
async def hello(name: str):
    """Simple hello endpoint for testing."""
    return {"message": f"Hello, {name}!", "service": "anyplot"}
