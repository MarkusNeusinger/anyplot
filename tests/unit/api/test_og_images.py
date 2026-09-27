"""
Tests for api/routers/og_images.py — OG image endpoints.

Covers:
- Static OG image loading (including FileNotFoundError, line 32)
- Home and plots OG image endpoints
- _get_http_client() creation
- _fetch_image() preferring the 800px derivative of prod-shaped preview URLs
  (plot-light.png / plot-dark.png, legacy plot.png), with a logged fallback
- Branded impl image: success, cache hit, no DB, not found, HTTP error,
  and the source URL it requests
- Spec collage image: success, no DB, not found, no previews, HTTP error
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from api.cache import clear_cache
from api.main import app, fastapi_app
from api.routers import og_images as og_images_module
from core.database import get_db


DB_CONFIG_PATCH = "api.dependencies.is_db_configured"

FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # Minimal PNG-like bytes

# Preview URLs shaped like production: since 2026-04-23 `preview_url` is
# `preview_url_light`, so every one ends in `/plot-light.png`. A legacy
# `/plot.png` fixture is what let the dead 800px branch stay green.
GCS_IMPL = "https://storage.googleapis.com/anyplot-images/plots/scatter-basic/python/matplotlib"
LIGHT_URL = f"{GCS_IMPL}/plot-light.png"
DARK_URL = f"{GCS_IMPL}/plot-dark.png"
LEGACY_URL = f"{GCS_IMPL}/plot.png"


def _fake_http_client(statuses: dict[str, int]) -> AsyncMock:
    """A stand-in for the shared httpx client: `get(url)` answers with the status
    mapped to that URL (404 for any URL not listed) and FAKE_PNG as the body."""

    def get(url: str) -> httpx.Response:
        status = statuses.get(url, 404)
        return httpx.Response(status, content=FAKE_PNG if status == 200 else b"", request=httpx.Request("GET", url))

    client = AsyncMock()
    client.get = AsyncMock(side_effect=get)
    return client


@pytest.fixture(autouse=True)
def _clear_cache_and_static():
    """Clear cache and reset the static OG image singleton before each test."""
    clear_cache()
    og_images_module._STATIC_OG_IMAGE = None


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db_client():
    """Test client with mocked database dependency."""
    mock_session = AsyncMock()

    async def mock_get_db():
        yield mock_session

    fastapi_app.dependency_overrides[get_db] = mock_get_db

    with patch(DB_CONFIG_PATCH, return_value=True):
        client = TestClient(app)
        yield client, mock_session

    fastapi_app.dependency_overrides.clear()


def _make_impl(library_id="matplotlib", preview_url=LIGHT_URL, quality_score=92.5, language="python"):
    """Helper to create a mock implementation."""
    impl = MagicMock()
    impl.library_id = library_id
    impl.library = MagicMock()
    impl.library.language = language
    impl.preview_url = preview_url
    impl.quality_score = quality_score
    return impl


def _make_spec(spec_id="scatter-basic", impls=None):
    """Helper to create a mock spec."""
    spec = MagicMock()
    spec.id = spec_id
    spec.impls = impls or []
    return spec


# ============================================================================
# Static OG Image
# ============================================================================


class TestStaticOgImage:
    """Tests for _get_static_og_image and home/plots endpoints."""

    def test_home_og_image_success(self, client) -> None:
        """Home OG image should return 200 with PNG content."""
        with (
            patch("api.routers.og_images._get_static_og_image", return_value=FAKE_PNG),
            patch("api.routers.og_images.track_og_image"),
        ):
            response = client.get("/og/home.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content == FAKE_PNG

    def test_home_og_image_with_filter_params(self, client) -> None:
        """Home OG image should pass filter params for tracking."""
        with (
            patch("api.routers.og_images._get_static_og_image", return_value=FAKE_PNG),
            patch("api.routers.og_images.track_og_image") as mock_track,
        ):
            response = client.get("/og/home.png?lib=plotly&dom=statistics")

        assert response.status_code == 200
        mock_track.assert_called_once()
        call_kwargs = mock_track.call_args
        assert call_kwargs.kwargs.get("page") == "home"
        assert call_kwargs.kwargs.get("filters") is not None

    def test_plots_og_image_success(self, client) -> None:
        """Plots OG image should return 200 with PNG content."""
        with (
            patch("api.routers.og_images._get_static_og_image", return_value=FAKE_PNG),
            patch("api.routers.og_images.track_og_image"),
        ):
            response = client.get("/og/plots.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_static_og_image_falls_back_to_disk_when_dynamic_fails(self, client) -> None:
        """Dynamic any.plot() generation is the primary path; the bundled
        `api/static/og-image.png` is the last-resort fallback if PIL/font
        loading is broken in the container.
        """
        with (
            patch("api.routers.og_images.create_home_og_image", side_effect=RuntimeError("PIL broken")),
            patch("pathlib.Path.read_bytes", return_value=FAKE_PNG),
            patch("api.routers.og_images.track_og_image"),
        ):
            response = client.get("/og/home.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_static_og_image_500_when_dynamic_and_disk_both_fail(self, client) -> None:
        """If dynamic generation AND the bundled static fallback both fail,
        return 500 — there's nothing to serve."""
        with (
            patch("api.routers.og_images.create_home_og_image", side_effect=RuntimeError("PIL broken")),
            patch("pathlib.Path.read_bytes", side_effect=FileNotFoundError("not found")),
            patch("api.routers.og_images.track_og_image"),
        ):
            response = client.get("/og/home.png")

        assert response.status_code == 500


