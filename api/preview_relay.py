"""The relay page of the agent chat's interactive preview (JS-4b-2, route A of step 3g in
agentic/specs/261024-agent-all-libraries.md, owner decision of 2026-10-31).

A JavaScript plot's preview shows the same `plot.html` the download serves (the agents
service's wrapper: no script of its own, the browser harness's policy plus `frame-src
'none'`, the plot in a sandboxed `srcdoc` frame) inside the chat. The chat fetches that page
through its authenticated artifact route and hands it to this relay, a static page on the API's
origin that holds no data, takes no token and reads no cookie:

    the chat (anyplot.ai)
      <iframe sandbox="allow-scripts" src="https://api.anyplot.ai/preview/relay">
        the relay: an opaque origin (`sandbox allow-scripts` in its policy), its own script only
          <iframe sandbox="allow-scripts" srcdoc=<the wrapper, set as a property>>
            the wrapper: no script
              <iframe sandbox="allow-scripts" srcdoc=<the harness's page>>
                the plot code

* **Who may frame it.** `frame-ancestors` names the site's origins (`settings.cors_origins`) and
  any local dev server (`http://localhost:*`, the BFF's `LOCAL_ORIGIN_REGEX`), so no other site
  can embed it and post a page into it.
* **What it accepts.** One message, the first that comes from `window.parent` (never the plot's
  frame, a sibling or a popup) at one of those origins, holding a string of at most
  `MAX_PAGE_CHARS` characters. It writes that string into a new `<iframe sandbox="allow-scripts">`
  through the `srcdoc` property, never as built HTML, and ignores every later message. It sends
  nothing back.
* **What it may do.** Its policy is the harness's (`PAGE_POLICY`: no request, no `eval`, no form,
  no `<base>`), so neither the relay nor any frame inside it, which inherit it, reaches the
  network; `sandbox allow-scripts` gives it an opaque origin, so it has no cookies or storage of
  the API's origin either.

The chat posts with the target origin `*`, because an opaque origin cannot be named, and only
once, on the first `load` of the relay frame it has just mounted (a later load is ignored).
The probe (`agents/renderer/page_probe.mjs relay`, the renderer image's CI step) checks all of
it in Chromium.

Standard library only: the renderer image's CI step loads this module by its path to serve the
probe's relay with the real headers; `api/routers/preview.py` serves it with the site's origins.
"""

import json
import re
from collections.abc import Iterable


RELAY_PATH = "/preview/relay"
PAGE_POLICY = (
    "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; "
    "form-action 'none'; base-uri 'none'"
)
"""The browser harness's sandbox policy (`CONTENT_SECURITY_POLICY` in `automation/js-render/render.mjs`, the agents'
`render/page.py` `PAGE_POLICY`; pinned equal by a test): the relay's, which every frame inside it inherits."""
LOCAL_ORIGINS = "http://localhost:*"
"""Any local dev server, the source expression of the BFF's `LOCAL_ORIGIN_REGEX` (`http://localhost:\\d+`)."""
LOCAL_ORIGIN_PATTERN = r"^http://localhost:\d+$"
"""The same origins as a regular expression, for the relay's own check."""
_LOCAL_REGEX_LITERAL = LOCAL_ORIGIN_PATTERN.replace("/", "\\/")
"""`LOCAL_ORIGIN_PATTERN` with its slashes escaped, the body of a JavaScript regular expression literal."""
MAX_PAGE_CHARS = 32 * 1024 * 1024
"""The longest page the relay takes: the agents service answers a wrapper of at most 30 MiB
(`render/page.py` `MAX_WRAPPED_PAGE_BYTES`), and a string has at most as many characters as its UTF-8 bytes."""
_ORIGIN = re.compile(r"^https?://[A-Za-z0-9.-]+(:[0-9]{1,5})?$")
"""An origin the relay names: a scheme, a host and an optional port, nothing that could end a directive."""


def relay_origins(origins: Iterable[str]) -> list[str]:
    """The configured origins that are plain origins, sorted and without duplicates; anything else is left out."""
    return sorted({origin for origin in origins if _ORIGIN.fullmatch(origin)})


def relay_policy(origins: Iterable[str]) -> str:
    """The relay's `Content-Security-Policy`: an opaque origin with scripts, the harness's policy, and who may frame it."""
    ancestors = " ".join([*relay_origins(origins), LOCAL_ORIGINS])
    return f"sandbox allow-scripts; {PAGE_POLICY}; frame-ancestors {ancestors}"


def relay_headers(origins: Iterable[str]) -> dict[str, str]:
    """The relay's response headers; the page is the same for every caller, so the edge may keep it for a while."""
    return {
        "Content-Security-Policy": relay_policy(origins),
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "public, max-age=300",
    }


def relay_html(origins: Iterable[str]) -> str:
    """The relay page: no markup of its own, a script that takes one page from its parent (module docstring)."""
    allowed = json.dumps(relay_origins(origins)).replace("<", "\\u003c")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>anyplot preview</title>
<style>
  html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
  iframe {{ display: block; border: 0; width: 100%; height: 100%; }}
</style>
</head>
<body>
<script>
(function () {{
  "use strict";
  var ORIGINS = {allowed};
  var LOCAL = /{_LOCAL_REGEX_LITERAL}/;
  var MAX_PAGE_CHARS = {MAX_PAGE_CHARS};
  var shown = false;
  window.addEventListener("message", function (event) {{
    if (shown || event.source !== window.parent) return;
    if (ORIGINS.indexOf(event.origin) === -1 && !LOCAL.test(event.origin)) return;
    var page = event.data;
    if (typeof page !== "string" || page.length === 0 || page.length > MAX_PAGE_CHARS) return;
    shown = true;
    var frame = document.createElement("iframe");
    frame.setAttribute("sandbox", "allow-scripts");
    frame.setAttribute("title", "Interactive plot");
    frame.srcdoc = page;
    document.body.appendChild(frame);
  }});
}})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    # `python3 api/preview_relay.py [origin ...]`: the relay's page and headers as JSON, which the probe serves
    # (`agents/renderer/page_probe.mjs relay`).
    import sys

    print(json.dumps({"html": relay_html(sys.argv[1:]), "headers": relay_headers(sys.argv[1:])}))
