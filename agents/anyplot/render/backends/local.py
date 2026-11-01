"""The local render backend: one Docker container per theme, development only.

Every theme runs as

    docker run --rm --name r-<job>-<theme> --network none --read-only --tmpfs /tmp
        --cap-drop ALL --security-opt no-new-privileges --pids-limit 256 --memory 2g
        --user <uid>:<gid> -v <rundir>:/work -v <harness>:/opt/anyplot/harness.py:ro -w /work
        -e ANYPLOT_THEME=<theme> -e MPLBACKEND=Agg ... <image>
        /app/.venv/bin/python -I -X disable-remote-debug /opt/anyplot/harness.py plot.py

started with `asyncio.create_subprocess_exec` (never a shell) in its own process
group. The image is `AGENT_RENDER_IMAGE`, the production renderer image built from
`agents/renderer/Dockerfile` (it has the plotting venv at `/app/.venv`). The harness
is mounted read-only from this checkout, so a render uses the harness of the code
under development; a JavaScript container also gets the checkout's browser harness
(`automation/js-render/render.mjs`) over the image's, renders and page builds alike, so
the PNG and the page of one version come from the same harness (JS-4b; a checkout without
the file, an agents image, keeps the image's), and so does a plotly or bokeh container,
whose screenshot step is that harness (PB-2a). On timeout the container is killed by name.
The run directory is a fresh temporary directory that is removed afterwards. stdout is discarded and stderr
is read while the container runs, keeping only its last `STDERR_LIMIT` bytes: the
code under test writes it, so it can be arbitrarily large. A theme's stderr tail is then
cut as the renderer cuts it (`executor.stderr_tail` with the row's `stderr_head`). A
JavaScript job's typed table (`RenderJob.data_json`) is written as `data.json` next to
the code file and named in `ANYPLOT_DATA_JSON`, as the renderer's executor does.

The backend holds no semaphore: `SerialRenderer` (`render/serial.py`), which
`Services.backend` puts in front of every backend, hands it one theme at a time.

A data run (`run_data`) uses the same isolation with the harness in data mode
(`harness.py --data snippet.py`), no theme and no plotting settings, and reads the
harness's `status.json` (its exit code and a refusal's measured value and cap, as the
renderer does) and the `out.csv` it wrote after exit code 0, under the computed-data cap.
A conversion (`convert`) does the same with the harness in convert mode on `input.bin`
(the converter mounted read-only next to the harness), and reads `out.csv` under the paste
cap and `meta.json`. A page build (`page`) runs a JavaScript render's container with
`ANYPLOT_PAGE_ONLY=1`, as the renderer's `POST /page` does, and reads `plot-<theme>.html`
under `wire.MAX_PAGE_BYTES` after exit code 0.

The backend refuses `ENVIRONMENT=production` and fails when Docker is missing:
there is no bare-subprocess fallback, because that would run model-written code on
the host with the host's network and files.
"""

import asyncio
import json
import os
import shutil
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from agents.renderer.commands import JS_HARNESS, command_for
from agents.renderer.executor import DATA_JSON_ENV, DATA_JSON_FILE, WORKDIR, stderr_tail
from agents.renderer.wire import (
    CONVERT_META_FILE,
    CONVERT_REQUEST_FILE,
    DATA_STATUS_FILE,
    MAX_CONVERT_META_BYTES,
    MAX_CONVERT_TEXT_BYTES,
    MAX_DATA_STATUS_BYTES,
    MAX_PAGE_BYTES,
    PAGE_FILE,
    PAGE_ONLY_ENV,
    ConvertMeta,
    convert_refusal,
    parse_data_status,
)

