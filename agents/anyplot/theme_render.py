"""The theme toggle: render another theme of a finished version, with no model call.

A pipeline run renders one theme (`PipelineArgs.theme`). `render_theme` renders a
stored version's run form in another theme on demand: the same code and the same
`data.csv`, through the render backend (so under its render semaphore) and the host
gates R1-R3 with the padding fallback, but never the adapter or the reviewer, so it
spends no tokens and does not wait in the run queue. The PNG joins the version's
render in the render store, so the artifact route serves it like the run's own.

| Status | Means | `reason` |
|---|---|---|
| `ok` | the theme passed the host gates on the exact canvas | none |
| `needs_attention` | the canvas missed, so the PNG was padded onto it (never cropped) | `canvas_padded` |
| `failed` | the render failed R1 or R2, or the backend could not run; nothing was stored | `render` or `error` |

A theme the version already holds is answered from its record without a render, and
a failed render is not recorded, so asking again retries it. The advisory probe lines
are not reported: the code is the run's own, whose lines that run already handled.
Every answer lists the version's artifacts after the call. No ADK import.
"""

import logging
import secrets
from dataclasses import dataclass
from typing import Any, Literal

from .render.contract import RenderJob, Theme
from .render.gates import data_rows, evaluate
from .render.runtimes.python import PythonRuntime
from .schemas import ArtifactName
from .services import PADDED_REASON, CodeVersion, Services, ThemeRender
from .settings import AgentSettings


logger = logging.getLogger(__name__)

ThemeStatus = Literal["ok", "needs_attention", "failed"]


class RenderGone(LookupError):
    """The version's render is no longer in the render store (swept or purged)."""


@dataclass(frozen=True)
class ThemeResult:
    """The answer of the theme toggle."""

    status: ThemeStatus
    reason: str | None
    artifacts: list[ArtifactName]

    def public(self) -> dict[str, Any]:
        body: dict[str, Any] = {"status": self.status, "artifacts": list(self.artifacts)}
        if self.reason is not None:
            body["reason"] = self.reason
        return body


async def render_theme(
    services: Services, settings: AgentSettings, session_id: str, version: CodeVersion, theme: Theme
) -> ThemeResult:
    """Render `theme` of `version` and store its PNG; raises `RenderGone` or `RenderStoreFull`."""
    render_id = version.render_id
    if render_id is None or services.renders.get(render_id, session_id) is None:
        raise RenderGone("the version's render is not in the store")
    known = version.themes.get(theme)
    if known is not None:
        return ThemeResult(known.status, known.reason, version.artifacts())
    runtime = PythonRuntime(cpu_seconds=settings.render_timeout_s)
    job = RenderJob(
        job_id=secrets.token_hex(8),
        language=runtime.language,
        library=version.library,
        source=version.run_form,
        data_csv=version.data_csv,
        themes=(theme,),
        timeout_s=settings.render_timeout_s,
    )
    try:
        result = await services.backend.render(job)
    except Exception as exc:  # no Docker, the sandbox stub: the class is logged, never the message
        logger.warning("theme render could not run: %s", type(exc).__name__)
        return ThemeResult("failed", "error", version.artifacts())
    report = evaluate(result, themes=job.themes, library=version.library, rows=data_rows(version.data_csv))
    if not report.passed_host_gates:
        return ThemeResult("failed", "render", version.artifacts())
    try:
        services.renders.add_theme(render_id, session_id, theme, report.shipped_pngs[theme])
    except KeyError:  # the session was purged or swept while the theme rendered
        raise RenderGone("the version's render left the store during the render") from None
    record = ThemeRender("ok") if report.canvas_ok else ThemeRender("needs_attention", PADDED_REASON)
    version.themes[theme] = record
    return ThemeResult(record.status, record.reason, version.artifacts())
