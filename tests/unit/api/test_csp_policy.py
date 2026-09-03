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
   nginx in front of it, so nothing there inherits anything from the website.

The nginx parse is deliberately crude — a brace counter over one file we write
ourselves, not a config parser. It only has to be right about this file.
"""

from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app


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
# `</script\s*>`, not `</script>`: HTML lets whitespace sit before the `>` of a
# closing tag, and a regex that misses `</script >` would silently swallow the
# rest of the document into one "script body" and hash that. CodeQL's
# py/bad-tag-filter says so, and it is right — this parses a file people edit.
_SCRIPT = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>", re.DOTALL | re.IGNORECASE)
_TYPE = re.compile(r"""type\s*=\s*["']?([^"'\s>]+)""", re.IGNORECASE)
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
        if "src=" in attrs:
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


def test_reporting_directives_are_not_both_present():
    """`report-to` beside `report-uri` silences Chromium entirely.

    Measured in the sibling repo kurrentschrift: with both directives in one
    policy, Chromium sends NO report at all rather than preferring the newer
    one. Neither is set here today; this test exists so that whoever adds
    reporting adds exactly one of them.
    """
    directives = csp_directives()
    assert not ("report-to" in directives and "report-uri" in directives), (
        "CSP carries both report-to and report-uri — Chromium then reports nothing. Keep one."
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