from ...data.parse import MAX_COMPUTED_BYTES
from ..contract import (
    ConvertJob,
    ConvertOutput,
    DataJob,
    DataOutput,
    PageFailed,
    PageJob,
    RendererUnavailable,
    RenderJob,
    RenderResult,
    RuntimeAdapter,
    Theme,
    ThemeOutput,
)
from ..harness import DATA_OUT_FILE
from ..png import PngRejected, read_output
from ..runtimes.javascript import JS_HARNESS_SOURCE
from ..runtimes.python import (
    CONVERT_INPUT_NAME,
    CONVERTER_SOURCE,
    DATA_FILE_NAME,
    HARNESS_SOURCE,
    IMAGE_CONVERTER,
    IMAGE_HARNESS,
)


MEMORY_LIMIT = "2g"
PIDS_LIMIT = "256"
STDERR_LIMIT = 64 * 1024
READ_CHUNK = 64 * 1024


async def read_tail(stream: asyncio.StreamReader | None, limit: int = STDERR_LIMIT) -> bytes:
    """Read `stream` to its end and keep only its last `limit` bytes.

    At most `limit` plus one chunk is held at any time, however much the process writes.
    """
    if stream is None:
        return b""
    tail = bytearray()
    while chunk := await stream.read(READ_CHUNK):
        tail += chunk
        if len(tail) > limit:
            del tail[:-limit]
    return bytes(tail)


def collect_data_run(run_dir: Path, returncode: int | None, tail: str, wall: float) -> DataOutput:
    """What a finished data run left in `run_dir`, as the renderer reads it: the harness's `status.json` first (its
    exit code and a refusal's measured value and cap), the launcher's `returncode` without one, and `out.csv` under
    the computed-data cap after exit code 0.

    One reader for every harness run outside the renderer service: this backend's containers and the prep eval's
    data runs (`agents/evals/host_data.py`), so the two answer `run_data_code` alike.
    """
    try:
        status = parse_data_status(read_output(run_dir / DATA_STATUS_FILE, MAX_DATA_STATUS_BYTES))
    except PngRejected:
        status = None
    exit_code = status.exit if status is not None else returncode
    if exit_code != 0:
        measured, limit = (status.measured, status.limit) if status is not None else (None, None)
        return DataOutput(exit_code=exit_code, stderr_tail=tail, wall_s=wall, measured=measured, limit=limit)
    try:
        raw = read_output(run_dir / DATA_OUT_FILE, MAX_COMPUTED_BYTES)
    except PngRejected as exc:  # the size and the cap of an oversized file, as the renderer's `_collect_data` sets them
        return DataOutput(
            exit_code=0, stderr_tail=tail, wall_s=wall, reason="output_rejected", measured=exc.size, limit=exc.limit
        )
    try:
        text = raw.decode("utf-8") if raw is not None else None
    except UnicodeDecodeError:
        return DataOutput(exit_code=0, stderr_tail=tail, wall_s=wall, reason="output_rejected")
    return DataOutput(exit_code=0, csv_text=text, stderr_tail=tail, wall_s=wall)


async def _drain_and_wait(process: asyncio.subprocess.Process) -> bytes:
    """The stderr tail of `process` once it has exited."""
    tail = await read_tail(process.stderr)
    await process.wait()
    return tail


