"""The local render backend: one Docker container per theme, development only.

Every theme runs as

    docker run --rm --name r-<job>-<theme> --network none --read-only --tmpfs /tmp
        --cap-drop ALL --security-opt no-new-privileges --pids-limit 256 --memory 2g
        --user <uid>:<gid> -v <rundir>:/work -v <harness>:/opt/anyplot/harness.py:ro -w /work
        -e ANYPLOT_THEME=<theme> -e MPLBACKEND=Agg ... <image> /app/.venv/bin/python -I /opt/anyplot/harness.py plot.py

started with `asyncio.create_subprocess_exec` (never a shell) in its own process
group. The image is `AGENT_RENDER_IMAGE`, the production agents image. The harness
is mounted read-only from this checkout, so a render uses the harness of the code
under development. On timeout the container is killed by name. The run directory is
a fresh temporary directory that is removed afterwards.

The backend refuses `ENVIRONMENT=production` and fails when Docker is missing:
there is no bare-subprocess fallback, because that would run model-written code on
the host with the host's network and files.
"""

import asyncio
import os
import shutil
import tempfile
import time
from pathlib import Path

from ..contract import RendererUnavailable, RenderJob, RenderResult, RuntimeAdapter, Theme, ThemeOutput
from ..png import PngRejected
from ..runtimes.python import HARNESS_SOURCE, IMAGE_HARNESS


MEMORY_LIMIT = "2g"
PIDS_LIMIT = "256"
STDERR_LIMIT = 64 * 1024


class LocalDockerBackend:
    """Renders in throwaway Docker containers without network access."""

    name = "local"

    def __init__(
        self, *, image: str, runtime: RuntimeAdapter, environment: str, concurrency: int, docker: str | None = None
    ) -> None:
        if environment == "production":
            raise RendererUnavailable("the local renderer refuses ENVIRONMENT=production")
        found = docker or shutil.which("docker")
        if not found:
            raise RendererUnavailable("the local renderer needs Docker, and no docker executable was found")
        self.docker = found
        self.image = image
        self.runtime = runtime
        self._semaphore = asyncio.Semaphore(concurrency)

    def argv(self, job: RenderJob, theme: Theme, run_dir: Path) -> list[str]:
        """The docker command of one theme; asserted to keep the network off."""
        argv = [
            self.docker,
            "run",
            "--rm",
            "--name",
            f"r-{job.job_id}-{theme}",
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
            "-w",
            "/work",
        ]
        for key, value in self.runtime.env(theme).items():
            argv += ["-e", f"{key}={value}"]
        argv += [self.image, *self.runtime.command(theme)]
        if argv[argv.index("--network") + 1] != "none" or any("--network=" in part for part in argv):
            raise AssertionError("a render container must never have network access")
        return argv

    async def _run_theme(self, job: RenderJob, theme: Theme, run_dir: Path) -> ThemeOutput:
        async with self._semaphore:
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
                _, stderr = await asyncio.wait_for(process.communicate(), timeout=job.timeout_s)
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
        try:
            png, probe = self.runtime.collect(run_dir, theme)
        except PngRejected as exc:
            return ThemeOutput(theme, process.returncode, timed_out, None, None, str(exc), wall)
        tail = (stderr or b"")[-STDERR_LIMIT:].decode("utf-8", errors="replace")
        return ThemeOutput(theme, None if timed_out else process.returncode, timed_out, png, probe, tail, wall)

    async def _kill(self, name: str, process: asyncio.subprocess.Process) -> None:
        killer = await asyncio.create_subprocess_exec(
            self.docker, "kill", name, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await killer.wait()
        if process.returncode is None:
            process.kill()
            await process.wait()

    async def render(self, job: RenderJob) -> RenderResult:
        run_dir = Path(tempfile.mkdtemp(prefix=f"anyplot-run-{job.job_id}-"))
        try:
            os.chmod(run_dir, 0o700)
            (run_dir / self.runtime.file_name).write_text(job.source, encoding="utf-8")
            (run_dir / "data.csv").write_text(job.data_csv, encoding="utf-8")
            outputs = await asyncio.gather(*(self._run_theme(job, theme, run_dir) for theme in job.themes))
            return RenderResult(job.job_id, {output.theme: output for output in outputs})
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)
