"""Process-wide services of the agents runtime: stores, the render backend, the judge, the usage book.

Everything here lives in memory for one instance's lifetime, which is consistent
because the service runs with `max-instances=1`; a restart answers `session_expired`.
The `/v1` routes, the tools, the plugins and the pipeline all reach the same objects
through `get_services()`. Tests replace them with `set_services(Services(...))`.

`VersionStore` keeps every code version a session produced: the working form, the
run form, the exported `plot.py`, the `data.csv` it ran on, the render id of its two
PNGs, the adapter plan and the `PlotResult`. The artifact and bundle routes read
from it.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .data.store import DatasetStore
from .models import JudgeClient, make_judge_client
from .plugins.ledger import UsageBook
from .render import make_backend
from .render.contract import RenderBackend
from .render.store import RenderStore
from .schemas import AdaptPlan, PlotResult
from .settings import get_settings


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

    def delete_session(self, session_id: str) -> None:
        self._versions.pop(session_id, None)


@dataclass
class Services:
    """The shared runtime objects; built lazily where construction needs settings or credentials."""

    datasets: DatasetStore = field(default_factory=DatasetStore)
    renders: RenderStore = field(default_factory=RenderStore)
    versions: VersionStore = field(default_factory=VersionStore)
    usage: UsageBook = field(default_factory=UsageBook)
    backend_factory: Callable[[], RenderBackend] = field(default=lambda: make_backend(get_settings()))
    judge_factory: Callable[[], JudgeClient] = field(default=lambda: make_judge_client(get_settings()))
    _backend: RenderBackend | None = None
    _judge: JudgeClient | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def backend(self) -> RenderBackend:
        if self._backend is None:
            self._backend = self.backend_factory()
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
