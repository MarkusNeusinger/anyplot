"""Request-scoped helpers shared across routers."""

import hashlib
import hmac
import ipaddress
import secrets

from fastapi import HTTPException, Request


IP_HASH_PREFIX = "hmac:"
"""Marks a salted key (`hash_ip`). The feedback table keeps it in `ip_hash` for its windows; the unsalted
SHA-256 hashes that rows written before it carried were cleared once by hand on 2026-11-02 after a snapshot,
so no migration is needed."""
_IP_SALT = secrets.token_bytes(32)
"""This process's salt for `hash_ip`. Never logged and never configured, so it dies with the process, and
with it every way to tell which address a key came from."""


def client_ip(request: Request) -> str:
    """Resolve the client IP for rate-limit / dup-suppression keying.

    Trust order (client → Cloudflare → Cloud Run):
    1. `cf-connecting-ip` — Cloudflare overwrites any client-supplied value on
       proxied traffic, so browsers on anyplot.ai cannot spoof it.
    2. Rightmost non-empty `x-forwarded-for` entry — appended by the trusted
       infrastructure hop. The *leftmost* entry (used here previously) is
       client-controlled: spoofing it evaded the rate limit and allowed
       poisoning another user's bucket to lock them out. Empty entries from
       malformed headers ("1.2.3.4, ") are skipped so a caller can't force
       everyone into one shared empty-string bucket.
    3. `request.client.host` as the last resort.

    A caller bypassing Cloudflare via the run.app URL can still forge
    `cf-connecting-ip`, but that only scatters its *own* submissions across
    buckets — no better than rotating source IPs, and it can no longer
    impersonate a victim's bucket.
    """
    cf_ip = request.headers.get("cf-connecting-ip", "").strip()
    if cf_ip:
        return cf_ip
    forwarded = request.headers.get("x-forwarded-for", "")
    for entry in reversed(forwarded.split(",")):
        if entry.strip():
            return entry.strip()
    return request.client.host if request.client else ""


def network_of(ip: str) -> str:
    """The network an address stands for, as a limit counts it: an IPv4 address itself, an IPv6 address its /64.

    One IPv6 subscriber holds a whole /64 and can take a new address for every request without
    forging anything, so a limit keyed on the full address would bind nobody. An IPv4 address
    written as IPv6 (`::ffff:203.0.113.7`) is the IPv4 address. A value that is no address is the
    empty string, so all of them share one key.
    """
    try:
        address = ipaddress.ip_address(ip.strip())
    except ValueError:
        return ""
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped is not None:
            return str(address.ipv4_mapped)
        return str(ipaddress.IPv6Network((address, 64), strict=False))
    return str(address)


TOO_LARGE = "Request body too large"
"""The fixed message of a body refused for its size: it says nothing about what the body held."""


async def read_body_within(request: Request, limit: int) -> bytes:
    """The request body, read by hand up to *limit* bytes; a fixed `413` for a body above it.

    A route that declares a body model has its whole body read and parsed by the framework before
    any of its own code runs, so a cap there comes too late. This one comes first: a declared
    `Content-Length` above the limit is refused before anything is read, and a body without one
    (chunked) is read only until it passes the limit. At most the limit and the one chunk the
    server handed over are ever held.
    """
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            size = int(declared)
        except ValueError:
            raise HTTPException(status_code=400, detail="Bad request") from None
        if size > limit:
            raise HTTPException(status_code=413, detail=TOO_LARGE)
    body = bytearray()
    async for chunk in request.stream():
        body += chunk
        if len(body) > limit:
            raise HTTPException(status_code=413, detail=TOO_LARGE)
    return bytes(body)


def hash_ip(ip: str) -> str:
    """The client address as this process's rate-limit key: `hmac:` and 32 hex digits.

    An HMAC-SHA256 under a random per-process salt, not a plain hash: there are only about
    four billion IPv4 addresses, so a plain SHA-256 of one is undone by trying them all. The
    limits that use it need the key only within one process: the feedback route keeps it in
    its row until the longest of its windows has passed (`FeedbackRepository.clear_ip_hashes`),
    and the search-miss limit holds it in memory only until a later minute's first request clears
    it (`api/search_misses.py`). With more than one instance, each counts its own requests: a
    limit then binds per instance."""
    if not ip:
        return ""
    return IP_HASH_PREFIX + hmac.new(_IP_SALT, ip.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
