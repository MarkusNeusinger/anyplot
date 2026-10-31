"""The downloadable `plot.html` of a JavaScript plot: the harness's page inside a sandboxed frame (JS-4b).

The renderer builds the page a render screenshots (`POST /page`, the browser harness in
page-only mode): the library bundle, the theme's tokens, the typed table and the plot code
inlined, under the harness's content security policy (`CONTENT_SECURITY_POLICY` in
`automation/js-render/render.mjs`: nothing but the inlined page, no request, no `eval`, no
form, no `<base>`). A policy stops a request, but not the page's own top-level navigation, so
the download is not that page but `wrap_page`'s document around it (step 3g of
agentic/specs/261024-agent-all-libraries.md):

* **No script of its own**, and a policy that is the harness's plus `frame-src 'none'`
  (`WRAPPER_POLICY`). A `srcdoc` frame inherits its parent's policy, so a stricter parent
  (`default-src 'none'` without `script-src 'unsafe-inline'`) blanks the plot; `frame-src
  'none'` does not block the `srcdoc` itself, but it does block the frame's own navigation to
  an http(s) URL (both measured by Fable in Chromium, 2026-10-31).
* **The page in `<iframe sandbox="allow-scripts" srcdoc=...>`**: an opaque origin (`null`), so
  no cookies, storage or same-origin access; without `allow-same-origin`,
  `allow-top-navigation`, `allow-popups`, `allow-modals`, `allow-forms` and `allow-downloads`,
  setting `top.location`, `window.open`, dialogs, forms and downloads are refused. The probe
  (`agents/renderer/page_probe.mjs`, the renderer image's CI step) checks it.
* **The page in a single-quoted attribute**, with `&` and `'` written as character references
  (`frame_source`). Those two are the only characters a single-quoted attribute value treats
  specially, so the frame gets the page byte for byte; a double-quoted one would turn every `"`
  of the bundle and the typed table into six bytes.
* **Sized by CSS alone** (`sizing_css`): the frame keeps the page's canvas (1600x900 CSS pixels,
  1200x1200 for a square plot), scaled down in steps by media queries until it fits the window
  with a margin (`SCALES`, down to a quarter), and scrolls below that, so no part is cut off on
  a laptop screen and the plot stays interactive (a transform keeps pointer events mapped).

Pure and deterministic, no I/O: the artifact route builds the page on demand and wraps it here.
A unit test pins `PAGE_POLICY` and `BACKGROUNDS` to the harness's own constants, which own them.
The module imports only the standard library, so the renderer image's CI step loads it by its
path to wrap the probe's page (the package's `__init__` imports ADK).
"""

import html
from typing import Literal


Theme = Literal["light", "dark"]
"""`schemas.Theme`, written out: this module imports nothing of the package (module docstring)."""


PAGE_POLICY = (
    "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; "
    "form-action 'none'; base-uri 'none'"
)
"""The harness's sandbox policy, character for character (`CONTENT_SECURITY_POLICY` in `render.mjs`, pinned by a test):
the page's own, which its frame inherits from the wrapper."""
WRAPPER_POLICY = f"{PAGE_POLICY}; frame-src 'none'"
FRAME_SANDBOX = "allow-scripts"
"""The frame's only permission: its scripts run, in an opaque origin, with nothing else allowed."""
BACKGROUNDS: dict[Theme, str] = {"light": "#FAF8F1", "dark": "#1A1A17"}
"""The page's background per theme (`pageBg` of the harness's `themeTokens`, pinned by a test), so the margin around
the frame matches it."""
DEVICE_SCALE_FACTOR = 2
"""The harness's: the PNG's pixels per CSS pixel of the page."""
SCALES = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25)
"""The frame's scales, largest first; the first that fits the window with `MARGIN_PX` on every side applies."""
MARGIN_PX = 16
MAX_WRAPPED_PAGE_BYTES = 30 * 1024 * 1024
"""The largest wrapper the artifact route answers: Cloud Run caps a response that is not streamed at 32 MiB. The page
is at most `wire.MAX_PAGE_BYTES` (24 MiB), and only its `&` and `'` grow (by four bytes each), so only a table full of
them comes near this."""


def frame_source(page: str) -> str:
    """`page` as the value of a single-quoted attribute: `&` and `'` as references, everything else as it is."""
    return page.replace("&", "&amp;").replace("'", "&#39;")


def sizing_css(width: int, height: int) -> str:
    """The frame at `width` x `height` CSS pixels, scaled down in `SCALES` steps by media queries on the window."""
    rules = [
        f".frame {{ width: {width}px; height: {height}px; }}",
        f"iframe {{ width: {width}px; height: {height}px; transform-origin: 0 0; }}",
    ]
    for larger, scale in zip(SCALES, SCALES[1:], strict=False):
        too_narrow = round(width * larger) + 2 * MARGIN_PX - 1
        too_short = round(height * larger) + 2 * MARGIN_PX - 1
        rules.append(
            f"@media (max-width: {too_narrow}px), (max-height: {too_short}px) {{ "
            f".frame {{ width: {round(width * scale)}px; height: {round(height * scale)}px; }} "
            f"iframe {{ transform: scale({scale}); }} }}"
        )
    return "\n  ".join(rules)


def wrap_page(page: str, *, theme: Theme, canvas: tuple[int, int], title: str) -> str:
    """The downloadable `plot.html`: `page` (the harness's page of `theme`) in a sandboxed `srcdoc` frame.

    `canvas` is the render's size in pixels (3200x1800 or 2400x2400), which the frame shows at
    half in CSS pixels, as the harness lays the page out; `title` is the document's title.
    """
    width, height = (side // DEVICE_SCALE_FACTOR for side in canvas)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta http-equiv="Content-Security-Policy" content="{WRAPPER_POLICY}" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html.escape(title)}</title>
<style>
  html, body {{ margin: 0; padding: 0; background: {BACKGROUNDS[theme]}; }}
  .frame {{ margin: {MARGIN_PX}px auto; overflow: hidden; }}
  iframe {{ display: block; border: 0; }}
  {sizing_css(width, height)}
</style>
</head>
<body>
<div class="frame"><iframe sandbox="{FRAME_SANDBOX}" title="{html.escape(title)}" srcdoc='{frame_source(page)}'></iframe></div>
</body>
</html>
"""
