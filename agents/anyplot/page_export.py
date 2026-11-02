"""The `plot.html` download of a JavaScript version: its page built on demand in one theme and wrapped (JS-4b).

A JavaScript plot's code runs only in the harness's page (the library bundle, the theme's
tokens and the typed table around it), so its version offers that page as `plot.html`
(`schemas.PAGE_ARTIFACT`), next to the PNG and the code file (owner decision of
2026-10-30, question 12 of agentic/specs/261024-agent-all-libraries.md). Nothing of it is
stored: a page is the bundle plus the table, up to about 25 MB, so `page_download` builds it
from the version's run form, library and `data_json` whenever it is asked for, through the
render backend's `page` (the renderer's `POST /page`: the harness in page-only mode, which
starts no browser), and wraps it in the sandboxed frame of `render/page.py`.

It waits for a slot of the `toggle` lane (`render/serial.py`) as long as the theme toggle
does (`theme_render.slot_wait_s`), so a download never delays a pipeline render; the route
registers it in the run registry like the toggle. No model call, no ADK import.
"""

import asyncio
import logging
import secrets

from .code.profiles.javascript.normalise import CANVASES, measure_canvas
from .render.contract import PageFailed, PageJob
from .render.page import MAX_WRAPPED_PAGE_BYTES, wrap_page
from .render.runtimes import runtime_for
from .schemas import PAGE_ARTIFACT, Theme
from .services import CodeVersion, Services
from .settings import AgentSettings
from .theme_render import slot_wait_s


logger = logging.getLogger(__name__)


class NoPage(LookupError):
    """The version has no page: it is not a JavaScript plot, or it carries no typed table."""


class PageTooLarge(PageFailed):
    """The wrapped page is over `MAX_WRAPPED_PAGE_BYTES`, which a response that is not streamed cannot carry."""


def page_title(version: CodeVersion, spec_id: str) -> str:
    """The downloaded document's title: the spec, the library and the version, as the PNG's name gives them."""
    return f"{spec_id} · {version.library} · v{version.number} · anyplot.ai"


async def page_download(
    services: Services, settings: AgentSettings, version: CodeVersion, theme: Theme, *, spec_id: str
) -> bytes:
    """The wrapped `plot.html` of `version` in `theme`, as UTF-8.

    Raises `NoPage` for a version without a page, `RenderBusy` when no slot came free in
    time, `PageUnsupported` or `RendererUnavailable` when the backend cannot build pages,
    and `PageFailed` (`PageTooLarge` among them) when the build left none.
    """
    if PAGE_ARTIFACT not in version.artifacts() or version.data_json is None:
        raise NoPage("the version has no page")
    runtime = runtime_for(version.library, cpu_seconds=settings.render_timeout_s)
    job = PageJob(
        job_id=secrets.token_hex(8),
        library=version.library,
        source=version.run_form,
        data_json=version.data_json,
        theme=theme,
        timeout_s=settings.render_timeout_s,
    )
    try:
        page = await services.backend.page(job, wait_s=slot_wait_s(settings))
    except PageFailed as exc:
        # The error summary names the kind, the class and the line, never the message, which can quote the data.
        summary = runtime.error_summary(exc.stderr_tail, run_form=version.run_form)
        logger.warning("page build failed: exit %s, reason %s: %s", exc.exit_code, exc.reason, summary)
        raise
    canvas = measure_canvas(version.run_form, library=version.library).target or CANVASES["landscape"]
    title = page_title(version, spec_id)
    content = await asyncio.to_thread(lambda: wrap_page(page, theme=theme, canvas=canvas, title=title).encode())
    if len(content) > MAX_WRAPPED_PAGE_BYTES:
        logger.warning("page too large: %d bytes wrapped, the cap is %d", len(content), MAX_WRAPPED_PAGE_BYTES)
        raise PageTooLarge(exit_code=0, reason="output_rejected")
    return content
