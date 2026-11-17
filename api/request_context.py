"""Request-scoped helpers shared across routers."""

import hashlib
import hmac
import secrets

from fastapi import Request


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
