"""anyplot-renderer: runs adapted plot code in Cloud Run sandboxes, one at a time.

The agents service (`agents/main.py`) and a developer's `adk web` both reach this
service through the `remote` render backend (`agents/anyplot/render/backends/remote.py`),
so a local run and the deployed service render in the same sandboxes. Nothing in
`agents/renderer/` imports ADK or `agents.anyplot` (whose package import loads ADK),
so the renderer image installs neither; `wire.py` is the JSON contract both sides
read. The directory has no `__init__.py` on purpose: `adk web agents` lists every
subdirectory of `agents/` that has one as an agent, so this is a namespace package,
like `agents/evals/`.

| Route | Body | Result | Errors |
|---|---|---|---|
| `POST /render` | `RenderRequest` (`wire.py`): `{job_id, language, library, source, data_csv, themes, timeout_s}` | `RenderResponse`: per theme the exit code, a timeout flag, the stderr tail, the probe, the PNG as base64, the attempts and a reason; the slot wait and total time; `MemAvailable` | `401 unauthenticated`, `403 forbidden`, `422 invalid_job`, `503 busy` (no slot within `RENDERER_SLOT_WAIT_S`), `503 low_memory`, `503 stuck`, `503 sandbox_unavailable` |
| `GET /status` | | `RendererStatus`: name, version, revision, in flight, waiting, stuck launchers, `MemAvailable`, whether the launcher exists | `401`, `403` |

Both routes sit behind the caller check (`auth.py`) and Cloud Run IAM. There is no
`/healthz`: Google's front end intercepts that path (spike S), and Cloud Run's
default TCP startup probe is enough for a service with no dependencies.

**One render at a time.** The service holds one render slot, and the themes of a job
render one after the other inside it, so at most one sandbox exists on the instance:
spikes S and S2 showed that one 4 GiB instance serves one sandbox safely and that
many sandboxes crash the whole instance. A request waits at most
`RENDERER_SLOT_WAIT_S` for the slot (`503 busy`), and a render is refused while
`MemAvailable` is below `RENDERER_MIN_MEM_AVAILABLE_MB` (`503 low_memory`), which is
the memory signal S2 asked for because the cgroup's memory counter is unreadable.

The service only runs code and returns what the run left: the agents service's host
gates (R1-R3) and probe gates judge it (`agents/anyplot/render/gates.py`). Nothing of
a job (code, data, stderr, PNG) is logged; the log carries ids, exit codes, reasons
and timings. A request validation error answers `invalid_job` without echoing the
body, because the body is the user's code and data.

Run locally (without a launcher every render answers `503 sandbox_unavailable`):
`ENVIRONMENT=development uv run uvicorn agents.renderer.main:app --port 8003`.
"""

import asyncio
import contextlib
import importlib.metadata
import json
import logging
import time
from collections.abc import AsyncIterator
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .auth import CallerRefused, check_caller
from .executor import Executor, ExecutorConfig, SandboxExecutor, Unavailable, mem_available_mb
from .settings import RendererSettings, get_settings
from .wire import RendererStatus, RenderRequest, RenderResponse, RenderTimings, Theme, ThemeRun


logger = logging.getLogger("agents.renderer")
VERSION_FILE = Path(__file__).with_name("VERSION")
"""Written by the image build from `pyproject.toml`, because the image does not install the project."""
_NO_STORE = {"Cache-Control": "no-store"}


def _version() -> str:
    try:
        return importlib.metadata.version("anyplot")
    except importlib.metadata.PackageNotFoundError:
        pass
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip() or "dev"
    except OSError:
        return "dev"


