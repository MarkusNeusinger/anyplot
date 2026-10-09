"""The sandbox executor: one `sandbox do` per theme, with a kill path, a byte watchdog and one retry.

Every theme runs in a sandbox of its own, in a run directory of its own:

    /usr/local/gcp/bin/sandbox do --sandbox-name r-<random>-<theme>
        --mount type=bind,source=/tmp/runs/r-<random>-<theme>/work,destination=/work -w /work
        --env PATH=/app/.venv/bin:/usr/local/bin:/usr/bin:/bin --env HOME=/tmp --env ANYPLOT_THEME=<theme> ...
        -- /app/.venv/bin/python -I /opt/anyplot/harness.py plot.py

started with `asyncio.create_subprocess_exec` (never a shell) in a session of its own.
Each rule below comes from spike S or S2 (docs/concepts/agent-network.md, "Render"):

* **No `--write`, no `--allow-egress`.** `--write` makes the sandbox's root filesystem
  writable, and with it a nested egress attempt got one step further (S2). `build_argv`
  asserts that neither flag is ever present.
* **A complete environment.** A sandbox sees only `HOME`, `LC_CTYPE` and the `--env`
  values, with no `PATH`, so `PATH` is passed explicitly.
* **Every user byte under `/tmp/runs/<run>`.** The image and every host file outside
  `/tmp` are readable from inside a sandbox, while sibling run directories are not
  (spike G). On Cloud Run `/tmp/runs` is a size-limited in-memory volume, because a
  disk fill through `/work` crashed the whole instance at about 3.4 GB (S2).
* **A byte watchdog.** The host measures each live run directory every
  `RENDERER_WATCH_INTERVAL_S` and kills the sandbox once it holds more than
  `RENDERER_RUN_BUDGET_MB` or `MAX_RUN_ENTRIES` entries (reason `disk_budget`).
* **The kill path.** On a timeout, the watchdog or a cancellation: `os.killpg` with
  SIGKILL on the launcher's process group, then `sandbox delete --force <name>`.
  `delete` exits 0 even when it did nothing (S2), so the kill counts as confirmed only
  when the launcher process exits. One that does not exit within
  `RENDERER_KILL_GRACE_S` is kept as `stuck`, and every render is refused with
  `503 stuck` until it is gone.
* **One retry with a new sandbox name** when the launcher failed before the harness
  started: a non-zero exit with no `HARNESS` start line on stdout. S2 saw one of 26
  renders end in 0.4 s with `failed to exec in container ... exit status 137` and no
  output. A render whose harness started failed in the plot code and is not retried;
  a second launcher failure is reported with reason `launcher`.
* **Bounded output.** stderr keeps its last `STDERR_LIMIT` bytes and stdout its first
  and last few KiB, however much the code writes. Output files are read without
  following links (`O_NOFOLLOW`, then `fstat`) and under the wire caps.

Strictly serial: the service holds one render slot (`main.py`), and the themes of a
job run one after the other. No ADK import.
"""

import asyncio
import base64
import contextlib
import json
import logging
import math
import os
import secrets
import shutil
import signal
import stat
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .settings import RendererSettings
from .wire import MAX_PNG_BYTES, MAX_PROBE_BYTES, MAX_STDERR_CHARS, RenderRequest, RunReason, Theme, ThemeRun


logger = logging.getLogger(__name__)

SANDBOX_PATH = "/app/.venv/bin:/usr/local/bin:/usr/bin:/bin"
FORBIDDEN_FLAGS = ("--allow-egress", "--write")
WORKDIR = "/work"
CODE_FILE = "plot.py"
DATA_FILE = "data.csv"
LAUNCHER_FAILURE = "failed to exec in container"
HARNESS_START = 'HARNESS {"event": "start"}'
HARNESS_END = 'HARNESS {"event": "end"'
STDERR_LIMIT = 64 * 1024
STDOUT_HEAD = 4 * 1024
STDOUT_TAIL = 4 * 1024
READ_CHUNK = 64 * 1024
MAX_RUN_ENTRIES = 10_000
"""Files and directories one run may create; many tiny files cost memory on the volume too."""
DELETE_TIMEOUT_S = 30.0
READER_GRACE_S = 5.0
MIN_RETRY_S = 1.0
"""A retry needs at least this much of the job's time left."""
MEMINFO = Path("/proc/meminfo")


