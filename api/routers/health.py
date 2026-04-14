"""Health and info endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse


router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to anyplot API", "version": "0.2.0", "docs": "/docs", "health": "/health"}


@router.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return JSONResponse(content={"status": "healthy", "service": "anyplot-api", "version": "0.2.0"}, status_code=200)


@router.get("/hello/{name}")
async def hello(name: str):
    """Simple hello endpoint for testing."""
    return {"message": f"Hello, {name}!", "service": "anyplot"}
