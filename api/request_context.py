"""Request-scoped helpers shared across routers."""

import ipaddress

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

    Spoofing matters less in this direction: a forged value skews a
    geolocation bucket, where forging the rate-limit key locked people out.

    One consumer: `api/analytics.py::track_og_image`, for the link previews
    that fetch an og image from `api.anyplot.ai` directly, never through the
    site's nginx. Order:

    1. `cf-connecting-ip`, because Cloudflare overwrites it on everything it
       proxies, so through the edge it cannot be forged.
    2. The leftmost PUBLIC `x-forwarded-for` entry. A scanner forging a private
       or reserved address at the front of the list (`10.0.0.9, …`) is skipped
       rather than handed to Plausible as the visitor.
    3. The socket peer, if it is public. Behind Cloud Run it is the front end's
       private or loopback address, which Plausible would drop the event for.

    The empty string when none of the three is a public address: the event then
    goes without an `X-Forwarded-For` rather than with an address that is not
    the visitor's, and Plausible sees only the API's own address.
    """
    cf_ip = request.headers.get("cf-connecting-ip", "").strip()
    if _is_public_ip(cf_ip):
        return cf_ip
    for entry in request.headers.get("x-forwarded-for", "").split(","):
        candidate = entry.strip()
        if _is_public_ip(candidate):
            return candidate
    peer = request.client.host if request.client else ""
    return peer if _is_public_ip(peer) else ""


def _is_public_ip(value: str) -> bool:
    """Whether the token is a public unicast address.

    Proxies insert non-addresses (`unknown` is the classic), and Plausible
    documents that it uses "the first **valid** IP address from the list", so a
    malformed entry is skipped rather than passed on. Private, loopback,
    link-local, carrier-grade NAT, unique-local, documentation (TEST-NET) and
    unspecified addresses are all `is_global=False`; a multicast address can be
    `is_global=True` (224.0.0.1 is), hence the second clause.
    """
    if not value:
        return False
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return address.is_global and not address.is_multicast
