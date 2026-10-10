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
| `POST /render` | `RenderRequest` (`wire.py`): `{job_id, language, library, source, data_csv, themes, timeout_s}` | `RenderResponse`: per theme the exit code, a timeout flag, the stderr tail, the probe, the PNG as base64, the attempts, a reason with the measured value and the limit; the slot wait and total time; `MemAvailable` | `401 unauthenticated`, `403 forbidden`, `422 invalid_job`, `499 cancelled` or `499 client_gone` (nobody reads it), `500 internal`, `503 busy` (no slot within `RENDERER_SLOT_WAIT_S`), `503 low_memory`, `503 stuck`, `503 sandbox_unavailable`, `503 volume_missing`, `503 io` |
| `POST /render/{job_id}/cancel` | | `{"cancelled": n}`: the renders of that job it stopped | `401`, `403`, `422 invalid_job` |
| `GET /status` | | `RendererStatus`: name, version, revision, in flight, waiting, stuck launchers, `MemAvailable`, whether the launcher exists, whether the run volume is in place | `401`, `403` |

All routes sit behind the caller check (`auth.py`) and Cloud Run IAM. There is no
`/healthz`: Google's front end intercepts that path (spike S), and Cloud Run's
default TCP startup probe is enough for a service with no dependencies.

**One render at a time.** The service holds one render slot, and the themes of a job
render one after the other inside it, so at most one sandbox exists on the instance:
spikes S and S2 showed that one 4 GiB instance serves one sandbox safely and that
many sandboxes crash the whole instance. A request waits at most
`RENDERER_SLOT_WAIT_S` for the slot (`503 busy`), and a render is refused while
`MemAvailable` is below `RENDERER_MIN_MEM_AVAILABLE_MB` (`503 low_memory`), which is
the memory signal S2 asked for because the cgroup's memory counter is unreadable.

**A render stops when its caller does.** uvicorn does not cancel a handler whose
client went away, so the route runs the render as a task and races it against the
connection's `http.disconnect`; a caller that is gone, or a
`POST /render/{job_id}/cancel` from the `remote` backend when its own render was
cancelled or timed out (for a front end that does not pass the disconnect on), cancels
the task, and the executor's kill path stops the sandbox and frees the slot.

**Fail closed on the instance.** On Cloud Run the run directories must sit on the
size-limited volume (`runs_volume_ok`), or every render answers `503 volume_missing`.
A launcher that outlived its kill makes every later render `503 stuck`, so the
service then ends its own process (SIGTERM, after answering), and Cloud Run starts
a fresh instance for the next request.

The service only runs code and returns what the run left: the agents service's host
gates (R1-R3) and probe gates judge it (`agents/anyplot/render/gates.py`). Nothing of
a job (code, data, stderr, PNG) is logged, and an unexpected error is logged by its
class and answered `500 internal`, because its message can hold the job's content;
the log carries ids, exit codes, reasons and timings. A request validation error
answers `invalid_job` without echoing the body, because the body is the user's code
and data.