class RenderSlot:
    """The renderer's one render slot: first come, first served, with a bounded wait."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.waiting = 0

    @property
    def in_flight(self) -> int:
        return 1 if self._lock.locked() else 0

    @contextlib.asynccontextmanager
    async def hold(self, wait_s: float) -> AsyncIterator[None]:
        """Hold the slot; raises `Unavailable("busy")` when it did not come free within `wait_s`."""
        self.waiting += 1
        try:
            async with asyncio.timeout(wait_s):
                await self._lock.acquire()
        except TimeoutError:
            raise Unavailable("busy") from None
        finally:
            self.waiting -= 1
        try:
            yield
        finally:
            self._lock.release()


class Renderer:
    """The settings, the executor and the slot of one service instance."""

    def __init__(self, settings: RendererSettings, executor: Executor) -> None:
        self.settings = settings
        self.executor = executor
        self.slot = RenderSlot()
        self.version = _version()

    async def render(self, job: RenderRequest) -> RenderResponse:
        started = time.monotonic()
        async with self.slot.hold(self.settings.slot_wait_s):
            waited = time.monotonic() - started
            floor = self.settings.min_mem_available_mb
            available = mem_available_mb()
            if floor and available is not None and available < floor:
                raise Unavailable("low_memory")
            outputs: dict[Theme, ThemeRun] = {}
            for theme in job.themes:
                outputs[theme] = await self.executor.run_theme(job, theme)
        response = RenderResponse(
            job_id=job.job_id,
            outputs=outputs,
            timings=RenderTimings(slot_wait_s=round(waited, 3), total_s=round(time.monotonic() - started, 3)),
            version=self.version,
            mem_available_mb=mem_available_mb(),
        )
        logger.info(
            json.dumps(
                {
                    "event": "render",
                    "job_id": job.job_id,
                    "library": job.library,
                    "themes": list(job.themes),
                    "exit_codes": {theme: run.exit_code for theme, run in response.outputs.items()},
                    "reasons": {theme: run.reason for theme, run in response.outputs.items()},
                    "attempts": {theme: run.attempts for theme, run in response.outputs.items()},
                    "slot_wait_s": response.timings.slot_wait_s,
                    "total_s": response.timings.total_s,
                    "mem_available_mb_before": available,
                    "mem_available_mb_after": response.mem_available_mb,
                }
            )
        )
        return response

    def status(self) -> RendererStatus:
        return RendererStatus(
            version=self.version,
            revision=self.settings.revision,
            in_flight=self.slot.in_flight,
            waiting=self.slot.waiting,
            stuck=self.executor.stuck,
            mem_available_mb=mem_available_mb(),
            sandbox=self.executor.available,
        )


@lru_cache(maxsize=1)
def get_renderer() -> Renderer:
    """The process-wide renderer; tests override this dependency."""
    settings = get_settings()
    return Renderer(settings, SandboxExecutor(ExecutorConfig.from_settings(settings)))


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Fail at startup, not at the first render, when the settings are invalid."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    get_renderer()
    yield


app = FastAPI(title="anyplot-renderer", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
RendererDep = Annotated[Renderer, Depends(get_renderer)]
caller_checked = [Depends(check_caller)]


@app.exception_handler(CallerRefused)
async def _caller_refused(_: Request, exc: CallerRefused) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"detail": exc.code}, headers=_NO_STORE)


@app.exception_handler(Unavailable)
async def _unavailable(_: Request, exc: Unavailable) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": exc.code}, headers=_NO_STORE)


@app.exception_handler(RequestValidationError)
async def _invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
    """A fixed answer: FastAPI's default would echo the body, which is the user's code and data."""
    return JSONResponse(status_code=422, content={"detail": "invalid_job"}, headers=_NO_STORE)


@app.post("/render", dependencies=caller_checked)
async def render(job: RenderRequest, renderer: RendererDep) -> JSONResponse:
    """Run every theme of `job` in its own sandbox, one after the other, inside the render slot."""
    response = await renderer.render(job)
    return JSONResponse(content=response.model_dump(mode="json"), headers=_NO_STORE)


@app.get("/status", dependencies=caller_checked)
async def status(renderer: RendererDep) -> JSONResponse:
    return JSONResponse(content=renderer.status().model_dump(mode="json"), headers=_NO_STORE)
