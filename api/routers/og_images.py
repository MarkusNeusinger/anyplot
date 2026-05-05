"""OG Image endpoints for branded social media preview images."""

import asyncio
import logging
from io import BytesIO
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from api.analytics import track_og_image
from api.cache import cache_key, get_cache, set_cache
from api.dependencies import optional_db
from core.database import SpecRepository
from core.images import create_branded_og_image, create_home_og_image, create_og_collage


logger = logging.getLogger(__name__)


# Bump this when the OG visual template changes — it's folded into every
# `cache_key()` call below so a deploy invalidates already-cached PNGs without
# needing a manual `clear_cache()`. Issue #5652 introduces the any.plot()
# visual identity, so we bump v1 → v2.
OG_VERSION = "v2"

# Static og:image (lazily generated once per process at first request)
_STATIC_OG_IMAGE: bytes | None = None


def _get_static_og_image() -> bytes:
    """Render the home/plots fallback OG image (memoized after a successful render).

    Previously read a hardcoded `api/static/og-image.png`; now it generates the
    new any.plot() hero-style card on the fly so a single source of truth in
    `core/images.py` controls the entire OG surface. Process-local memoisation
    means we only pay the render cost once per worker — but only on success,
    so a transient failure (font GCS hiccup, etc.) doesn't lock the worker
    into serving the legacy disk PNG until restart.
    """
    global _STATIC_OG_IMAGE
    if _STATIC_OG_IMAGE is not None:
        return _STATIC_OG_IMAGE

    try:
        result = create_home_og_image(theme="light")
        rendered = result if isinstance(result, bytes) else _image_to_bytes(result)
        _STATIC_OG_IMAGE = rendered  # only memoize successful dynamic output
        return rendered
    except Exception as exc:
        # Last-resort: serve the bundled static asset so the endpoint never
        # 500s if PIL/font loading is broken in a fresh container — but do
        # NOT memoize it, so the next request retries the dynamic path.
        # Log loudly so the regression is visible in production rather than
        # silently degrading to the legacy image.
        logger.warning("Dynamic OG generation failed, serving disk fallback: %s", exc, exc_info=True)
        path = Path(__file__).parent.parent / "static" / "og-image.png"
        try:
            return path.read_bytes()
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="Static OG image not available") from exc


def _image_to_bytes(img: Image.Image) -> bytes:
    """Convert a PIL Image to PNG bytes (only used by the static-fallback branch)."""
    buf = BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


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


@router.get("/{spec_id}/{language}/{library}.png")
async def get_branded_impl_image(
    spec_id: str, language: str, library: str, request: Request, db: AsyncSession | None = Depends(optional_db)
) -> Response:
    """Get a branded OG image for an implementation.

    Returns a 1200x630 PNG with anyplot.ai header and the plot image.
    """
    # Track og:image request (fire-and-forget)
    track_og_image(request, page="spec_detail", spec=spec_id, language=language, library=library)

    # Check cache first
    # Spec_id sits before the version so `clear_spec_cache(spec_id)` (which
    # patterns on `og:{spec_id}`) still invalidates this entry — see api/cache.py.
    key = cache_key("og", spec_id, OG_VERSION, language, library)
    cached = get_cache(key)
    if cached:
        return Response(content=cached, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})

    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    repo = SpecRepository(db)
    spec = await repo.get_by_id(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")

    # Find the implementation matching language + library
    impl = next(
        (i for i in spec.impls if i.library_id == library and i.library and i.library.language == language), None
    )
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
    key = cache_key("og", spec_id, OG_VERSION, "collage")
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
        # Labels are just the library id — chip color picks deterministically
        # off the trailing token, and the spec_id is now in the section title.
        labels = [impl.library_id for impl in selected_impls]

        # Create collage
        collage_bytes = create_og_collage(images, labels=labels, spec_id=spec_id)

        # Cache the result
        set_cache(key, collage_bytes)

        return Response(
            content=collage_bytes, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"}
        )

    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch images: {e}") from e
