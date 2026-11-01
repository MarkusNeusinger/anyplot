"""Process-wide services of the agents runtime: stores, the render backend, the judge, the usage book.

Everything here lives in memory for one instance's lifetime, which is consistent
because the service runs with `max-instances=1`; a restart answers `session_expired`.
The `/v1` routes, the tools, the plugins and the pipeline all reach the same objects
through `get_services()`. Tests replace them with `set_services(Services(...))`.

`VersionStore` keeps every code version a session produced: the working form, the
run form, the exported `plot.py`, the `data.csv` it ran on, the render id of its
PNGs (the run's theme, plus the other theme once the toggle rendered it), the gate
outcome per rendered theme, the adapter plan and the `PlotResult`. The artifact,
bundle and theme-toggle routes read from it.

`RefusalStore` keeps, only with `AGENT_KEEP_REFUSALS`, the messages the scope judge
refused, per session and bounded, for the feedback bundle.
"""

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from .data.store import DatasetStore
from .models import JudgeClient, make_judge_client
from .plugins.ledger import UsageBook
from .render import make_backend
from .render.contract import RenderBackend
from .render.serial import SerialRenderer
from .render.store import RenderStore
from .schemas import DEFAULT_CODE_ARTIFACT, AdaptPlan, ArtifactName, CodeArtifact, PlotResult, Theme, artifact_names
from .settings import get_settings


PADDED_REASON = "canvas_padded"
"""The reason of a rendered theme whose PNG missed the canvas and was padded (never cropped)."""


@dataclass(frozen=True)
class ThemeRender:
    """The host-gate outcome of one theme of a version.

    `ok`, or `needs_attention` when its PNG was padded; `failed` (reason `render`) is
    a theme toggle whose render failed the host gates `tries` times: the same code
    and data fail the same way, so the toggle retries it only while `tries` is below
    `MAX_THEME_TRIES`. A failed theme holds no PNG and is not an artifact.
    """

    status: Literal["ok", "needs_attention", "failed"]
    reason: str | None = None
    tries: int = 1

    @property
    def rendered(self) -> bool:
        return self.status != "failed"


@dataclass
class CodeVersion:
    """One adapted version of the plot in a session."""

    number: int
    working: str
    run_form: str
    export: str
    data_csv: str
    render_id: str | None
    result: PlotResult
    plan: AdaptPlan | None = None
    title: str = ""
    feedback: list[str] = field(default_factory=list)
    library: str = ""
    """The library the version was adapted for; a session can switch library."""
    theme: Theme = "light"
    """The theme the run rendered and the reviewer saw."""
    theme_asked: bool = False
    """The user asked for `theme` in the chat, for this version or for the one it changed, so a change of it keeps
    the theme; otherwise a change follows the site theme of its turn (`pipeline.run_theme`)."""
    language: str = "en"
    """The plot language the version's text was written in (`session_state.plot_language`)."""
    requests: list[str] = field(default_factory=list)
    """The change requests the version carries out, oldest first: its lineage's earlier ones and its own,
    within `MAX_USER_REQUESTS` and `MAX_USER_REQUESTS_CHARS`. A change of this version hands them to the
    adapter and the reviewer as the user's standing decisions (`pipeline.standing_requests`)."""
    themes: dict[Theme, ThemeRender] = field(default_factory=dict)
    """Every theme rendered for the version, with its gate outcome; a rendered one has its PNG in the render."""
    code_artifact: CodeArtifact = DEFAULT_CODE_ARTIFACT
    """The name the exported code downloads under: the runtime's (`plot.py` for Python, `plot.R`, `plot.js`, ...)."""
    data_json: str | None = None
    """The version's table as typed JSON for a JavaScript plot (`RenderJob.data_json`), so the theme toggle renders the
    other theme from the same job; None for every other language, whose code reads `data_csv`."""

    def artifacts(self) -> list[ArtifactName]:
        """The version's artifacts: the PNG of every rendered theme, the code under its language's name, `data.csv`."""
        rendered = [theme for theme, record in self.themes.items() if record.rendered] or [self.theme]
        return artifact_names(rendered, self.code_artifact)


MAX_KEPT_REFUSALS = 20
"""Refused messages kept per session when `AGENT_KEEP_REFUSALS` is on; the oldest goes first."""


