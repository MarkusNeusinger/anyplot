"""The relay page of the agent chat's interactive preview (`api/preview_relay.py`, JS-4b-2).

Static and unauthenticated on purpose: it holds no data and takes no token, and it sits outside
`/debug/*`, so Cloudflare Access, which guards that prefix, does not stand in front of it.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from api.preview_relay import RELAY_PATH, relay_headers, relay_html
from core.config import settings


router = APIRouter(tags=["preview"])

_BODY = relay_html(settings.cors_origins)
_HEADERS = relay_headers(settings.cors_origins)


@router.get(RELAY_PATH, include_in_schema=False)
async def preview_relay() -> HTMLResponse:
    """The relay: one page from the chat into a sandboxed frame; every response is the same."""
    return HTMLResponse(_BODY, headers=_HEADERS)
