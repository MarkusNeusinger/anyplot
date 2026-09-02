"""Health and info endpoints."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.origin_gate import header_verdict
from api.version import APP_VERSION


router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to anyplot API", "version": APP_VERSION, "docs": "/docs", "health": "/health"}


@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint for Cloud Run — and the one place the origin gate
    can be observed.

    `origin_gate` reports what `api/origin_gate.py` makes of THIS request —
    `off` · `off-seen` · `ok` · `missing` · `mismatch`. `/health` is exempt from
    the gate, so the answer comes back on every route into the service: the
    `api.` host, the apex `/api/*` Worker, the site's nginx, the raw `run.app`.
    That is what makes the rollout measurable instead of a leap — with the
    Transform Rule already stamping but the gate still off, every path that must
    keep working has to answer `off-seen` before the switch is thrown. It
    reports the verdict, never the value, and tells a caller nothing about its
    own request it did not already know.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "anyplot-api",
            "version": APP_VERSION,
            "origin_gate": header_verdict(request),
        },
        status_code=200,
    )


@router.get("/hello/{name}")
async def hello(name: str):
    """Simple hello endpoint for testing."""
    return {"message": f"Hello, {name}!", "service": "anyplot"}