@dataclass(frozen=True)
class KeptRefusal:
    """One message the scope judge refused: its text, the verdict and language, and when (UTC, ISO 8601)."""

    verdict: str
    lang: str
    text: str
    at: str


class RefusalStore:
    """The refused messages of each session, a ring of `MAX_KEPT_REFUSALS`; filled only with `AGENT_KEEP_REFUSALS`.

    The feedback bundle is the only reader. Nothing here is logged, and a session's
    ring goes with the session (`Services.purge_session`).
    """

    def __init__(self, per_session: int = MAX_KEPT_REFUSALS) -> None:
        self.per_session = per_session
        self._rings: dict[str, deque[KeptRefusal]] = {}

    def add(self, session_id: str, refusal: KeptRefusal) -> None:
        self._rings.setdefault(session_id, deque(maxlen=self.per_session)).append(refusal)

    def all(self, session_id: str) -> list[KeptRefusal]:
        return list(self._rings.get(session_id, ()))

    def delete_session(self, session_id: str) -> None:
        self._rings.pop(session_id, None)


class VersionStore:
    """Code versions per session, numbered from 1."""

    def __init__(self) -> None:
        self._versions: dict[str, list[CodeVersion]] = {}

    def add(self, session_id: str, version: CodeVersion) -> CodeVersion:
        self._versions.setdefault(session_id, []).append(version)
        return version

    def next_number(self, session_id: str) -> int:
        return len(self._versions.get(session_id, [])) + 1

    def all(self, session_id: str) -> list[CodeVersion]:
        return list(self._versions.get(session_id, []))

    def get(self, session_id: str, number: int | None = None, *, library: str | None = None) -> CodeVersion | None:
        """Version `number`, or the latest one when `number` is None or 0; `library` limits both to that library."""
        versions = [
            version for version in self._versions.get(session_id, []) if library is None or version.library == library
        ]
        if not versions:
            return None
        if not number:
            return versions[-1]
        return next((version for version in versions if version.number == number), None)

    def latest_rendered(self, session_id: str, *, library: str | None = None) -> CodeVersion | None:
        """The newest version that shipped a render (`ok` or `needs_attention`), of `library` when given."""
        for version in reversed(self._versions.get(session_id, [])):
            if version.render_id is not None and (library is None or version.library == library):
                return version
        return None

    def latest_language(self, session_id: str) -> str | None:
        """The language the session's latest rendered version is written in, of any library; None before the first
        (`session_state.plot_language`)."""
        latest = self.latest_rendered(session_id)
        return latest.language if latest is not None else None

    def delete_session(self, session_id: str) -> None:
        self._versions.pop(session_id, None)


@dataclass
class Services:
    """The shared runtime objects; built lazily where construction needs settings or credentials."""

    datasets: DatasetStore = field(default_factory=DatasetStore)
    renders: RenderStore = field(default_factory=RenderStore)
    versions: VersionStore = field(default_factory=VersionStore)
    usage: UsageBook = field(default_factory=UsageBook)
    refusals: RefusalStore = field(default_factory=RefusalStore)
    backend_factory: Callable[[], RenderBackend] = field(default=lambda: make_backend(get_settings()))
    judge_factory: Callable[[], JudgeClient] = field(default=lambda: make_judge_client(get_settings()))
    _backend: SerialRenderer | None = None
    _judge: JudgeClient | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def backend(self) -> SerialRenderer:
        """The factory's backend behind the instance's one render semaphore, so every render is serial."""
        if self._backend is None:
            self._backend = SerialRenderer(self.backend_factory(), concurrency=get_settings().render_concurrency)
        return self._backend

    @property
    def judge(self) -> JudgeClient:
        if self._judge is None:
            self._judge = self.judge_factory()
        return self._judge

    def purge_session(self, session_id: str) -> None:
        """Drop everything a session left in the stores."""
        self.datasets.delete_session(session_id)
        self.renders.delete_session(session_id)
        self.versions.delete_session(session_id)
        self.refusals.delete_session(session_id)


_SERVICES: Services | None = None


def get_services() -> Services:
    global _SERVICES
    if _SERVICES is None:
        _SERVICES = Services()
    return _SERVICES


def set_services(services: Services | None) -> None:
    """Replace the process-wide services (tests), or reset them with None."""
    global _SERVICES
    _SERVICES = services
