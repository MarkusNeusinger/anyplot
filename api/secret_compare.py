"""One constant-time comparison for every shared secret that arrives in a header.

`secrets.compare_digest` accepts two `str` only while both are ASCII; give it a
character above U+007F and it raises `TypeError`. That matters here because a
header value reaches the application latin-1-decoded straight off the wire, so a
caller can put one byte >= 0x80 into `X-Origin-Secret`, `X-Admin-Token` or
`X-Cache-Token` and turn a cheap 401 or 403 into an unhandled 500 — a way to
make a rejection expensive, available to anyone, and logged as an error every
time (Copilot review).

Encoding both sides first removes the restriction and the whole class of
problem, including the mirror case of a secret that legitimately contains
non-ASCII characters. It lives in one module because the same header pattern
appears at three call sites, and a comparator that is correct in two of them is
the sort of thing nobody notices.

`presented` is deliberately allowed to be `None` or empty: an absent header is
not a value to compare, it is simply no credential, and it must not be reported
as a coincidental match against an unset secret.
"""

from __future__ import annotations

import secrets


def secret_matches(presented: str | None, expected: str | None) -> bool:
    """Whether the caller presented exactly `expected`, in constant time.

    False whenever either side is missing, so an unconfigured secret can never
    be satisfied by an absent header.
    """
    if not presented or not expected:
        return False
    return secrets.compare_digest(presented.encode("utf-8"), expected.encode("utf-8"))
