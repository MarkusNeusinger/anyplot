"""The delivery-side security policy, held against the files it describes.

`app/security-headers.conf` is a string in an nginx include. Nothing compiles
it, nothing imports it, and three things in it can drift silently — each of
which has cost someone a day somewhere:

1. **The inline-script hashes.** `script-src` cannot enforce them yet —
   Cloudflare JavaScript Detections injects a fourth inline script at the edge
   whose body changes per response (measured 2026-09-03, the reasoning is in
   `security-headers.conf`) — so the file records them in a comment instead,
   ready for the day a nonce or a zone setting makes the switch possible. A
   recorded hash that no longer matches its script is worse than none: it looks
   like readiness. This recomputes them on every run.

2. **nginx's `add_header` inheritance.** A location with any `add_header` of
   its own drops every inherited one. `app/nginx.conf` therefore re-includes
   the snippet in each such location, and forgetting that in a new location is
   invisible in review and invisible in the browser until someone checks that
   one URL.

3. **The API host's own headers.** api.anyplot.ai is a separate origin with no
   nginx in front of it, so nothing there inherits anything from the website —
   and it has two exits, only one of which is a middleware.

The nginx parse is deliberately crude — a brace counter over one file we write
ourselves, not a config parser. It only has to be right about this file.
"""

from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app, fastapi_app


ROOT = Path(__file__).resolve().parents[3]
INDEX_HTML = ROOT / "app" / "index.html"
HEADERS_CONF = ROOT / "app" / "security-headers.conf"
NGINX_CONF = ROOT / "app" / "nginx.conf"

INCLUDE_LINE = "include /etc/nginx/security-headers.conf;"

# Comments are stripped BEFORE the script scan. index.html documents its own
# Eruda loader with the words `Plain <script> (not type="module")`, and a
# regex that reads that as a tag hashes the comment prose instead of the
# script — silently, and with a hash that looks perfectly plausible.
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
# The closing tag is `</script` followed by whitespace, `/` or `>`, and then
# anything up to the first `>` — which is what a browser accepts and what
# CodeQL's py/bad-tag-filter insists on (`</script >`, `</script\t\n bar>`). A
# regex that missed one of those would swallow the rest of the document into a
# single "script body" and hash that, silently. The lookahead is what keeps
# `</scriptfoo>` from counting as a close.
_SCRIPT = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script(?=[\s/>])[^>]*>", re.DOTALL | re.IGNORECASE)
_TYPE = re.compile(r"""type\s*=\s*["']?([^"'\s>]+)""", re.IGNORECASE)
# An EXTERNAL script, which CSP judges by its URL and never by a hash. HTML
# attribute names are case-insensitive and whitespace around `=` is legal, so
# `<script SRC = "…">` is external too — a plain `"src=" in attrs` called it
# inline and would have demanded a hash for a script with no body (Copilot
# review). `\b` keeps it from matching a `data-src=` or an `xlink:src=`.
_SRC = re.compile(r"\bsrc\s*=", re.IGNORECASE)
# A <script> whose type is none of these is a DATA BLOCK (the three JSON-LD
# blocks in index.html): the browser never executes it, and CSP never asks for
# a hash.
_EXECUTABLE_TYPES = {"", "module", "text/javascript", "application/javascript"}


def inline_script_hashes(html: str) -> list[str]:
    """`sha256-…` for every executable inline script, in document order."""
    html = _COMMENT.sub("", html)
    out = []
    for match in _SCRIPT.finditer(html):
        attrs = match.group("attrs")
        if _SRC.search(attrs):
            continue
        declared = _TYPE.search(attrs)
        if (declared.group(1).lower() if declared else "") not in _EXECUTABLE_TYPES:
            continue
        digest = hashlib.sha256(match.group("body").encode("utf-8")).digest()
        out.append(f"sha256-{base64.b64encode(digest).decode('ascii')}")
    return out


def csp_directives() -> dict[str, list[str]]:
    """The Content-Security-Policy(-Report-Only) value, split by directive."""
    conf = HEADERS_CONF.read_text(encoding="utf-8")
    match = re.search(r'add_header\s+Content-Security-Policy(?:-Report-Only)?\s+"([^"]+)"', conf)
    assert match, "no Content-Security-Policy header found in app/security-headers.conf"
    directives = {}
    for part in match.group(1).split(";"):
        tokens = part.split()
        if tokens:
            directives[tokens[0]] = tokens[1:]
    return directives


_ADD_HEADER = re.compile(r"^\s*add_header\b", re.MULTILINE)