class Unavailable(Exception):
    """The renderer cannot take a render now; answered as `503 {"detail": code}`."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class OutputRejected(ValueError):
    """An output file the host refuses to read: not a regular file, or over its cap."""


def mem_available_mb(path: Path = MEMINFO) -> int | None:
    """`MemAvailable` in MiB: the memory signal, because the cgroup's `memory.current` is unreadable (S2)."""
    try:
        for line in path.read_text(encoding="ascii").splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


async def read_tail(stream: asyncio.StreamReader | None, limit: int) -> bytes:
    """Read `stream` to its end and keep only its last `limit` bytes."""
    if stream is None:
        return b""
    tail = bytearray()
    while chunk := await stream.read(READ_CHUNK):
        tail += chunk
        if len(tail) > limit:
            del tail[:-limit]
    return bytes(tail)


async def read_head_tail(stream: asyncio.StreamReader | None, head: int, tail: int) -> tuple[bytes, bytes]:
    """Read `stream` to its end and keep its first `head` and its last `tail` bytes."""
    if stream is None:
        return b"", b""
    first = bytearray()
    last = bytearray()
    while chunk := await stream.read(READ_CHUNK):
        if len(first) < head:
            first += chunk[: head - len(first)]
        last += chunk
        if len(last) > tail:
            del last[:-tail]
    return bytes(first), bytes(last)


def tree_size(root: Path, max_bytes: int, max_entries: int) -> tuple[int, int]:
    """Bytes and entries under `root`, without following links; stops early once a limit is passed."""
    total = 0
    entries = 0
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            with os.scandir(current) as listing:
                for entry in listing:
                    entries += 1
                    try:
                        info = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue  # removed while it was listed
                    total += info.st_size
                    if stat.S_ISDIR(info.st_mode):
                        pending.append(Path(entry.path))
                    if total > max_bytes or entries > max_entries:
                        return total, entries
        except OSError:
            continue
    return total, entries


async def watch_run_dir(root: Path, max_bytes: int, interval_s: float) -> None:
    """Return as soon as the run directory holds more than `max_bytes` or `MAX_RUN_ENTRIES` entries."""
    while True:
        await asyncio.sleep(interval_s)
        size, entries = await asyncio.to_thread(tree_size, root, max_bytes, MAX_RUN_ENTRIES)
        if size > max_bytes or entries > MAX_RUN_ENTRIES:
            return


def read_regular(path: Path, max_bytes: int) -> bytes | None:
    """The bytes of a regular file the run left, or None when it is missing.

    Opened with `O_NOFOLLOW` (a symlink fails) and `O_NONBLOCK` (a FIFO cannot block
    the host), then checked with `fstat` on the open descriptor, so what is read is
    exactly what was checked.
    """
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise OutputRejected(f"{path.name} could not be opened as a regular file ({type(exc).__name__})") from None
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise OutputRejected(f"{path.name} is not a regular file")
        if info.st_size > max_bytes:
            raise OutputRejected(f"{path.name} is {info.st_size} bytes, more than the {max_bytes}-byte limit")
        chunks = bytearray()
        while len(chunks) <= max_bytes and (chunk := os.read(descriptor, READ_CHUNK)):
            chunks += chunk
    finally:
        os.close(descriptor)
    if len(chunks) > max_bytes:
        raise OutputRejected(f"{path.name} grew past the {max_bytes}-byte limit while it was read")
    return bytes(chunks)


