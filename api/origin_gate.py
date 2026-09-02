"""Shared-secret gate that closes the direct `*.run.app` door.

Both Cloud Run services stand with `ingress=all` — there is no load balancer,
and putting one in front would cost more per month than the services do. So the
API answers on two addresses: `https://api.anyplot.ai`, which is proxied by
Cloudflare, and the raw `*.run.app` URL, which is not. Everything Cloudflare
enforces for this site — the bot challenge, the WAF, the cache that makes the
`public, max-age=300` reads free — is one URL away from being bypassed, and
`api/request_context.py` already documents callers doing it.

A Cloudflare Transform Rule stamps `X-Origin-Secret: <secret>` onto every
request it proxies for `api.anyplot.ai`. This middleware requires that header,
so a caller who skips the edge is refused with 403 before the request costs
anything. It is not authentication — it says "you came through the front door",
nothing about who you are; `api/dependencies.py` still decides what a caller may
do on the `/debug/*` routes.

One path stamps it itself rather than getting it from the rule: `anyplot.ai/api/*`
runs through a Cloudflare Worker, and a Worker subrequest to a host in the SAME
zone skips that zone's Transform Rules (measured during kurrentschrift's rollout;
the Worker's source now lives in `infra/cloudflare/`).

**The check is OFF unless `ORIGIN_SECRET` is set.** That is the rollback: take
the variable off the Cloud Run service, then promote the resulting revision —
this service pins traffic to a named revision, so a new one serves nothing until
it is promoted. Local development and the test suite therefore never see the
gate, and the rollout can put the code in production long before the rule and
the secret exist.

Exempt by path, and only these two:

* `/health` — the deploy's pre-traffic smoke probes the candidate revision on
  its `run.app` tag URL, which by definition never passes the edge. Gating it
  would make every deploy fail closed.
* `/debug/cache/invalidate` — the one legitimate caller that has no front door.
  `sync-postgres.yml` flushes the cache from a GitHub runner at the end of each
  sync, and it posts to the direct `*.run.app` URL *on purpose*: Cloudflare's
  bot challenge answers an unauthenticated curl POST against `api.anyplot.ai`
  with a 403 HTML page. The endpoint carries its own shared secret
  (`CACHE_INVALIDATE_TOKEN`, constant-time compared) and returns 503 when none
  is configured, so it is gated — just by a different lock. Sending the origin
  secret from CI instead would let this exemption go; that needs a repository
  secret and a workflow change, and is named as the follow-up in the PR that
  introduced this file.

`/seo-proxy/…` is deliberately NOT exempt, though the sibling repo exempts it
belt-and-braces. The site's nginx fetches the prerendered pages over
`https://api.anyplot.ai` (`app/nginx.conf` `@seo_proxy` and `@seo_proxy_python`),
so that path does pass the edge and does carry the header — while an exemption
would leave the most expensive reads in the API open on the direct URL: a cache
miss or an unknown id queries `SpecRepository`/`ImplRepository`, and a crawler
user agent schedules an outbound Plausible event per request. That is precisely
the cost this gate exists to refuse (Copilot review). The rollout measures the
crawler path end to end before arming, and `bot-serving-check.yml` runs daily,
so being wrong here is loud rather than silent.

`OPTIONS` never reaches the gate in the shipped stack — `CORSMiddleware` sits
outside it (`api/main.py`) and answers a preflight itself — but it is let
through explicitly anyway: a browser cannot attach a custom header to a
preflight, so a gate that refused one would break every cross-origin call on the
site rather than protecting anything. The exemption is what makes that
independent of where the middleware ends up in the stack.
"""

from __future__ import annotations

import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from core.config import settings


ORIGIN_SECRET_HEADER = "x-origin-secret"

# Exact paths only, no prefixes: a prefix exemption is how a gate quietly grows
# a hole. See the module docstring for what each of these two buys, and why
# `/seo-proxy/…` is not among them.
EXEMPT_PATHS = frozenset({"/health", "/debug/cache/invalidate"})


def _matches(presented: str, expected: str) -> bool:
    """Constant-time compare of the presented header against the secret.

    Compared as BYTES, not as `str`: `secrets.compare_digest` raises TypeError
    when either `str` holds a non-ASCII character, and a header value reaches
    here latin-1-decoded straight from the wire. So a caller could put one byte
    ≥ 0x80 in `X-Origin-Secret` and turn every refusal into an unhandled 500 —
    an unauthenticated way to make the gate expensive instead of cheap (Copilot
    review). Encoding first removes the restriction and the whole class of
    problem, and covers a non-ASCII secret at the other end too.
    """
    return secrets.compare_digest(presented.encode("utf-8"), expected.encode("utf-8"))


def gate_is_armed() -> bool:
    """Whether a secret is configured at all.

    Read per call, not at import: unsetting the variable is the rollback, and
    the tests flip the setting and expect the next request to notice.
    """
    return bool(settings.origin_secret)


def is_exempt(path: str, method: str) -> bool:
    """Paths and methods the gate never refuses."""
    if method == "OPTIONS":
        return True
    return path in EXEMPT_PATHS


def header_verdict(request: Request) -> str:
    """What the gate makes of this request. Five values, in two groups:

    * armed — `ok` · `missing` · `mismatch`
    * not armed — `off` (no header arrived) · `off-seen` (one did)

    `off-seen` is what makes the rollout measurable rather than brave: put the
    Transform Rule live while the gate is still off, then ask each path in turn
    — the `api.` host, the apex `/api/*` Worker, the site's nginx, the raw
    `run.app` — and only arm the gate once every path that must keep working
    answers `off-seen`. Collapsing that into a bare `off` would make the switch
    a leap.

    It earned its keep on the sibling repo's first run: the apex Worker
    answered `off` with the rule already live, because a Worker subrequest to a
    host in the same zone skips that zone's Transform Rules. Arming the gate
    then would have taken the whole admin route down.

    It reports the verdict, never the value, and tells a caller on `run.app`
    only what it already knows about its own request.
    """
    presented = request.headers.get(ORIGIN_SECRET_HEADER)
    if not gate_is_armed():
        return "off-seen" if presented else "off"
    if not presented:
        return "missing"
    return "ok" if _matches(presented, settings.origin_secret or "") else "mismatch"


class OriginSecretMiddleware:
    """Require the edge's shared header on every request that is not exempt.

    A raw ASGI middleware rather than a `BaseHTTPMiddleware`: a refused request
    must cost as little as possible, and this way it never allocates a request
    or response object beyond the refusal itself.

    Placed (`api/main.py`) INSIDE `CORSMiddleware`, so a 403 still carries the
    CORS headers a browser needs to read it as a 403 rather than as an opaque
    network error, and OUTSIDE the analytics middleware, so a refused request
    can never fire an outbound Plausible event. That second one is not
    hypothetical: `track_asset_fetch` fires per request for anything with a
    crawler user agent, and a caller on the direct URL could otherwise turn
    each of its own refusals into one.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not gate_is_armed() or is_exempt(scope["path"], scope["method"]):
            await self.app(scope, receive, send)
            return
        presented = Request(scope).headers.get(ORIGIN_SECRET_HEADER)
        # An absent header is not a mismatch to measure, it is simply the wrong
        # door — so it short-circuits before the compare.
        if presented and _matches(presented, settings.origin_secret or ""):
            await self.app(scope, receive, send)
            return
        response = JSONResponse(
            {"detail": "this API is reached through https://api.anyplot.ai"},
            status_code=403,
            headers={"Cache-Control": "private, no-store"},
        )
        await response(scope, receive, send)