def _without_comments(text: str) -> str:
    """nginx comment lines dropped — a `#` line that MENTIONS `add_header` is
    prose, and prose must not count as a directive."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def locations_with_add_header() -> list[str]:
    """Every `location …{ … }` block of app/nginx.conf that sets a header itself.

    Returned as the raw block text, so the caller can check what is inside it.
    """
    conf = NGINX_CONF.read_text(encoding="utf-8")
    blocks = []
    for match in re.finditer(r"^\s*location\s[^{]*\{", conf, re.MULTILINE):
        depth = 0
        start = match.start()
        for i in range(match.end() - 1, len(conf)):
            if conf[i] == "{":
                depth += 1
            elif conf[i] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(conf[start : i + 1])
                    break
    return [b for b in blocks if _ADD_HEADER.search(_without_comments(b))]


def recorded_hashes() -> list[str]:
    """The `sha256-…` values app/security-headers.conf keeps in its comment."""
    conf = HEADERS_CONF.read_text(encoding="utf-8")
    comments = "\n".join(line for line in conf.splitlines() if line.lstrip().startswith("#"))
    return re.findall(r"'(sha256-[A-Za-z0-9+/=]+)'", comments)


def test_recorded_hashes_match_the_inline_scripts_of_index_html():
    """The hashes the conf holds in reserve still describe the scripts they name."""
    expected = inline_script_hashes(INDEX_HTML.read_text(encoding="utf-8"))
    assert expected, "app/index.html has no inline scripts — did the extraction break?"
    assert sorted(recorded_hashes()) == sorted(expected), (
        "the hashes recorded in app/security-headers.conf and app/index.html's inline "
        "scripts disagree.\n"
        f"  recorded: {sorted(recorded_hashes())}\n"
        f"  computed: {sorted(expected)}\n"
        "Recompute after ANY edit to an inline <script> — even whitespace."
    )


def test_script_src_never_mixes_unsafe_inline_with_hashes():
    """The two together are the trap, not the belt-and-braces pair they look like.

    A browser ignores `'unsafe-inline'` as soon as a hash or nonce is present.
    So a policy carrying both is exactly as strict as the hash list alone —
    which, while Cloudflare JavaScript Detections injects an unhashable inline
    script, means the edge's script is blocked while the policy reads as though
    nothing changed.
    """
    script_src = csp_directives()["script-src"]
    has_hash = any(t.startswith("'sha256-") for t in script_src)
    assert not (has_hash and "'unsafe-inline'" in script_src), (
        "script-src carries both a hash and 'unsafe-inline'. The browser ignores the "
        "latter, so this is the hash-only policy with a misleading label. Pick one."
    )


def test_object_src_and_base_uri_stay_closed():
    """The two directives `default-src` does not cover on its own."""
    directives = csp_directives()
    assert directives["object-src"] == ["'none'"]
    assert directives["base-uri"] == ["'self'"]


def reporting_endpoint_groups() -> set[str]:
    """The group names `Reporting-Endpoints` defines, if the header is set at all."""
    conf = HEADERS_CONF.read_text(encoding="utf-8")
    match = re.search(r'add_header\s+Reporting-Endpoints\s+"([^"]+)"', conf)
    if not match:
        return set()
    return {part.split("=", 1)[0].strip() for part in match.group(1).split(",") if "=" in part}


def test_a_named_report_to_group_is_actually_defined():
    """`report-to <group>` is inert unless `Reporting-Endpoints` defines <group>.

    The failure this guards is silence, which looks exactly like "no
    violations": a policy that names a group nobody declared sends nothing, and
    the sibling repo spent a measurement on that before recognising it. Note
    what is NOT asserted — `report-uri` beside `report-to` is a legitimate
    migration setup, since Chromium prefers `report-to` and keeps `report-uri`
    as the fallback for clients that lack it (Copilot review). Neither is set
    here today; this exists for whoever adds reporting.
    """
    named = csp_directives().get("report-to", [])
    missing = [group for group in named if group not in reporting_endpoint_groups()]
    assert not missing, (
        f"CSP names report-to group(s) {missing} that no Reporting-Endpoints header defines — "
        "reports would go nowhere, and nowhere reads as 'no violations'."
    )


def test_every_location_with_its_own_header_reincludes_the_snippet():
    """nginx drops inherited add_headers per location; each one must re-include."""
    # `.strip()` first: the block regex may start its match on the newline
    # before `location`, which would otherwise name the offender as "".
    missing = [b.strip().splitlines()[0].strip() for b in locations_with_add_header() if INCLUDE_LINE not in b]
    assert not missing, (
        "these app/nginx.conf locations set an add_header and so lose every inherited "
        f"security header: {missing}. Add `{INCLUDE_LINE}` to each."
    )


def test_the_api_host_stamps_its_own_baseline_headers():
    """api.anyplot.ai has no nginx in front of it and inherits nothing."""
    response = TestClient(app).get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    # NOT X-Frame-Options: the SPA embeds /proxy/html cross-origin in an iframe,
    # which SAMEORIGIN would break.
    assert "X-Frame-Options" not in response.headers


def test_an_unhandled_500_carries_them_too():
    """The exit the header middleware cannot reach.

    `ServerErrorMiddleware` wraps every user middleware, so a route that RAISES
    makes `await call_next(request)` raise with it and the response
    `generic_exception_handler` builds never passes back through the stack
    (Copilot review). The handler stamps the headers itself, through the same
    helper — this is what proves the two exits agree.
    """

    # `app` is the ASGI wrapper (HeadAsGetMiddleware); `fastapi_app` is the
    # instance that owns the router and the exception handlers.
    @fastapi_app.get("/_test/raises", include_in_schema=False)
    async def _boom() -> None:
        raise RuntimeError("boom")

    try:
        response = TestClient(app, raise_server_exceptions=False).get("/_test/raises")
        assert response.status_code == 500
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    finally:
        routes = fastapi_app.router.routes
        routes[:] = [r for r in routes if getattr(r, "path", None) != "/_test/raises"]