@dataclass(frozen=True)
class ExecutorConfig:
    """Everything the executor needs, taken from `RendererSettings` (tests build it directly)."""

    sandbox_binary: str
    python: str
    harness: str
    runs_dir: Path
    mpl_seed: str
    mplconfig: str
    run_budget_bytes: int
    watch_interval_s: float
    rlimit_cpu_s: int
    rlimit_fsize_mb: int
    rlimit_as_mb: int
    rlimit_nproc: int
    kill_grace_s: float
    bind_tmp: bool

    @classmethod
    def from_settings(cls, settings: RendererSettings) -> "ExecutorConfig":
        return cls(
            sandbox_binary=settings.sandbox_binary,
            python=settings.python,
            harness=settings.harness,
            runs_dir=Path(settings.runs_dir),
            mpl_seed=settings.mpl_seed,
            mplconfig=settings.mplconfig,
            run_budget_bytes=settings.run_budget_mb * 1024 * 1024,
            watch_interval_s=settings.watch_interval_s,
            rlimit_cpu_s=settings.rlimit_cpu_s,
            rlimit_fsize_mb=settings.rlimit_fsize_mb,
            rlimit_as_mb=settings.rlimit_as_mb,
            rlimit_nproc=settings.rlimit_nproc,
            kill_grace_s=settings.kill_grace_s,
            bind_tmp=settings.bind_tmp,
        )


def sandbox_env(config: ExecutorConfig, theme: Theme, cpu_s: int) -> dict[str, str]:
    """The complete environment inside the sandbox: nothing of the host's reaches it."""
    env = {
        "PATH": SANDBOX_PATH,
        "HOME": "/tmp",
        "ANYPLOT_THEME": theme,
        "MPLBACKEND": "Agg",
        "MPLCONFIGDIR": config.mplconfig,
        "ANYPLOT_MPL_SEED": config.mpl_seed,
        "PYTHONDONTWRITEBYTECODE": "1",
        # One BLAS thread: Agg renders on one core, and every thread reserves address
        # space under RLIMIT_AS and counts toward RLIMIT_NPROC.
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "ANYPLOT_RLIMIT_CPU_S": str(cpu_s),
        "ANYPLOT_RLIMIT_FSIZE_MB": str(config.rlimit_fsize_mb),
    }
    if config.rlimit_as_mb:
        env["ANYPLOT_RLIMIT_AS_MB"] = str(config.rlimit_as_mb)
    if config.rlimit_nproc:
        env["ANYPLOT_RLIMIT_NPROC"] = str(config.rlimit_nproc)
    return env


def build_argv(config: ExecutorConfig, name: str, run_dir: Path, theme: Theme, cpu_s: int) -> list[str]:
    """The `sandbox do` command of one theme; asserted to carry neither `--write` nor `--allow-egress`."""
    argv = [
        config.sandbox_binary,
        "do",
        "--sandbox-name",
        name,
        "--mount",
        f"type=bind,source={run_dir / 'work'},destination={WORKDIR}",
    ]
    if config.bind_tmp:
        argv += ["--mount", f"type=bind,source={run_dir / 'tmp'},destination=/tmp"]
    argv += ["-w", WORKDIR]
    for key, value in sandbox_env(config, theme, cpu_s).items():
        argv += ["--env", f"{key}={value}"]
    flags = list(argv)
    argv += ["--", config.python, "-I", config.harness, CODE_FILE]
    if any(part.split("=", 1)[0] in FORBIDDEN_FLAGS for part in flags):
        raise AssertionError("a sandbox must never get --write or --allow-egress")
    return argv


@dataclass
class Attempt:
    """One launch of one theme's sandbox."""

    name: str
    exit_code: int | None
    timed_out: bool = False
    reason: RunReason | None = None
    stdout_head: str = ""
    stdout_tail: str = ""
    stderr: str = ""
    png: bytes | None = None
    probe: dict[str, Any] | None = None
    wall_s: float = 0.0

    @property
    def harness_started(self) -> bool:
        return HARNESS_START in self.stdout_head.splitlines()

    @property
    def launcher_failed(self) -> bool:
        """The launcher failed before the harness printed its start line: worth one retry."""
        return self.exit_code not in (0, None) and self.reason is None and not self.harness_started

    def usage(self) -> dict[str, float]:
        """The harness's own peak memory and CPU time, from its last end line (advisory)."""
        for line in reversed(self.stdout_tail.splitlines()):
            if not line.startswith(HARNESS_END):
                continue
            try:
                report = json.loads(line.split(" ", 1)[1])
            except (ValueError, IndexError):
                return {}
            if not isinstance(report, dict):
                return {}
            return {
                key: float(value)
                for key, value in report.items()
                if key in ("max_rss_mb", "cpu_s") and isinstance(value, int | float) and math.isfinite(value)
            }
        return {}

    def to_wire(self, theme: Theme, attempts: int) -> ThemeRun:
        usage = self.usage()
        return ThemeRun(
            theme=theme,
            exit_code=self.exit_code,
            timed_out=self.timed_out,
            png_base64=None if self.png is None else _b64(self.png),
            probe=self.probe,
            stderr_tail=self.stderr[-MAX_STDERR_CHARS:],
            wall_s=round(self.wall_s, 3),
            attempts=attempts,
            reason=self.reason,
            max_rss_mb=usage.get("max_rss_mb"),
            cpu_s=usage.get("cpu_s"),
        )


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


