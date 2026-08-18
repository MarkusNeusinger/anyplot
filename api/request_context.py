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


def visitor_ip(request: Request) -> str:
    """Resolve the IP to report to analytics — deliberately not `client_ip`.

    The two answer opposite questions and must not be merged.

    `client_ip` keys rate limiting, so it takes the RIGHTMOST forwarded entry:
    the leftmost is client-controlled, and trusting it let a caller poison
    another user's bucket. Analytics needs the opposite — Plausible documents
    that it uses "the first valid IP address from the list" and that "if you
    forward a server, hosting provider, or CDN IP address instead of the actual
    visitor IP, Plausible's bot filtering will drop the event". Handing it the
    rightmost entry means handing it our own infrastructure's address, and the
    event is silently discarded.

    Spoofing is not a concern in this direction: a forged value skews a
    geolocation bucket, where forging the rate-limit key locked people out.

    Order: `cf-connecting-ip`, which Cloudflare overwrites on proxied traffic
    and is therefore both real and unforgeable; then the leftmost non-empty
    forwarded entry; then the socket peer.
    """
    cf_ip = request.headers.get("cf-connecting-ip", "").strip()
    if cf_ip:
        return cf_ip
    for entry in request.headers.get("x-forwarded-for", "").split(","):
        if entry.strip():
            return entry.strip()
    return request.client.host if request.client else ""
