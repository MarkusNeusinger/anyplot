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

Exempt by path, and only this one:

* `/health` — the deploy's pre-traffic smoke probes the candidate revision on
  its `run.app` tag URL, which by definition never passes the edge. Gating it
  would make every deploy fail closed.

`/debug/cache/invalidate` used to be the second, and is not any more.
`sync-postgres.yml` flushes the cache from a GitHub runner at the end of each
sync and posts to the direct `*.run.app` URL *on purpose* — Cloudflare's bot
challenge answers an unauthenticated curl POST against `api.anyplot.ai` with a
403 HTML page — so it had no front door to come through. It has one now: the
workflow sends the header itself, out of the `ORIGIN_SECRET` repository secret.
That is strictly better than the exemption it replaces. An exempt path is one
anybody may POST to from anywhere, with only the endpoint's own
`CACHE_INVALIDATE_TOKEN` behind it; a workflow that carries the header needs no
hole in the gate at all.

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

**What this gate does not close, measured 2026-09-03.** It protects the API
service's own door. The APP service (`anyplot-app`) also stands with
`ingress=all`, and its nginx relays a crawler user agent through `@seo_proxy` to
`https://api.anyplot.ai` — where the edge stamps the header legitimately. So a
caller who sends a crawler user agent to the app's raw `*.run.app` URL still
reaches the prerendered render, and its DB queries and Plausible event, without
having passed the edge himself (Copilot review). Confirmed live: a Googlebot UA
against `…run.app/scatter-basic` answers 200 with the correct
`<link rel="canonical" href="https://anyplot.ai/scatter-basic">`. That is a
second door on a second service, not a hole in this one — the request this
process sees genuinely came through the edge.

Two things about closing it are now known, and neither was before:

* **A `Host` rule would be a real boundary, not theatre.** The obvious worry is
  that anyone could send `Host: anyplot.ai` to the `run.app` URL and walk
  straight through a host check. They cannot: Google's frontend routes by Host
  and answers a foreign one with its own 404 before the container is reached
  (measured — `curl -H "Host: anyplot.ai" https://anyplot-app-….run.app/…`
  returns Google's 404 page). On that origin `$host` is therefore always the
  `run.app` name, so `app/nginx.conf` could refuse `@seo_proxy` for it.
* **That alone would break `bot-serving-check.yml`**, which probes exactly this
  origin with crawler UAs and cannot spoof the Host either, because Cloudflare
  403s GitHub-runner IPs even for a UA-spoofed Googlebot. An exception keyed on
  a header or a UA the workflow sends is worthless — this repository is public,
  so the value is public with it. The exception has to be the shared secret,
  which means the app's nginx must LEARN the secret: template the config
  (`nginx-unprivileged` ships the `envsubst` entrypoint), attach `ORIGIN_SECRET`
  to `anyplot-app` in `app/cloudbuild.yaml`, add a Cloudflare Transform Rule for
  the `anyplot.ai` host (today's rule covers `api.anyplot.ai` only — without it
  the enforcing config locks out every human visitor), and hand the workflow the
  same secret.

Four coordinated changes, two of them in the dashboard and one of them able to
take the whole site down if it lands out of order. That is the reason this is
still described here rather than done.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from api.secret_compare import secret_matches
from core.config import settings


ORIGIN_SECRET_HEADER = "x-origin-secret"

# Exact paths only, no prefixes: a prefix exemption is how a gate quietly grows
# a hole. See the module docstring for what this one buys, why
# `/debug/cache/invalidate` no longer needs it, and why `/seo-proxy/…` never did.
EXEMPT_PATHS = frozenset({"/health"})


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
    return "ok" if secret_matches(presented, settings.origin_secret) else "mismatch"


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
        if secret_matches(presented, settings.origin_secret):
            await self.app(scope, receive, send)
            return
        response = JSONResponse(
            {"detail": "this API is reached through https://api.anyplot.ai"},
            status_code=403,
            headers={"Cache-Control": "private, no-store"},
        )
        await response(scope, receive, send)
