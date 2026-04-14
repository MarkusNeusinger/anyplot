"""
FastAPI backend for anyplot platform.

AI-powered plotting examples that work with YOUR data.
"""

# Load .env file FIRST, before any other imports that might read env vars
from dotenv import load_dotenv  # noqa: E402, I001

load_dotenv()

import logging  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI, HTTPException, Request, Response  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from starlette.middleware.gzip import GZipMiddleware  # noqa: E402

from api.exceptions import (  # noqa: E402
    AnyplotException,
    anyplot_exception_handler,
    generic_exception_handler,
    http_exception_handler,
)
from api.mcp.server import mcp_server  # noqa: E402
from api.routers import (  # noqa: E402
    debug_router,
    download_router,
    health_router,
    insights_router,
    libraries_router,
    og_images_router,
    plots_router,
    proxy_router,
    seo_router,
    specs_router,
    stats_router,
)
from core.database import close_db, init_db, is_db_configured  # noqa: E402


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Create MCP HTTP app (needed for lifespan integration)
mcp_http_app = mcp_server.http_app(path="/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting anyplot API...")

    # Initialize database connection
    if is_db_configured():
        try:
            await init_db()
            logger.info("Database connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    # Initialize MCP server lifespan
    async with mcp_http_app.lifespan(app):
        logger.info("MCP server initialized")
        yield

    # Cleanup database connection
    logger.info("Shutting down anyplot API...")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="anyplot API",
    description="Backend API for anyplot.ai - plotting gallery across 9 libraries",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Register exception handlers
app.add_exception_handler(AnyplotException, anyplot_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Enable GZip compression for responses > 500 bytes
# This significantly reduces payload size for JSON API responses
# (e.g., /plots/filter: 301KB -> ~40KB with gzip)
# Note: GZip must be added before CORS so compression happens before CORS headers are added
app.add_middleware(GZipMiddleware, minimum_size=500)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://anyplot.ai"],
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],  # MCP session tracking
)


# Add cache headers middleware
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    """Add Cache-Control headers to API responses for better browser caching."""
    response: Response = await call_next(request)

    # Skip for non-GET requests or error responses
    if request.method != "GET" or response.status_code >= 400:
        return response

    path = request.url.path

    # Static data — changes only on deploy (10 min cache, 1h stale-while-revalidate)
    if path in ("/libraries", "/stats"):
        response.headers["Cache-Control"] = "public, max-age=600, stale-while-revalidate=3600"
    # Specs list (5 min cache, 1h stale-while-revalidate)
    elif path == "/specs":
        response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=3600"
    # Filter endpoint — most dynamic, moderate cache (1 min, 10 min stale)
    elif path == "/plots/filter":
        response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=600"
    # Individual spec details (5 min cache, 1h stale-while-revalidate)
    elif path.startswith("/specs/"):
        response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=3600"
    # Insights endpoints (5 min cache, 1h stale-while-revalidate)
    elif path.startswith("/insights/"):
        response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=3600"

    return response


# Mount MCP server for AI assistant integration
app.mount("/mcp", mcp_http_app)

# Register routers
app.include_router(health_router)
app.include_router(stats_router)
app.include_router(specs_router)
app.include_router(libraries_router)
app.include_router(plots_router)
app.include_router(insights_router)
app.include_router(download_router)
app.include_router(seo_router)
app.include_router(og_images_router)
app.include_router(proxy_router)
app.include_router(debug_router)


# ASGI middleware to handle /mcp without trailing slash
# This runs BEFORE FastAPI routing, avoiding the 307 redirect
# MCP clients like Claude CLI don't follow redirects
class MCPTrailingSlashMiddleware:
    """Rewrite /mcp to /mcp/ before routing to avoid 307 redirect."""

    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] == "/mcp":
            scope = scope.copy()
            scope["path"] = "/mcp/"
        await self.asgi_app(scope, receive, send)


# Wrap the FastAPI app with the middleware
# This must be done after all routers are registered
# Keep reference to FastAPI instance for tests
fastapi_app = app
app = MCPTrailingSlashMiddleware(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