# ============================================================================
# _fetch_image and _get_http_client
# ============================================================================


class TestFetchImage:
    """Tests for _fetch_image and _get_http_client internal functions."""

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            (LIGHT_URL, f"{GCS_IMPL}/plot-light_800.png"),
            (DARK_URL, f"{GCS_IMPL}/plot-dark_800.png"),
            (LEGACY_URL, f"{GCS_IMPL}/plot_800.png"),
        ],
        ids=["light", "dark", "legacy"],
    )
    async def test_fetch_image_requests_800px_variant_first(self, url, expected, caplog) -> None:
        """A full-size render is never downloaded when its 800px derivative exists."""
        mock_client = _fake_http_client({expected: 200})

        with patch("api.routers.og_images._get_http_client", return_value=mock_client):
            result = await og_images_module._fetch_image(url)

        assert result == FAKE_PNG
        mock_client.get.assert_awaited_once_with(expected)
        assert "falling back" not in caplog.text

    async def test_fetch_image_falls_back_to_original_with_warning(self, caplog) -> None:
        """A missing 800px derivative falls back to the original, and says so."""
        small_url = f"{GCS_IMPL}/plot-light_800.png"
        mock_client = _fake_http_client({small_url: 404, LIGHT_URL: 200})

        with (
            patch("api.routers.og_images._get_http_client", return_value=mock_client),
            caplog.at_level("WARNING", logger="api.routers.og_images"),
        ):
            result = await og_images_module._fetch_image(LIGHT_URL)

        assert result == FAKE_PNG
        assert [c.args[0] for c in mock_client.get.await_args_list] == [small_url, LIGHT_URL]
        warnings = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warnings) == 1
        assert small_url in warnings[0].getMessage()
        assert LIGHT_URL in warnings[0].getMessage()

    async def test_fetch_image_falls_back_on_transport_error(self) -> None:
        """A transport error on the derivative falls back to the original too."""
        ok = httpx.Response(200, content=FAKE_PNG, request=httpx.Request("GET", LIGHT_URL))
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[httpx.ConnectError("reset"), ok])

        with patch("api.routers.og_images._get_http_client", return_value=mock_client):
            result = await og_images_module._fetch_image(LIGHT_URL)

        assert result == FAKE_PNG
        assert mock_client.get.await_count == 2

    async def test_fetch_image_raises_when_original_also_fails(self) -> None:
        """If the fallback fails as well, the HTTP error reaches the endpoint (502)."""
        mock_client = _fake_http_client({})

        with (
            patch("api.routers.og_images._get_http_client", return_value=mock_client),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await og_images_module._fetch_image(LIGHT_URL)

        assert mock_client.get.await_count == 2

    @pytest.mark.parametrize("width", [400, 800, 1200])
    async def test_fetch_image_does_not_resuffix_a_variant(self, width) -> None:
        """A URL that already names a size variant is fetched as given."""
        variant = f"{GCS_IMPL}/plot-light_{width}.png"
        mock_client = _fake_http_client({variant: 200})

        with patch("api.routers.og_images._get_http_client", return_value=mock_client):
            result = await og_images_module._fetch_image(variant)

        assert result == FAKE_PNG
        mock_client.get.assert_awaited_once_with(variant)

    async def test_fetch_image_non_png_url(self) -> None:
        """A non-PNG URL has no derivative and is fetched as given."""
        url = "https://storage.example.com/scatter/image.jpg"
        mock_client = _fake_http_client({url: 200})

        with patch("api.routers.og_images._get_http_client", return_value=mock_client):
            result = await og_images_module._fetch_image(url)

        assert result == FAKE_PNG
        mock_client.get.assert_awaited_once_with(url)

    def test_get_http_client_creates_new(self) -> None:
        """_get_http_client should create a new client when none exists."""
        # Reset the module-level client
        og_images_module._http_client = None

        client = og_images_module._get_http_client()
        assert isinstance(client, httpx.AsyncClient)
        assert not client.is_closed

        # Cleanup
        og_images_module._http_client = None

    def test_get_http_client_reuses_existing(self) -> None:
        """_get_http_client should reuse an existing open client."""
        og_images_module._http_client = None
        client1 = og_images_module._get_http_client()
        client2 = og_images_module._get_http_client()
        assert client1 is client2

        # Cleanup
        og_images_module._http_client = None


# ============================================================================
# Branded Implementation Image
# ============================================================================


class TestBrandedImplImage:
    """Tests for GET /og/{spec_id}/{library}.png endpoint."""

    def test_branded_impl_image_success(self, db_client) -> None:
        """Should return a branded PNG for a valid spec+library."""
        client, _ = db_client

        impl = _make_impl(library_id="matplotlib")
        spec = _make_spec(spec_id="scatter-basic", impls=[impl])

        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(return_value=spec)

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.set_cache"),
            patch("api.routers.og_images.SpecRepository", return_value=mock_repo),
            patch("api.routers.og_images._fetch_image", new_callable=AsyncMock, return_value=FAKE_PNG),
            patch("api.routers.og_images.create_branded_og_image", return_value=FAKE_PNG),
        ):
            response = client.get("/og/scatter-basic/python/matplotlib.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_branded_impl_image_renders_from_800px_variant(self, db_client) -> None:
        """A cache miss for a prod-shaped preview downloads only the 800px derivative."""
        client, _ = db_client

        spec = _make_spec(spec_id="scatter-basic", impls=[_make_impl(library_id="matplotlib")])
        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(return_value=spec)
        small_url = f"{GCS_IMPL}/plot-light_800.png"
        http = _fake_http_client({small_url: 200, LIGHT_URL: 200})

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.set_cache"),
            patch("api.routers.og_images.SpecRepository", return_value=mock_repo),
            patch("api.routers.og_images._get_http_client", return_value=http),
            patch("api.routers.og_images.create_branded_og_image", return_value=FAKE_PNG) as render,
        ):
            response = client.get("/og/scatter-basic/python/matplotlib.png")

        assert response.status_code == 200
        http.get.assert_awaited_once_with(small_url)
        assert render.call_args.args[0] == FAKE_PNG

    def test_branded_impl_image_cache_hit(self, db_client) -> None:
        """Should return cached image without hitting DB."""
        client, _ = db_client

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=FAKE_PNG),
        ):
            response = client.get("/og/scatter-basic/python/matplotlib.png")

        assert response.status_code == 200
        assert response.content == FAKE_PNG

    def test_branded_impl_image_no_db(self, client) -> None:
        """Should return 503 when DB is not available."""
        with (
            patch(DB_CONFIG_PATCH, return_value=False),
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
        ):
            response = client.get("/og/scatter-basic/python/matplotlib.png")

        assert response.status_code == 503

    def test_branded_impl_image_spec_not_found(self, db_client) -> None:
        """Should return 404 when spec does not exist."""
        client, _ = db_client

        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(return_value=None)

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.SpecRepository", return_value=mock_repo),
        ):
            response = client.get("/og/nonexistent/python/matplotlib.png")

        assert response.status_code == 404

    def test_branded_impl_image_impl_not_found(self, db_client) -> None:
        """Should return 404 when spec exists but library impl is missing."""
        client, _ = db_client

        impl = _make_impl(library_id="seaborn")  # Different library than requested
        spec = _make_spec(spec_id="scatter-basic", impls=[impl])

        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(return_value=spec)

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.SpecRepository", return_value=mock_repo),
        ):
            response = client.get("/og/scatter-basic/python/matplotlib.png")

        assert response.status_code == 404

    def test_branded_impl_image_no_preview_url(self, db_client) -> None:
        """Should return 404 when impl has no preview_url."""
        client, _ = db_client

        impl = _make_impl(library_id="matplotlib", preview_url=None)
        spec = _make_spec(spec_id="scatter-basic", impls=[impl])

        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(return_value=spec)

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.SpecRepository", return_value=mock_repo),
        ):
            response = client.get("/og/scatter-basic/python/matplotlib.png")

        assert response.status_code == 404

    def test_branded_impl_image_http_error(self, db_client) -> None:
        """Should return 502 when image fetch fails with HTTPError."""
        client, _ = db_client

        impl = _make_impl(library_id="matplotlib")
        spec = _make_spec(spec_id="scatter-basic", impls=[impl])

        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(return_value=spec)

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.SpecRepository", return_value=mock_repo),
            patch(
                "api.routers.og_images._fetch_image",
                new_callable=AsyncMock,
                side_effect=httpx.HTTPError("connection failed"),
            ),
        ):
            response = client.get("/og/scatter-basic/python/matplotlib.png")

        assert response.status_code == 502


