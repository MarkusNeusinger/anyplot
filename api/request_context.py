"""Request-scoped helpers shared across routers."""

from fastapi import Request


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
