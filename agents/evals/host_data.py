"""The prep eval's render backend: the fake renderer, with data runs that execute the snippet like `/run-data` does.

The fake renderer answers every data run with one fixture table (`FIXTURE_CSV`, four
rows of `x` and `y`), whatever the snippet computes. The prep eval lets the real root
read that answer, and the root reads it right: a 500-step random walk that comes back
as four squares is not the user's data, so it runs the code a second time or falls back
to `generate_data`. On 2026-10-15 nine of the eval's eleven data-code cases missed for
that reason alone (36 of 50, 72 percent, below the 80 percent gate). The eval measured
the fake, not the root.

`HostDataBackend` keeps the fake's renders and conversions (no prep case renders) and
runs a data snippet the way the renderer does: the real harness in data mode
(`harness.py --data snippet.py`) with the renderer's data-run limits
(`PythonRuntime.data_env`), in a fresh private directory, its outcome read by the
local backend's reader (`local.collect_data_run`), so `run_data_code` gets the same
`DataOutput` it would get from `POST /run-data`: the table the snippet computed, or the
harness's refusal with its exit code and caps.

It runs on this machine, without the container. What stands between the snippet and
the machine is what the renderer has inside its container: `run_data_code` runs only a
snippet the DATA validator passed (an import allow-list, no dunder, no `open`), the
harness arms its audit-hook guard before the snippet runs (no file, process, network or
native-library access), the limits cap CPU seconds, address space and file size, the
interpreter runs isolated (`-I`) with a minimal environment, and the run directory is
removed afterwards. `RLIMIT_NPROC` is left out: outside a container it counts every
process of the developer's user, so the renderer's 64 would refuse the snippet's first
thread. The backend is for the eval only (`ENVIRONMENT=development`); it refuses
production as the local backend does.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import signal
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from agents.anyplot.render.backends.fake import FakeBackend
from agents.anyplot.render.backends.local import collect_data_run, read_tail
from agents.anyplot.render.contract import DataJob, DataOutput, RendererUnavailable
from agents.anyplot.render.harness import DATA_FLAG
from agents.anyplot.render.runtimes.python import DATA_FILE_NAME, HARNESS_SOURCE, PythonRuntime


HOST_ENV_DROPPED = ("ANYPLOT_RLIMIT_NPROC",)
"""Limits of the renderer's data environment that do not carry over to a run outside a container (module docstring)."""


def host_data_env(run_dir: Path, cpu_seconds: int) -> dict[str, str]:
    """The renderer's data-run environment (`PythonRuntime.data_env`) for a run in `run_dir` on this machine."""
    env = {
        key: value
        for key, value in PythonRuntime(cpu_seconds=cpu_seconds).data_env().items()
        if key not in HOST_ENV_DROPPED
    }
    return {**env, "HOME": str(run_dir), "PATH": "/usr/bin:/bin"}


@dataclass
class HostDataBackend(FakeBackend):
    """Fixture renders and conversions; data runs execute the snippet under the real harness (module docstring)."""

    name: str = "fake+host-data"
    python: str = sys.executable
    cpu_seconds: int = 60
    environment: str = "development"

    def __post_init__(self) -> None:
        if self.environment == "production":
            raise RendererUnavailable("the prep eval's host data runs refuse ENVIRONMENT=production")

    def data_argv(self) -> list[str]:
        """The harness in data mode, as `PythonRuntime.data_command` runs it in the renderer's image."""
        return [self.python, "-I", str(HARNESS_SOURCE), DATA_FLAG, DATA_FILE_NAME]

    async def run_data(self, job: DataJob) -> DataOutput:
        """Run the snippet in a fresh private directory and read what it left there as the renderer does."""
        self.data_jobs.append(job)
        if self.data_script is not None:
            return self.data_script(job)
        run_dir = Path(tempfile.mkdtemp(prefix=f"anyplot-eval-data-{job.job_id}-"))
        try:
            os.chmod(run_dir, 0o700)
            (run_dir / DATA_FILE_NAME).write_text(job.source, encoding="utf-8")
            started = time.monotonic()
            process = await asyncio.create_subprocess_exec(
                *self.data_argv(),
                cwd=run_dir,
                env=host_data_env(run_dir, self.cpu_seconds),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
            try:
                tail = await asyncio.wait_for(_drain_and_wait(process), timeout=job.timeout_s)
            except TimeoutError:
                await _kill(process)
                return DataOutput(exit_code=None, timed_out=True, wall_s=time.monotonic() - started)
            except asyncio.CancelledError:
                await asyncio.shield(_kill(process))
                raise
            wall = time.monotonic() - started
            return collect_data_run(run_dir, process.returncode, tail.decode("utf-8", errors="replace"), wall)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


async def _drain_and_wait(process: asyncio.subprocess.Process) -> bytes:
    tail = await read_tail(process.stderr)
    await process.wait()
    return tail


async def _kill(process: asyncio.subprocess.Process) -> None:
    """Kill the run's process group (it was started in a session of its own) and reap it."""
    if process.returncode is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        await process.wait()
