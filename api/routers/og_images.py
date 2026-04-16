"""OG Image endpoints for branded social media preview images."""

import asyncio
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.analytics import track_og_image
from api.cache import cache_key, get_cache, set_cache
from api.dependencies import optional_db
from core.database import SpecRepository
from core.images import create_branded_og_image, create_og_collage


# Static og:image (loaded once at startup)
_STATIC_OG_IMAGE: bytes | None = None


def _get_static_og_image() -> bytes:
    """Load static og-image.png (cached in memory)."""
    global _STATIC_OG_IMAGE
    if _STATIC_OG_IMAGE is None:
        # Use api/static/ which is bundled in the Docker image
        path = Path(__file__).parent.parent / "static" / "og-image.png"
        try:
            _STATIC_OG_IMAGE = path.read_bytes()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail="Static OG image not found") from exc
    return _STATIC_OG_IMAGE


router = APIRouter(prefix="/og", tags=["og-images"])


@router.get("/home.png")
async def get_home_og_image(request: Request) -> Response:
    """OG image for home page with tracking.

    Supports filter params (e.g., ?lib=plotly&dom=statistics) for tracking shared filtered URLs.
    """
    # Capture filter params for tracking (e.g., ?lib=plotly&dom=statistics)
    filters = dict(request.query_params) if request.query_params else None
    track_og_image(request, page="home", filters=filters)

    return Response(
        content=_get_static_og_image(), media_type="image/png", headers={"Cache-Control": "public, max-age=86400"}
    )


@router.get("/plots.png")
async def get_plots_og_image(request: Request) -> Response:
    """OG image for plots page with tracking."""
    track_og_image(request, page="plots")

    return Response(
        content=_get_static_og_image(), media_type="image/png", headers={"Cache-Control": "public, max-age=86400"}
    )


_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    """Get or create a shared httpx client for connection reuse (avoids per-request TLS handshakes)."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=30.0, limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
    return _http_client


async def _fetch_image(url: str) -> bytes:
    """Fetch an image from a URL, trying the 800px variant first for efficiency."""
    client = _get_http_client()
    # Prefer smaller responsive variant for OG collage (each slot is ~400px wide)
    if url and url.endswith("/plot.png"):
        small_url = url.replace("/plot.png", "/plot_800.png")
        try:
            response = await client.get(small_url)
            response.raise_for_status()
            return response.content
        except Exception:
            pass  # Fall back to original
    response = await client.get(url)
    response.raise_for_status()
    return response.content


@router.get("/{spec_id}/{library}.png")
async def get_branded_impl_image(
    spec_id: str, library: str, request: Request, db: AsyncSession | None = Depends(optional_db)
) -> Response:
    """Get a branded OG image for an implementation.

    Returns a 1200x630 PNG with anyplot.ai header and the plot image.
    """
    # Track og:image request (fire-and-forget)
    track_og_image(request, page="spec_detail", spec=spec_id, library=library)

    # Check cache first
    key = cache_key("og", spec_id, library)
    cached = get_cache(key)
    if cached:
        return Response(content=cached, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})

    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    repo = SpecRepository(db)
    spec = await repo.get_by_id(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")

    # Find the implementation
    impl = next((i for i in spec.impls if i.library_id == library), None)
    if not impl or not impl.preview_url:
        raise HTTPException(status_code=404, detail="Implementation not found")

    try:
        # Fetch the original plot image
        image_bytes = await _fetch_image(impl.preview_url)

        # Create branded image
        branded_bytes = create_branded_og_image(image_bytes, spec_id=spec_id, library=library)

        # Cache the result
        set_cache(key, branded_bytes)

        return Response(
            content=branded_bytes, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"}
        )

    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch image: {e}") from e


@router.get("/{spec_id}.png")
async def get_spec_collage_image(
    spec_id: str, request: Request, db: AsyncSession | None = Depends(optional_db)
) -> Response:
    """Get a collage OG image for a spec (showing top 6 implementations by quality).

    Returns a 1200x630 PNG with anyplot.ai branding and a 2x3 grid of implementations,
    sorted by quality_score descending.
    """
    # Track og:image request (fire-and-forget)
    track_og_image(request, page="spec_overview", spec=spec_id)

    # Check cache first
    key = cache_key("og", spec_id, "collage")
    cached = get_cache(key)
    if cached:
        return Response(content=cached, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})

    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    repo = SpecRepository(db)
    spec = await repo.get_by_id(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")

    # Get implementations with preview images
    impls_with_preview = [i for i in spec.impls if i.preview_url]
    if not impls_with_preview:
        raise HTTPException(status_code=404, detail="No implementations with previews")

    # Sort by quality_score (descending) and take top 6 for 2x3 grid
    sorted_impls = sorted(
        impls_with_preview, key=lambda i: i.quality_score if i.quality_score is not None else 0, reverse=True
    )
    selected_impls = sorted_impls[:6]

    try:
        # Fetch all images in parallel
        images = list(await asyncio.gather(*[_fetch_image(impl.preview_url) for impl in selected_impls]))
        labels = [f"{spec_id} · {impl.library_id}" for impl in selected_impls]

        # Create collage
        collage_bytes = create_og_collage(images, labels=labels)

        # Cache the result
        set_cache(key, collage_bytes)

        return Response(
            content=collage_bytes, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"}
        )

    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch images: {e}") from e