async def _settle[T](task: "asyncio.Task[T]", default: T) -> T:
    """The reader's result once the process is gone, or `default` when the pipe stays open."""
    try:
        return await asyncio.wait_for(task, READER_GRACE_S)
    except TimeoutError:
        return default


class Executor(Protocol):
    """What the service needs from an executor; tests substitute a fake."""

    @property
    def stuck(self) -> int: ...

    @property
    def available(self) -> bool: ...

    async def run_theme(self, job: RenderRequest, theme: Theme) -> ThemeRun: ...


class SandboxExecutor:
    """Runs one theme of a job per call in a fresh Cloud Run sandbox."""

    def __init__(self, config: ExecutorConfig, *, clock: Callable[[], float] = time.monotonic) -> None:
        self.config = config
        self.clock = clock
        self._stuck: list[asyncio.subprocess.Process] = []

    @property
    def stuck(self) -> int:
        """Launcher processes that outlived their kill and are still alive."""
        self._stuck = [process for process in self._stuck if process.returncode is None]
        return len(self._stuck)

    @property
    def available(self) -> bool:
        return os.access(self.config.sandbox_binary, os.X_OK)

    async def run_theme(self, job: RenderRequest, theme: Theme) -> ThemeRun:
        """Render one theme; a launcher failure before the harness started is retried once."""
        if not self.available:
            raise Unavailable("sandbox_unavailable")
        if self.stuck:
            raise Unavailable("stuck")
        cpu_s = max(1, min(self.config.rlimit_cpu_s, math.ceil(job.timeout_s)))
        started = self.clock()
        attempt = await self._attempt(job, theme, cpu_s, job.timeout_s)
        attempts = 1
        if attempt.launcher_failed:
            remaining = job.timeout_s - (self.clock() - started)
            _log_attempt(attempt, theme, retry=remaining >= MIN_RETRY_S)
            if remaining >= MIN_RETRY_S:
                attempt = await self._attempt(job, theme, cpu_s, remaining)
                attempts = 2
            if attempt.launcher_failed:
                attempt.reason = "launcher"
        _log_attempt(attempt, theme, retry=False)
        return attempt.to_wire(theme, attempts)

    async def _attempt(self, job: RenderRequest, theme: Theme, cpu_s: int, timeout_s: float) -> Attempt:
        name = f"r-{secrets.token_hex(6)}-{theme}"
        run_dir = self.config.runs_dir / name
        try:
            work = run_dir / "work"
            work.mkdir(parents=True)
            # The sandbox is uid 0 behind gVisor's gofer, and the spikes ran with these
            # modes; the host runs no other user, so nothing else can reach the files.
            os.chmod(run_dir, 0o777)
            os.chmod(work, 0o777)
            if self.config.bind_tmp:
                tmp = run_dir / "tmp"
                tmp.mkdir()
                os.chmod(tmp, 0o1777)
            (work / CODE_FILE).write_text(job.source, encoding="utf-8")
            (work / DATA_FILE).write_text(job.data_csv, encoding="utf-8")
            return await self._run(name, run_dir, theme, cpu_s, timeout_s)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

    async def _run(self, name: str, run_dir: Path, theme: Theme, cpu_s: int, timeout_s: float) -> Attempt:
        argv = build_argv(self.config, name, run_dir, theme, cpu_s)
        started = self.clock()
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        stdout_task = asyncio.create_task(read_head_tail(process.stdout, STDOUT_HEAD, STDOUT_TAIL))
        stderr_task = asyncio.create_task(read_tail(process.stderr, STDERR_LIMIT))
        exited = asyncio.create_task(process.wait())
        watchdog = asyncio.create_task(
            watch_run_dir(run_dir, self.config.run_budget_bytes, self.config.watch_interval_s)
        )
        reason: RunReason | None = None
        try:
            done, _ = await asyncio.wait({exited, watchdog}, timeout=timeout_s, return_when=asyncio.FIRST_COMPLETED)
            if exited not in done:
                reason = "disk_budget" if watchdog in done else "timeout"
                await self._stop(name, process)
        except asyncio.CancelledError:
            # The client went away: stop the sandbox before _attempt removes its run
            # directory, then let the cancellation through.
            await asyncio.shield(self._stop(name, process))
            stdout_task.cancel()
            stderr_task.cancel()
            raise
        finally:
            watchdog.cancel()
            exited.cancel()
        wall = self.clock() - started
        head, tail = await _settle(stdout_task, (b"", b""))
        stderr = await _settle(stderr_task, b"")
        attempt = Attempt(
            name=name,
            exit_code=None if reason else process.returncode,
            timed_out=reason == "timeout",
            reason=reason,
            stdout_head=head.decode("utf-8", errors="replace"),
            stdout_tail=tail.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
            wall_s=wall,
        )
        if reason != "disk_budget":
            self._collect(attempt, run_dir / "work", theme)
        return attempt

    def _collect(self, attempt: Attempt, work: Path, theme: Theme) -> None:
        """Read the PNG and the probe the run left; a refused PNG is reported, a broken probe is simply absent."""
        try:
            attempt.png = read_regular(work / f"plot-{theme}.png", MAX_PNG_BYTES)
        except OutputRejected as exc:
            attempt.reason = "output_rejected"
            attempt.stderr = str(exc)
        try:
            raw = read_regular(work / f"probe-{theme}.json", MAX_PROBE_BYTES)
            loaded = json.loads(raw) if raw else None
            attempt.probe = loaded if isinstance(loaded, dict) else None
        except (OutputRejected, ValueError, RecursionError):
            attempt.probe = None

    async def _stop(self, name: str, process: asyncio.subprocess.Process) -> None:
        """Kill the launcher's process group, delete the sandbox, and confirm by the launcher's exit."""
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(process.pid, signal.SIGKILL)
        await self._delete(name)
        try:
            await asyncio.wait_for(process.wait(), self.config.kill_grace_s)
        except TimeoutError:
            self._stuck.append(process)
            logger.error(json.dumps({"event": "sandbox_stuck", "sandbox": name}))

    async def _delete(self, name: str) -> None:
        """`sandbox delete --force <name>`; its exit code proves nothing (it is 0 for an unknown name)."""
        try:
            deleter = await asyncio.create_subprocess_exec(
                self.config.sandbox_binary,
                "delete",
                "--force",
                name,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            logger.error(json.dumps({"event": "sandbox_delete_failed", "sandbox": name, "error": type(exc).__name__}))
            return
        try:
            await asyncio.wait_for(deleter.wait(), DELETE_TIMEOUT_S)
        except TimeoutError:
            with contextlib.suppress(ProcessLookupError):
                deleter.kill()
            await deleter.wait()


def _log_attempt(attempt: Attempt, theme: Theme, *, retry: bool) -> None:
    """One JSON line per sandbox launch: ids, codes and timings, never stdout, stderr or code."""
    logger.info(
        json.dumps(
            {
                "event": "sandbox",
                "sandbox": attempt.name,
                "theme": theme,
                "exit_code": attempt.exit_code,
                "reason": attempt.reason,
                "harness_started": attempt.harness_started,
                "launcher_message": LAUNCHER_FAILURE in attempt.stderr,
                "retry": retry,
                "wall_s": round(attempt.wall_s, 3),
                "png_bytes": None if attempt.png is None else len(attempt.png),
            }
        )
    )
