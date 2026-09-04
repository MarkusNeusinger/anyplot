"""The delivery-side security policy, held against the files it describes.

`app/security-headers.conf` is a string in an nginx include. Nothing compiles
it, nothing imports it, and four things around it can drift silently — each of
which has cost someone a day somewhere:

1. **The CSP nonce, which lives in two files at once.** `script-src` names
   `'nonce-$request_id'` here; `app/nginx.conf` stamps that same `$request_id`
   onto every `<script` tag with `sub_filter`. Nothing but agreement makes them
   one mechanism, and disagreement is invisible: the page still arrives, the
   header still reads as a modern policy, and every inline script on it is
   blocked — a nonce in the policy makes `'unsafe-inline'` inert, so there is
   no fallback left to catch the fall. The delivery half also depends on the
   shell NOT being precompressed (`gzip_static` would hand out the untouched
   `.gz`) and on it never being stored for replay.

2. **nginx's `add_header` inheritance.** A location with any `add_header` of
   its own drops every inherited one. `app/nginx.conf` therefore re-includes
   the snippet in each such location, and forgetting that in a new location is
   invisible in review and invisible in the browser until someone checks that
   one URL.

3. **The API host's own headers.** api.anyplot.ai is a separate origin with no
   nginx in front of it, so nothing there inherits anything from the website —
   and it has two exits, only one of which is a middleware.

4. **The keywords a hardening pass reaches for by reflex.** `'unsafe-inline'`
   beside a nonce, `'strict-dynamic'` over a shell that links its chunks with
   `<link rel="modulepreload">`, a `report-to` group nobody defined: each looks
   stricter and is quietly worse.

What this file cannot see is whether Cloudflare copies the nonce onto the
script IT injects at the edge — that is a live measurement, recorded in
`app/security-headers.conf` next to the directive it justifies.

The nginx parse is deliberately crude — a brace counter over one file we write
ourselves, not a config parser. It only has to be right about this file.
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app, fastapi_app


ROOT = Path(__file__).resolve().parents[3]
HEADERS_CONF = ROOT / "app" / "security-headers.conf"
NGINX_CONF = ROOT / "app" / "nginx.conf"
VITE_CONFIG = ROOT / "app" / "vite.config.ts"

INCLUDE_LINE = "include /etc/nginx/security-headers.conf;"


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


def server_blocks() -> list[str]:
    """Every `server { … }` block of app/nginx.conf, as raw text."""
    conf = NGINX_CONF.read_text(encoding="utf-8")
    blocks = []
    for match in re.finditer(r"^server\s*\{", conf, re.MULTILINE):
        depth = 0
        for i in range(match.end() - 1, len(conf)):
            if conf[i] == "{":
                depth += 1
            elif conf[i] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(conf[match.start() : i + 1])
                    break
    return blocks


# The nonce as the stamp spells it (`nonce="$request_id"`). Its counterpart in
# the header is read out of the parsed DIRECTIVE, never out of the raw file:
# security-headers.conf explains itself at length and quotes `'nonce-…'` in its
# own prose, so a regex over the whole file happily reports a nonce that the
# policy no longer carries — which is how this very test first passed while the
# header had none at all.
_HEADER_NONCE = re.compile(r"^'nonce-(\$[A-Za-z_][A-Za-z0-9_]*)'$")
_STAMP = re.compile(r"""sub_filter\s+'<script'\s+'<script nonce="(\$[A-Za-z_][A-Za-z0-9_]*)"'\s*;""")


def header_nonce_variable() -> str | None:
    """The nginx variable `script-src` reads its nonce from, if any."""
    for token in csp_directives().get("script-src", []):
        match = _HEADER_NONCE.match(token)
        if match:
            return match.group(1)
    return None


def test_the_policy_takes_its_nonce_from_a_per_request_variable():
    """A nonce is only a nonce if it is fresh per response.

    A literal would be a shared secret baked into an image and reused for the
    lifetime of a revision — which is to say, not a secret. `$request_id` is
    nginx's own 16 random bytes as 32 hex digits: hex is inside the CSP nonce
    grammar's charset, and 128 bits is at the ceiling of what the spec asks
    for.
    """
    script_src = csp_directives()["script-src"]
    nonces = [t for t in script_src if t.startswith("'nonce-")]
    assert nonces == ["'nonce-$request_id'"], (
        f"script-src carries {nonces or 'no nonce'}; expected exactly one, "
        "'nonce-$request_id'. A literal nonce is a constant, and a constant "
        "nonce is 'unsafe-inline' with extra steps."
    )
    assert "'unsafe-inline'" not in script_src, (
        "script-src still allows 'unsafe-inline'. With a nonce present a browser "
        "ignores it anyway, so this only misleads the next reader."
    )


def test_the_header_and_the_stamp_name_the_same_variable():
    """The one failure with no symptom until every inline script is dead.

    The header promises a nonce; `sub_filter` writes one onto the tags. Nothing
    connects them but this equality, and if it breaks the page still arrives,
    still renders its shell, still reports a strict-looking policy — while the
    browser refuses every script in it.
    """
    stamps = _STAMP.findall(NGINX_CONF.read_text(encoding="utf-8"))
    assert stamps, (
        "app/nginx.conf stamps no CSP nonce onto <script> tags. The policy's nonce "
        "makes 'unsafe-inline' inert, so without the stamp NOTHING inline runs."
    )
    assert set(stamps) == {header_nonce_variable()}, (
        f"the stamp writes {sorted(set(stamps))} but script-src reads "
        f"{header_nonce_variable()!r} — the tags would carry a nonce the policy "
        "does not allow."
    )


def test_every_server_block_stamps_the_nonce():
    """Both vhosts, at server level, because four locations serve the shell.

    The exact `= /index.html`, the SPA fallback, and — in the python block —
    two regex routes whose `try_files /index.html =404` serves the file in
    place, with no internal redirect to re-run location matching. A stamp
    placed per-location is a stamp missing from whichever one is forgotten,
    and it fails on those routes alone.
    """
    missing = [
        block.splitlines()[0]
        for block in server_blocks()
        if INCLUDE_LINE in block and not _STAMP.search(_without_comments(block))
    ]
    assert not missing, (
        f"these server blocks send the CSP but never stamp its nonce: {missing}. "
        "Every <script> tag they serve would be blocked."
    )
    assert all("sub_filter_once off;" in block for block in server_blocks() if _STAMP.search(block)), (
        "sub_filter replaces only the FIRST match without `sub_filter_once off` — "
        "the shell has seven script tags and six of them would go unstamped."
    )


def test_the_shell_is_never_precompressed():
    """`gzip_static` hands out the `.gz` untouched, and sub_filter never sees it.

    The prettiest way to break this whole mechanism: leave a build artefact in
    place. nginx would serve `index.html.gz` byte for byte, the stamp would
    never run, the header would still carry its nonce, and every inline script
    on the page would be refused — with nothing in any log to say why.
    """
    config = VITE_CONFIG.read_text(encoding="utf-8")
    calls = re.findall(r"compression\(\{[^}]*\}\)", config)
    assert calls, "app/vite.config.ts declares no compression plugin — did it move?"
    unguarded = [c for c in calls if "index" not in c.split("exclude")[-1]]
    assert not unguarded, (
        "a compression plugin in app/vite.config.ts does not exclude index.html: "
        f"{unguarded}. The shell is rewritten per request for the CSP nonce and "
        "must not exist as a precompressed file."
    )


def test_the_shell_is_never_stored():
    """A nonced response that can be replayed is a nonced response that fails.

    A stored shell pairs yesterday's `nonce="…"` in the body with today's
    header — and a 304 revalidation is worse, because HTTP says the 304's
    headers REPLACE the stored ones, so the browser ends up holding exactly
    that mismatch. Two things prevent it and only one of them is visible here:
    `sub_filter` drops `Last-Modified` and `ETag` on its own whenever it
    rewrites a body (so nothing can be revalidated), and these locations say
    `no-store` (so nothing is kept to revalidate).
    """
    shells = [b for b in locations_with_add_header() if b.lstrip().startswith("location = /index.html")]
    assert shells, "app/nginx.conf no longer has a `location = /index.html` — where does the shell get its headers?"
    missing = [b.splitlines()[0].strip() for b in shells if "no-store" not in b]
    assert not missing, (
        f"these shell locations do not send `no-store`: {missing}. The shell carries a "
        "per-request CSP nonce and must not be reusable."
    )


def test_strict_dynamic_needs_the_stamp_to_reach_the_module_preloads():
    """It reads as the stricter policy and would load the app from nothing.

    `'strict-dynamic'` makes a browser ignore `'self'` for scripts and trust
    only what an already-trusted script pulls in. `yarn build` links every
    chunk from the shell with `<link rel="modulepreload">` — a link element,
    which trust propagation does not cover and which the `<script` stamp does
    not touch. So adopting the keyword means widening the stamp in the same
    breath; adopting it alone means the preloads are refused. Absent today, and
    the reasoning is in security-headers.conf — this only has to hold whoever
    adds it to the second half.
    """
    if "'strict-dynamic'" not in csp_directives()["script-src"]:
        return
    conf = _without_comments(NGINX_CONF.read_text(encoding="utf-8"))
    assert re.search(r"sub_filter\s+'<link", conf), (
        "script-src carries 'strict-dynamic', which drops 'self' for scripts, but "
        "app/nginx.conf still stamps only <script> tags. Vite's <link "
        'rel="modulepreload"> chunk hints would be blocked and the SPA would never '
        "boot."
    )


def test_script_src_never_mixes_unsafe_inline_with_a_nonce_or_hash():
    """The two together are the trap, not the belt-and-braces pair they look like.

    A browser ignores `'unsafe-inline'` as soon as a hash or nonce is present.
    So a policy carrying both is exactly as strict as the nonce alone, while
    reading as though it still has a safety net — and the day someone removes
    the stamp because "'unsafe-inline' is still in there", the whole page goes
    quiet.
    """
    script_src = csp_directives()["script-src"]
    keyed = [t for t in script_src if t.startswith(("'sha256-", "'sha384-", "'sha512-", "'nonce-"))]
    assert not (keyed and "'unsafe-inline'" in script_src), (
        f"script-src carries both {keyed} and 'unsafe-inline'. The browser ignores the "
        "latter, so this is the strict policy with a misleading label. Pick one."
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