Run locally (without a launcher every render answers `503 sandbox_unavailable`):
`ENVIRONMENT=development uv run uvicorn agents.renderer.main:app --port 8003`.
"""

import asyncio
import contextlib
import importlib.metadata
import json
import logging
import os
import signal
import time
from collections.abc import AsyncIterator, Callable
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi import Path as PathParam
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .auth import CallerRefused, check_caller
from .executor import Executor, ExecutorConfig, SandboxExecutor, Unavailable, mem_available_mb, runs_volume_ok
from .settings import RendererSettings, get_settings
from .wire import JOB_ID_PATTERN, RendererStatus, RenderRequest, RenderResponse, RenderTimings, Theme, ThemeRun


logger = logging.getLogger("agents.renderer")
VERSION_FILE = Path(__file__).with_name("VERSION")
"""Written by the image build from `pyproject.toml`, because the image does not install the project."""
_NO_STORE = {"Cache-Control": "no-store"}
EXIT_DELAY_S = 1.0
"""How long the service waits after scheduling its own exit, so the answer in progress goes out first."""
DISCONNECT_PAUSE_S = 0.5
"""Pause after a `receive()` message that is not `http.disconnect`, so the watcher never spins."""
CLIENT_GONE = 499
"""The answer to a request that was cancelled or whose client left; nobody reads it."""


def _version() -> str:
    try:
        return importlib.metadata.version("anyplot")
    except importlib.metadata.PackageNotFoundError:
        pass
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip() or "dev"
    except OSError:
        return "dev"


def _terminate_soon() -> None:
    """End this process shortly (uvicorn shuts down gracefully on SIGTERM); Cloud Run starts a fresh instance."""
    asyncio.get_running_loop().call_later(EXIT_DELAY_S, os.kill, os.getpid(), signal.SIGTERM)


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
    """The settings, the executor, the slot and the running renders of one service instance."""

    def __init__(
        self, settings: RendererSettings, executor: Executor, *, terminate: Callable[[], None] = _terminate_soon
    ) -> None:
        self.settings = settings
        self.executor = executor
        self.slot = RenderSlot()
        self.version = _version()
        self.terminate = terminate
        self.terminating = False
        self.volume: bool | None = None
        if settings.cloud_run_service:
            self.volume = runs_volume_ok(Path(settings.runs_dir), settings.runs_volume_max_mb * 1024 * 1024)
            if not self.volume:
                logger.error(json.dumps({"event": "runs_volume_missing", "runs_dir": settings.runs_dir}))
        self._running: dict[str, set[asyncio.Task[RenderResponse]]] = {}

    def start(self, job: RenderRequest) -> "asyncio.Task[RenderResponse]":
        """Run `job` as a task that `cancel(job.job_id)` can stop."""
        task = asyncio.create_task(self.render(job))
        self._running.setdefault(job.job_id, set()).add(task)
        task.add_done_callback(lambda done: self._forget(job.job_id, done))
        return task

    def _forget(self, job_id: str, task: "asyncio.Task[RenderResponse]") -> None:
        tasks = self._running.get(job_id)
        if tasks is not None:
            tasks.discard(task)
            if not tasks:
                del self._running[job_id]

    def cancel(self, job_id: str) -> int:
        """Cancel every running render of `job_id`; the executor's kill path stops its sandbox."""
        tasks = [task for task in self._running.get(job_id, ()) if not task.done()]
        for task in tasks:
            task.cancel()
        return len(tasks)

    async def render(self, job: RenderRequest) -> RenderResponse:
        started = time.monotonic()
        try:
            return await self._render(job, started)
        finally:
            self._exit_if_stuck()

    async def _render(self, job: RenderRequest, started: float) -> RenderResponse:
        if self.volume is False:
            raise Unavailable("volume_missing")
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

    def _exit_if_stuck(self) -> None:
        """On Cloud Run, a stuck launcher ends this instance: no render could run on it again."""
        if self.terminating or not self.settings.cloud_run_service or not self.executor.stuck:
            return
        self.terminating = True
        logger.error(json.dumps({"event": "renderer_exiting", "why": "stuck_launcher", "stuck": self.executor.stuck}))
        self.terminate()

    def status(self) -> RendererStatus:
        return RendererStatus(
            version=self.version,
            revision=self.settings.revision,
            in_flight=self.slot.in_flight,
            waiting=self.slot.waiting,
            stuck=self.executor.stuck,
            mem_available_mb=mem_available_mb(),
            sandbox=self.executor.available,
            volume=self.volume,
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


def _internal() -> JSONResponse:
    """The renderer's own 500: a JSON `detail`, so the `remote` backend never mistakes it for the front end's."""
    return JSONResponse(status_code=500, content={"detail": "internal"}, headers=_NO_STORE)


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


@app.exception_handler(Exception)
async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
    """The last resort outside `/render` (which answers its own errors): the class is logged, never the message."""
    logger.error(json.dumps({"event": "renderer_error", "error": type(exc).__name__}))
    return _internal()


async def _client_gone(request: Request) -> None:
    """Return once the server reports the client's disconnect.

    The body has been read by then, so uvicorn's `receive()` blocks until the
    connection closes (or the response is complete, which never happens while the
    render runs) and then answers `http.disconnect`.
    """
    while True:
        message = await request.receive()
        if message.get("type") == "http.disconnect":
            return
        await asyncio.sleep(DISCONNECT_PAUSE_S)


async def _abandon(task: "asyncio.Task[RenderResponse]") -> None:
    """Cancel a render and wait until its sandbox is stopped and its slot is free."""
    task.cancel()
    await asyncio.wait({task})


@app.post("/render", dependencies=caller_checked)
async def render(job: RenderRequest, renderer: RendererDep, request: Request) -> JSONResponse:
    """Run every theme of `job` in its own sandbox, one after the other, inside the render slot."""
    task = renderer.start(job)
    gone = asyncio.create_task(_client_gone(request))
    try:
        await asyncio.wait({task, gone}, return_when=asyncio.FIRST_COMPLETED)
    except asyncio.CancelledError:
        await _abandon(task)
        raise
    finally:
        gone.cancel()
    if not task.done():
        await _abandon(task)
        logger.info(json.dumps({"event": "render_abandoned", "job_id": job.job_id, "why": "client_gone"}))
        return JSONResponse(status_code=CLIENT_GONE, content={"detail": "client_gone"}, headers=_NO_STORE)
    if task.cancelled():
        logger.info(json.dumps({"event": "render_abandoned", "job_id": job.job_id, "why": "cancelled"}))
        return JSONResponse(status_code=CLIENT_GONE, content={"detail": "cancelled"}, headers=_NO_STORE)
    error = task.exception()
    if isinstance(error, Unavailable):
        return await _unavailable(request, error)
    try:
        if error is not None:
            raise error
        content = task.result().model_dump(mode="json")
    except Exception as exc:  # the class only: a message can carry the job's code, data or output
        logger.error(json.dumps({"event": "render_error", "job_id": job.job_id, "error": type(exc).__name__}))
        return _internal()
    return JSONResponse(content=content, headers=_NO_STORE)


@app.post("/render/{job_id}/cancel", dependencies=caller_checked)
async def cancel(job_id: Annotated[str, PathParam(pattern=JOB_ID_PATTERN)], renderer: RendererDep) -> JSONResponse:
    """Stop the renders of `job_id`: the `remote` backend's call when its own render was cancelled or timed out."""
    cancelled = renderer.cancel(job_id)
    logger.info(json.dumps({"event": "render_cancel", "job_id": job_id, "cancelled": cancelled}))
    return JSONResponse(content={"cancelled": cancelled}, headers=_NO_STORE)


@app.get("/status", dependencies=caller_checked)
async def status(renderer: RendererDep) -> JSONResponse:
    return JSONResponse(content=renderer.status().model_dump(mode="json"), headers=_NO_STORE)