class LocalDockerBackend:
    """Renders in throwaway Docker containers without network access."""

    name = "local"

    def __init__(
        self,
        *,
        image: str,
        runtime: RuntimeAdapter,
        environment: str,
        docker: str | None = None,
        runtime_for: Callable[[str], RuntimeAdapter] | None = None,
    ) -> None:
        """`runtime` is the Python runtime, which data runs and conversions use; `runtime_for` resolves a render
        job's runtime by its library (the registry's `runtime_for`), else every render uses `runtime`."""
        if environment == "production":
            raise RendererUnavailable("the local renderer refuses ENVIRONMENT=production")
        found = docker or shutil.which("docker")
        if not found:
            raise RendererUnavailable("the local renderer needs Docker, and no docker executable was found")
        self.docker = found
        self.image = image
        self.runtime = runtime
        self.runtime_for = runtime_for

    def _runtime(self, library: str) -> RuntimeAdapter:
        return self.runtime_for(library) if self.runtime_for is not None else self.runtime

    def argv(self, job: RenderJob, theme: Theme, run_dir: Path) -> list[str]:
        """The docker command of one theme; asserted to keep the network off."""
        runtime = self._runtime(job.library)
        # plotly's and bokeh's screenshot step is the browser harness too (`RuntimeCommand.figure`).
        browser = runtime.language == "javascript" or bool(command_for(runtime.language, runtime.library).figure)
        argv = self._isolation(f"r-{job.job_id}-{theme}", run_dir, javascript=browser)
        for key, value in runtime.env(theme).items():
            argv += ["-e", f"{key}={value}"]
        if job.data_json is not None:
            # The page's table, which `render()` wrote next to the code file (`executor.sandbox_env`).
            argv += ["-e", f"{DATA_JSON_ENV}={WORKDIR}/{DATA_JSON_FILE}"]
        argv += [self.image, *runtime.command(theme)]
        if argv[argv.index("--network") + 1] != "none" or any("--network=" in part for part in argv):
            raise AssertionError("a render container must never have network access")
        return argv

    def page_argv(self, job: PageJob, run_dir: Path) -> list[str]:
        """The docker command of a page build: a JavaScript render's container with `ANYPLOT_PAGE_ONLY=1`."""
        runtime = self._runtime(job.library)
        argv = self._isolation(f"r-{job.job_id}-page-{job.theme}", run_dir, javascript=True)
        for key, value in runtime.env(job.theme).items():
            argv += ["-e", f"{key}={value}"]
        argv += ["-e", f"{DATA_JSON_ENV}={WORKDIR}/{DATA_JSON_FILE}", "-e", f"{PAGE_ONLY_ENV}=1"]
        argv += [self.image, *runtime.command(job.theme)]
        if argv[argv.index("--network") + 1] != "none" or any("--network=" in part for part in argv):
            raise AssertionError("a page container must never have network access")
        return argv

    def _isolation(self, name: str, run_dir: Path, *, javascript: bool = False) -> list[str]:
        """`docker run` with the run directory as `/work` and everything else locked down, up to the environment.

        A JavaScript container also mounts the checkout's browser harness over the image's (module docstring)."""
        harness = ["-v", f"{JS_HARNESS_SOURCE}:{JS_HARNESS}:ro"] if javascript and JS_HARNESS_SOURCE.is_file() else []
        return [
            self.docker,
            "run",
            "--rm",
            "--name",
            name,
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            "/tmp",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            PIDS_LIMIT,
            "--memory",
            MEMORY_LIMIT,
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "-v",
            f"{run_dir}:/work",
            "-v",
            f"{HARNESS_SOURCE}:{IMAGE_HARNESS}:ro",
            "-v",
            f"{CONVERTER_SOURCE}:{IMAGE_CONVERTER}:ro",
            *harness,
            "-w",
            "/work",
        ]

    async def _run_theme(self, job: RenderJob, theme: Theme, run_dir: Path) -> ThemeOutput:
        started = time.monotonic()
        process = await asyncio.create_subprocess_exec(
            *self.argv(job, theme, run_dir),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        timed_out = False
        try:
            stderr = await asyncio.wait_for(_drain_and_wait(process), timeout=job.timeout_s)
        except TimeoutError:
            timed_out = True
            await self._kill(f"r-{job.job_id}-{theme}", process)
            stderr = b""
        except asyncio.CancelledError:
            # An abort or the request deadline: stop the container before render()
            # removes the run directory under it, then let the cancellation through.
            await asyncio.shield(self._kill(f"r-{job.job_id}-{theme}", process))
            raise
        wall = time.monotonic() - started
        runtime = self._runtime(job.library)
        try:
            png, probe = runtime.collect(run_dir, theme)
        except PngRejected as exc:
            return ThemeOutput(theme, process.returncode, timed_out, None, None, str(exc), wall)
        # The renderer's cut of the stderr, the row's head line included (Julia's `ERROR:` line).
        head = command_for(runtime.language, runtime.library).stderr_head
        tail = stderr_tail(stderr.decode("utf-8", errors="replace"), head)
        return ThemeOutput(theme, None if timed_out else process.returncode, timed_out, png, probe, tail, wall)

    async def _kill(self, name: str, process: asyncio.subprocess.Process) -> None:
        killer = await asyncio.create_subprocess_exec(
            self.docker, "kill", name, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await killer.wait()
        if process.returncode is None:
            process.kill()
            await process.wait()

    def data_argv(self, job: DataJob, run_dir: Path) -> list[str]:
        """The docker command of a data run: the render's isolation, the harness in data mode, no theme."""
        argv = self._isolation(f"r-{job.job_id}-data", run_dir)
        for key, value in self.runtime.data_env(job.timeout_s).items():
            argv += ["-e", f"{key}={value}"]
        argv += [self.image, *self.runtime.data_command()]
        if argv[argv.index("--network") + 1] != "none" or any("--network=" in part for part in argv):
            raise AssertionError("a data container must never have network access")
        return argv

    async def run_data(self, job: DataJob) -> DataOutput:
        """Run a data snippet in a throwaway container and read the `out.csv` the harness wrote after exit code 0."""
        run_dir = Path(tempfile.mkdtemp(prefix=f"anyplot-data-{job.job_id}-"))
        name = f"r-{job.job_id}-data"
        try:
            os.chmod(run_dir, 0o700)
            (run_dir / DATA_FILE_NAME).write_text(job.source, encoding="utf-8")
            started = time.monotonic()
            process = await asyncio.create_subprocess_exec(
                *self.data_argv(job, run_dir),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
            try:
                stderr = await asyncio.wait_for(_drain_and_wait(process), timeout=job.timeout_s)
            except TimeoutError:
                await self._kill(name, process)
                return DataOutput(exit_code=None, timed_out=True, wall_s=time.monotonic() - started)
            except asyncio.CancelledError:
                await asyncio.shield(self._kill(name, process))
                raise
            wall = time.monotonic() - started
            return collect_data_run(run_dir, process.returncode, stderr.decode("utf-8", errors="replace"), wall)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

    def convert_argv(self, job: ConvertJob, run_dir: Path) -> list[str]:
        """The docker command of a conversion: the render's isolation, the harness in convert mode."""
        argv = self._isolation(f"r-{job.job_id}-convert", run_dir)
        for key, value in self.runtime.convert_env().items():
            argv += ["-e", f"{key}={value}"]
        argv += [self.image, *self.runtime.convert_command()]
        if argv[argv.index("--network") + 1] != "none" or any("--network=" in part for part in argv):
            raise AssertionError("a conversion container must never have network access")
        return argv

    async def convert(self, job: ConvertJob) -> ConvertOutput:
        """Convert a file in a throwaway container; read the text and `meta.json` after exit code 0."""
        run_dir = Path(tempfile.mkdtemp(prefix=f"anyplot-convert-{job.job_id}-"))
        name = f"r-{job.job_id}-convert"
        try:
            os.chmod(run_dir, 0o700)
            (run_dir / CONVERT_INPUT_NAME).write_bytes(job.data)
            (run_dir / CONVERT_REQUEST_FILE).write_text(json.dumps({"sheet": job.sheet}), encoding="utf-8")
            started = time.monotonic()
            process = await asyncio.create_subprocess_exec(
                *self.convert_argv(job, run_dir),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
            try:
                await asyncio.wait_for(_drain_and_wait(process), timeout=job.timeout_s)
            except TimeoutError:
                await self._kill(name, process)
                return ConvertOutput(
                    exit_code=None, timed_out=True, reason="timeout", wall_s=time.monotonic() - started
                )
            except asyncio.CancelledError:
                await asyncio.shield(self._kill(name, process))
                raise
            wall = time.monotonic() - started
            try:
                status = parse_data_status(read_output(run_dir / DATA_STATUS_FILE, MAX_DATA_STATUS_BYTES))
            except PngRejected:
                status = None
            exit_code = status.exit if status is not None else process.returncode
            if exit_code != 0:
                measured, limit = (status.measured, status.limit) if status is not None else (None, None)
                return ConvertOutput(
                    exit_code=exit_code,
                    refusal=convert_refusal(exit_code),
                    measured=measured,
                    limit=limit,
                    damage=status.damage if status is not None else None,
                    wall_s=wall,
                )
            try:
                raw = read_output(run_dir / DATA_OUT_FILE, MAX_CONVERT_TEXT_BYTES)
                meta_raw = read_output(run_dir / CONVERT_META_FILE, MAX_CONVERT_META_BYTES)
                if raw is None or meta_raw is None:
                    raise ValueError("missing output")
                text = raw.decode("utf-8")
                meta = ConvertMeta.model_validate_json(meta_raw, strict=True)
            except PngRejected, ValueError:
                return ConvertOutput(exit_code=0, reason="output_rejected", wall_s=wall)
            return ConvertOutput(exit_code=0, text=text, meta=meta, wall_s=wall)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

    async def render(self, job: RenderJob) -> RenderResult:
        run_dir = Path(tempfile.mkdtemp(prefix=f"anyplot-run-{job.job_id}-"))
        try:
            os.chmod(run_dir, 0o700)
            (run_dir / self._runtime(job.library).file_name).write_text(job.source, encoding="utf-8")
            (run_dir / "data.csv").write_text(job.data_csv, encoding="utf-8")
            if job.data_json is not None:
                (run_dir / DATA_JSON_FILE).write_text(job.data_json, encoding="utf-8")
            outputs = await asyncio.gather(*(self._run_theme(job, theme, run_dir) for theme in job.themes))
            return RenderResult(job.job_id, {output.theme: output for output in outputs})
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

    async def page(self, job: PageJob) -> str:
        """Build a JavaScript version's page in a throwaway container; read `plot-<theme>.html` after exit code 0."""
        run_dir = Path(tempfile.mkdtemp(prefix=f"anyplot-page-{job.job_id}-"))
        name = f"r-{job.job_id}-page-{job.theme}"
        try:
            os.chmod(run_dir, 0o700)
            (run_dir / self._runtime(job.library).file_name).write_text(job.source, encoding="utf-8")
            (run_dir / DATA_JSON_FILE).write_text(job.data_json, encoding="utf-8")
            started = time.monotonic()
            process = await asyncio.create_subprocess_exec(
                *self.page_argv(job, run_dir),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
            try:
                stderr = await asyncio.wait_for(_drain_and_wait(process), timeout=job.timeout_s)
            except TimeoutError:
                await self._kill(name, process)
                raise PageFailed(exit_code=None, reason="timeout", wall_s=time.monotonic() - started) from None
            except asyncio.CancelledError:
                await asyncio.shield(self._kill(name, process))
                raise
            wall = time.monotonic() - started
            tail = stderr_tail(stderr.decode("utf-8", errors="replace"))
            if process.returncode != 0:
                raise PageFailed(exit_code=process.returncode, stderr_tail=tail, wall_s=wall)
            try:
                raw = read_output(run_dir / PAGE_FILE.format(theme=job.theme), MAX_PAGE_BYTES)
                if raw is None:
                    raise PageFailed(exit_code=0, stderr_tail=tail, wall_s=wall)
                return raw.decode("utf-8")
            except (PngRejected, UnicodeDecodeError) as exc:
                raise PageFailed(exit_code=0, reason="output_rejected", stderr_tail=tail, wall_s=wall) from exc
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)
