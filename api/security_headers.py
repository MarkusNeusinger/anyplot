"""The two security headers every API response carries, in one place.

`app/security-headers.conf` gives the website its headers through nginx.
api.anyplot.ai is a separate origin with no nginx in front of it, so it inherits
none of them — and served none until this module existed, apart from the pair
`/proxy/html` set by hand on that one response.

One place, because there are TWO exits from the app and only one of them is a
middleware. Starlette's `ServerErrorMiddleware` wraps every user middleware, so
when a route raises, `await call_next(request)` raises with it and the response
the registered `Exception` handler builds is produced OUTSIDE the stack — an
unhandled 500 would leave without headers while the middleware's docstring
claimed otherwise (Copilot review). Both paths call `stamp` instead.

Deliberately NOT `X-Frame-Options`: the SPA embeds `/proxy/html` in an iframe
from a different origin (`frame-src https://api.anyplot.ai` in the site's CSP),
and `SAMEORIGIN` would break every interactive plot preview.
"""

from __future__ import annotations

from typing import TypeVar

from starlette.responses import Response


# So a caller that hands in a JSONResponse gets a JSONResponse back — the
# exception handler's signature promises one, and a bare `Response` return would
# make the helper the reason mypy fails there.
ResponseT = TypeVar("ResponseT", bound=Response)

SECURITY_HEADERS = {
    # The API returns JSON, PNG and (on /proxy/html) HTML from the same host, so
    # content-type sniffing is exactly the confusion to forbid.
    "X-Content-Type-Options": "nosniff",
    # The same value the website sends, so a link followed out of an API-served
    # page leaks no path.
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


def stamp(response: ResponseT) -> ResponseT:
    """Add the baseline headers, keeping any a route set on purpose.

    `setdefault`, so a response with a reason to say something else — as
    `/proxy/html` does — keeps its own value.
    """
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response
