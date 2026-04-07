"""API routers."""

from api.routers.debug import router as debug_router
from api.routers.download import router as download_router
from api.routers.health import router as health_router
from api.routers.insights import router as insights_router
from api.routers.libraries import router as libraries_router
from api.routers.og_images import router as og_images_router
from api.routers.plots import router as plots_router
from api.routers.proxy import router as proxy_router
from api.routers.seo import router as seo_router
from api.routers.specs import router as specs_router
from api.routers.stats import router as stats_router


__all__ = [
    "debug_router",
    "download_router",
    "health_router",
    "insights_router",
    "libraries_router",
    "og_images_router",
    "plots_router",
    "proxy_router",
    "seo_router",
    "specs_router",
    "stats_router",
]