# ============================================================================
# Spec Collage Image
# ============================================================================


class TestSpecCollageImage:
    """Tests for GET /og/{spec_id}.png endpoint."""

    def test_spec_collage_success(self, db_client) -> None:
        """Should return a collage PNG for a spec with multiple implementations."""
        client, _ = db_client

        impls = [
            _make_impl(library_id="matplotlib", quality_score=95.0),
            _make_impl(library_id="seaborn", quality_score=90.0),
        ]
        spec = _make_spec(spec_id="scatter-basic", impls=impls)

        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(return_value=spec)

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.set_cache"),
            patch("api.routers.og_images.SpecRepository", return_value=mock_repo),
            patch("api.routers.og_images._fetch_image", new_callable=AsyncMock, return_value=FAKE_PNG),
            patch("api.routers.og_images.create_og_collage", return_value=FAKE_PNG),
        ):
            response = client.get("/og/scatter-basic.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_spec_collage_renders_from_800px_variants(self, db_client) -> None:
        """Every collage source on a cache miss is the 800px derivative, never the original."""
        client, _ = db_client

        libraries = ["matplotlib", "seaborn", "plotly", "bokeh", "altair", "plotnine", "pygal"]
        base = "https://storage.googleapis.com/anyplot-images/plots/scatter-basic/python"
        impls = [
            _make_impl(library_id=lib, preview_url=f"{base}/{lib}/plot-light.png", quality_score=90.0 - i)
            for i, lib in enumerate(libraries)
        ]
        spec = _make_spec(spec_id="scatter-basic", impls=impls)
        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(return_value=spec)
        # Top six by quality; the seventh (pygal) is not fetched at all.
        expected = {f"{base}/{lib}/plot-light_800.png" for lib in libraries[:6]}
        http = _fake_http_client(dict.fromkeys(expected, 200))

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.set_cache"),
            patch("api.routers.og_images.SpecRepository", return_value=mock_repo),
            patch("api.routers.og_images._get_http_client", return_value=http),
            patch("api.routers.og_images.create_og_collage", return_value=FAKE_PNG) as render,
        ):
            response = client.get("/og/scatter-basic.png")

        assert response.status_code == 200
        assert {c.args[0] for c in http.get.await_args_list} == expected
        assert http.get.await_count == 6
        assert render.call_args.args[0] == [FAKE_PNG] * 6

    def test_spec_collage_cache_hit(self, db_client) -> None:
        """Should return cached collage without hitting DB."""
        client, _ = db_client

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=FAKE_PNG),
        ):
            response = client.get("/og/scatter-basic.png")

        assert response.status_code == 200
        assert response.content == FAKE_PNG

    def test_spec_collage_no_db(self, client) -> None:
        """Should return 503 when DB is not available."""
        with (
            patch(DB_CONFIG_PATCH, return_value=False),
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
        ):
            response = client.get("/og/scatter-basic.png")

        assert response.status_code == 503

    def test_spec_collage_spec_not_found(self, db_client) -> None:
        """Should return 404 when spec does not exist."""
        client, _ = db_client

        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(return_value=None)

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.SpecRepository", return_value=mock_repo),
        ):
            response = client.get("/og/nonexistent.png")

        assert response.status_code == 404

    def test_spec_collage_no_previews(self, db_client) -> None:
        """Should return 404 when all impls lack preview_url."""
        client, _ = db_client

        impl = _make_impl(library_id="matplotlib", preview_url=None)
        spec = _make_spec(spec_id="scatter-basic", impls=[impl])

        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(return_value=spec)

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.SpecRepository", return_value=mock_repo),
        ):
            response = client.get("/og/scatter-basic.png")

        assert response.status_code == 404

    def test_spec_collage_http_error(self, db_client) -> None:
        """Should return 502 when image fetch fails with HTTPError."""
        client, _ = db_client

        impl = _make_impl(library_id="matplotlib")
        spec = _make_spec(spec_id="scatter-basic", impls=[impl])

        mock_repo = MagicMock()
        mock_repo.get_by_id = AsyncMock(return_value=spec)

        with (
            patch("api.routers.og_images.track_og_image"),
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.SpecRepository", return_value=mock_repo),
            patch(
                "api.routers.og_images._fetch_image",
                new_callable=AsyncMock,
                side_effect=httpx.HTTPError("connection failed"),
            ),
        ):
            response = client.get("/og/scatter-basic.png")

        assert response.status_code == 502
