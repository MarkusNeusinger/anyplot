"""Tests for agents/renderer/executor.py: the launcher command, the kill path, the retry, the watchdog and the bounds.

The launcher is the fake in `helpers.FAKE_LAUNCHER`; the code runs under the real
probe harness with this interpreter, so every run here is a real subprocess.
"""

import asyncio
import base64
import os
import signal
import stat
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from agents.renderer import executor as executor_module
from agents.renderer.executor import (
    HARNESS_START,
    SANDBOX_PATH,
    Attempt,
    ExecutorConfig,
    OutputRejected,
    SandboxExecutor,
    Unavailable,
    build_argv,
    mem_available_mb,
    read_head_tail,
    read_regular,
    read_tail,
    runs_volume_ok,
    sandbox_env,
    tree_size,
)
from agents.renderer.settings import RendererSettings
from agents.renderer.wire import MAX_STDERR_CHARS, ThemeRun

from .conftest import FakeLauncher
from .helpers import PLOT, SLEEPER, job


def envs(argv: list[str]) -> dict[str, str]:
    return dict(argv[index + 1].split("=", 1) for index, part in enumerate(argv) if part == "--env")


class TestCommand:
    def test_argv_runs_the_harness_in_the_work_mount_with_a_complete_environment(
        self, config: ExecutorConfig, tmp_path: Path
    ) -> None:
        run_dir = tmp_path / "r-abc-dark"
        argv = build_argv(config, "r-abc-dark", run_dir, "dark", 30)

        assert argv[:4] == [config.sandbox_binary, "do", "--sandbox-name", "r-abc-dark"]
        assert f"type=bind,source={run_dir / 'work'},destination=/work" in argv
        assert argv[argv.index("-w") + 1] == "/work"
        assert argv[argv.index("--") :] == ["--", config.python, "-I", config.harness, "plot.py"]
        assert "--write" not in argv and not any(part.startswith("--allow-egress") for part in argv)
        values = envs(argv)
        assert values["PATH"] == SANDBOX_PATH  # a sandbox has no PATH of its own (spike S2)
        assert values["HOME"] == "/tmp" and values["ANYPLOT_THEME"] == "dark" and values["MPLBACKEND"] == "Agg"
        assert values["MPLCONFIGDIR"] == config.mplconfig and values["ANYPLOT_MPL_SEED"] == config.mpl_seed
        assert values["ANYPLOT_RLIMIT_CPU_S"] == "30" and values["ANYPLOT_RLIMIT_FSIZE_MB"] == "50"
        assert "ANYPLOT_RLIMIT_AS_MB" not in values and "ANYPLOT_RLIMIT_NPROC" not in values

    def test_deployed_defaults_set_every_rlimit_from_spike_s2(self) -> None:
        config = ExecutorConfig.from_settings(RendererSettings())
        values = sandbox_env(config, "light", 60)

        assert config.sandbox_binary == "/usr/local/gcp/bin/sandbox"
        assert config.runs_dir == Path("/tmp/runs") and config.run_budget_bytes == 64 * 1024 * 1024
        assert values["ANYPLOT_RLIMIT_CPU_S"] == "60" and values["ANYPLOT_RLIMIT_FSIZE_MB"] == "50"
        assert values["ANYPLOT_RLIMIT_AS_MB"] == "1024" and values["ANYPLOT_RLIMIT_NPROC"] == "64"
        assert values["MPLCONFIGDIR"] == "/tmp/mpl" and values["ANYPLOT_MPL_SEED"] == "/opt/mplconfig"

    def test_bind_tmp_mounts_a_run_directory_over_tmp(self, config: ExecutorConfig, tmp_path: Path) -> None:
        argv = build_argv(replace(config, bind_tmp=True), "r-abc-light", tmp_path / "r", "light", 60)

        assert f"type=bind,source={tmp_path / 'r' / 'tmp'},destination=/tmp" in argv

    def test_forbidden_flags_never_reach_the_launcher(
        self, config: ExecutorConfig, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(executor_module, "sandbox_env", lambda *args: {"--write": ""})

        with pytest.raises(AssertionError, match="--write"):
            build_argv(config, "r-abc-light", tmp_path, "light", 60)


class TestRender:
    async def test_a_theme_renders_with_png_probe_and_usage(
        self, executor: SandboxExecutor, launcher: FakeLauncher, config: ExecutorConfig
    ) -> None:
        run = await executor.run_theme(job(PLOT), "dark")

        assert run.exit_code == 0, run.stderr_tail
        assert run.reason is None and run.attempts == 1 and not run.timed_out
        assert run.png_base64 is not None and base64.b64decode(run.png_base64).startswith(b"\x89PNG")
        assert run.probe is not None and run.probe["canvas"] == [200, 100]
        assert run.max_rss_mb is not None and run.max_rss_mb > 0
        assert len(launcher.launches()) == 1 and launcher.launches()[0].endswith("-dark")
        assert launcher.deletes() == []  # a clean exit needs no delete
        assert envs(launcher.calls()[0])["ANYPLOT_THEME"] == "dark"
        assert list(config.runs_dir.iterdir()) == []  # every run directory is removed

    async def test_timeout_kills_the_launcher_and_deletes_the_sandbox(
        self, executor: SandboxExecutor, launcher: FakeLauncher, config: ExecutorConfig
    ) -> None:
        started = time.monotonic()
        run = await executor.run_theme(job(SLEEPER, timeout_s=1.5), "light")

        assert run.timed_out and run.exit_code is None and run.reason == "timeout"
        assert time.monotonic() - started < 15
        assert launcher.deletes() == launcher.launches()  # `delete --force` for the killed sandbox
        assert executor.stuck == 0  # the kill was confirmed by the launcher's exit
        assert list(config.runs_dir.iterdir()) == []

    async def test_cancellation_kills_the_sandbox_before_its_directory_goes(
        self, executor: SandboxExecutor, launcher: FakeLauncher, config: ExecutorConfig
    ) -> None:
        task = asyncio.create_task(executor.run_theme(job(SLEEPER), "light"))
        for _ in range(200):
            if launcher.launches():
                break
            await asyncio.sleep(0.05)
        await asyncio.sleep(0.2)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task
        assert launcher.deletes() == launcher.launches()
        assert executor.stuck == 0
        assert list(config.runs_dir.iterdir()) == []

    async def test_a_launcher_that_outlives_its_kill_blocks_renders_until_it_exits(
        self, config: ExecutorConfig, launcher: FakeLauncher, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        executor = SandboxExecutor(replace(config, kill_grace_s=0.2))
        monkeypatch.setattr(executor_module, "READER_GRACE_S", 0.2)
        monkeypatch.setattr(executor_module.os, "killpg", lambda pid, sig: None)  # the kill has no effect

        run = await executor.run_theme(job(SLEEPER, timeout_s=1.0), "light")

        assert run.timed_out and executor.stuck == 1
        with pytest.raises(Unavailable, match="stuck"):
            await executor.run_theme(job(PLOT), "light")
        survivor = executor._stuck[0]
        os.kill(survivor.pid, signal.SIGKILL)
        await survivor.wait()
        assert executor.stuck == 0

    async def test_a_missing_launcher_is_unavailable(self, config: ExecutorConfig, tmp_path: Path) -> None:
        executor = SandboxExecutor(replace(config, sandbox_binary=str(tmp_path / "missing")))

        assert executor.available is False
        with pytest.raises(Unavailable, match="sandbox_unavailable"):
            await executor.run_theme(job(PLOT), "light")


class TestRetry:
    async def test_a_launcher_failure_before_the_harness_is_retried_once_with_a_new_name(
        self, executor: SandboxExecutor, launcher: FakeLauncher
    ) -> None:
        launcher.fail_next(1)

        run = await executor.run_theme(job(PLOT), "light")

        assert run.exit_code == 0 and run.attempts == 2 and run.reason is None and run.png_base64
        names = launcher.launches()
        assert len(names) == 2 and names[0] != names[1]

    async def test_a_second_launcher_failure_is_reported(
        self, executor: SandboxExecutor, launcher: FakeLauncher
    ) -> None:
        launcher.fail_next(2)

        run = await executor.run_theme(job(PLOT), "light")

        assert run.exit_code == 1 and run.attempts == 2 and run.reason == "launcher" and run.png_base64 is None
        assert "failed to exec in container" in run.stderr_tail
        assert len(launcher.launches()) == 2
        assert launcher.deletes() == launcher.launches()  # a failed launch may leave a half-created sandbox

    async def test_a_failure_in_the_plot_code_is_not_retried(
        self, executor: SandboxExecutor, launcher: FakeLauncher
    ) -> None:
        run = await executor.run_theme(job("raise ValueError('a cell of the data')\n"), "light")

        assert run.exit_code == 1 and run.attempts == 1 and run.reason is None
        assert "ValueError" in run.stderr_tail
        assert len(launcher.launches()) == 1 and launcher.deletes() == launcher.launches()

    def test_only_a_run_without_the_harness_start_line_counts_as_a_launcher_failure(self) -> None:
        assert Attempt("r", exit_code=1).launcher_failed
        assert not Attempt("r", exit_code=1, stdout_head=f"{HARNESS_START}\n").launcher_failed
        assert not Attempt("r", exit_code=0).launcher_failed
        assert not Attempt("r", exit_code=None, timed_out=True, reason="timeout").launcher_failed
        assert not Attempt("r", exit_code=None, reason="disk_budget").launcher_failed


class TestBounds:
    async def test_the_byte_watchdog_kills_a_run_over_its_budget(
        self, executor: SandboxExecutor, launcher: FakeLauncher, config: ExecutorConfig
    ) -> None:
        source = (
            "import time\n"
            "with open('fill.bin', 'wb') as handle:\n"
            "    for _ in range(400):\n"
            "        handle.write(b'x' * 1024 * 1024)\n"
            "        handle.flush()\n"
            "        time.sleep(0.01)\n"
        )
        run = await executor.run_theme(job(source), "light")

        assert run.reason == "disk_budget" and run.exit_code is None and not run.timed_out
        assert run.png_base64 is None
        assert launcher.deletes() == launcher.launches()
        assert list(config.runs_dir.iterdir()) == []

    async def test_the_watchdog_counts_entries_too(
        self, executor: SandboxExecutor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(executor_module, "MAX_RUN_ENTRIES", 50)
        source = "import time\nfor index in range(5000):\n    open(f'f{index}', 'w').close()\n    time.sleep(0.001)\n"
        run = await executor.run_theme(job(source), "light")

        assert run.reason == "file_budget" and run.limit == 50
        assert run.measured is not None and run.measured > 50

    async def test_the_byte_watchdog_reports_the_measured_size_and_the_budget(
        self, executor: SandboxExecutor, config: ExecutorConfig
    ) -> None:
        source = "import time\nopen('fill.bin', 'wb').write(b'x' * 12 * 1024 * 1024)\ntime.sleep(30)\n"

        run = await executor.run_theme(job(source), "light")

        assert run.reason == "disk_budget" and run.limit == config.run_budget_bytes
        assert run.measured is not None and run.measured > config.run_budget_bytes

    async def test_a_tree_past_path_max_counts_as_over_its_limit(
        self, executor: SandboxExecutor, launcher: FakeLauncher
    ) -> None:
        """A walk by full paths cannot see past PATH_MAX; what it cannot measure must not escape the budget."""
        source = (
            "import os, time\nfor _ in range(40):\n    os.mkdir('d' * 200)\n    os.chdir('d' * 200)\ntime.sleep(30)\n"
        )

        run = await executor.run_theme(job(source), "light")

        assert run.reason == "file_budget" and run.measured is None and run.exit_code is None
        assert launcher.deletes() == launcher.launches()

    async def test_the_memory_floor_kills_the_run(
        self, config: ExecutorConfig, launcher: FakeLauncher, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A sandbox's private /tmp counts as instance memory (S2), so the watchdog reads MemAvailable too."""
        readings = iter([3000, 3000, 400])
        executor = SandboxExecutor(replace(config, kill_mem_available_mb=512), memory=lambda: next(readings, 400))

        run = await executor.run_theme(job(SLEEPER), "light")

        assert run.reason == "memory" and (run.measured, run.limit) == (400, 512)
        assert run.exit_code is None and not run.timed_out and run.png_base64 is None
        assert launcher.deletes() == launcher.launches()

    async def test_a_host_io_error_is_unavailable_and_leaves_nothing(
        self, executor: SandboxExecutor, launcher: FakeLauncher, config: ExecutorConfig, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def full(self: Path, *args: object, **kwargs: object) -> None:
            raise OSError(28, "No space left on device")

        monkeypatch.setattr(Path, "write_text", full)

        with pytest.raises(Unavailable, match="io"):
            await executor.run_theme(job(PLOT), "light")
        assert launcher.launches() == [] and list(config.runs_dir.iterdir()) == []

    async def test_a_launcher_that_cannot_start_is_unavailable(
        self, executor: SandboxExecutor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def no_fork(*args: object, **kwargs: object) -> None:
            raise BlockingIOError(11, "Resource temporarily unavailable")

        monkeypatch.setattr(executor_module.asyncio, "create_subprocess_exec", no_fork)

        with pytest.raises(Unavailable, match="io"):
            await executor.run_theme(job(PLOT), "light")

    async def test_stderr_keeps_only_its_tail(self, executor: SandboxExecutor) -> None:
        source = "import sys\nsys.stderr.write('x' * 2_000_000)\nsys.stderr.write('THE-END')\nraise SystemExit(3)\n"

        run = await executor.run_theme(job(source), "light")

        assert run.exit_code == 3 and run.attempts == 1
        assert len(run.stderr_tail) <= MAX_STDERR_CHARS and run.stderr_tail.endswith("THE-END")

    async def test_a_flood_on_stdout_keeps_the_harness_lines(self, executor: SandboxExecutor) -> None:
        run = await executor.run_theme(job("print('y' * 3_000_000)\n" + PLOT), "light")

        assert run.exit_code == 0 and run.attempts == 1 and run.png_base64 is not None
        assert run.max_rss_mb is not None  # the end line survives in the stdout tail

    async def test_a_symlinked_png_is_refused(self, executor: SandboxExecutor) -> None:
        source = "import os\nos.symlink('/etc/hostname', 'plot-light.png')\n"

        run = await executor.run_theme(job(source), "light")

        assert run.exit_code == 0 and run.png_base64 is None and run.reason == "output_rejected"

    async def test_a_broken_probe_is_absent(self, executor: SandboxExecutor) -> None:
        source = PLOT + "open('probe-light.json', 'w').write('[1, 2')\n"

        run = await executor.run_theme(job(source), "light")

        assert run.png_base64 is not None and run.probe is None

    async def test_an_oversized_png_reports_its_size_and_the_cap(
        self, executor: SandboxExecutor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(executor_module, "MAX_PNG_BYTES", 100)

        run = await executor.run_theme(job(PLOT), "light")

        assert run.reason == "output_rejected" and run.limit == 100
        assert run.measured is not None and run.measured > 100 and run.png_base64 is None

    @pytest.mark.parametrize("depth", [17, 210, 300])
    async def test_a_deeply_nested_probe_is_dropped_and_the_answer_still_serialises(
        self, executor: SandboxExecutor, depth: int
    ) -> None:
        """256 levels broke `model_dump`, about 200 the agents' parse; the renderer drops the probe instead."""
        source = PLOT + f"open('probe-light.json', 'w').write('{{\"a\": ' + '[' * {depth} + ']' * {depth} + '}}')\n"

        run = await executor.run_theme(job(source), "light")

        assert run.png_base64 is not None and run.probe is None
        ThemeRun.model_validate_json(run.model_dump_json())

    @pytest.mark.parametrize(
        "report",
        [
            '{"event": "end", "max_rss_mb": 1' + "0" * 400 + ', "cpu_s": -5}',
            '{"event": "end", "max_rss_mb": 1e999, "cpu_s": NaN}',
            '{"event": "end", "max_rss_mb": true, "cpu_s": "12"}',
            '{"event": "end", "max_rss_mb": ' + "[" * 5000 + "]" * 5000 + "}",
        ],
    )
    def test_a_forged_end_line_cannot_break_the_answer(self, report: str) -> None:
        """The code shares stdout; a JSON int too large for a float made `to_wire` raise OverflowError (a 500)."""
        attempt = Attempt("r", exit_code=0, stdout_tail=f"HARNESS {report}\n")

        run = attempt.to_wire("light", 1)

        assert run.max_rss_mb is None and run.cpu_s is None
        assert Attempt("r", 0, stdout_tail='HARNESS {"event": "end", "max_rss_mb": 150.5, "cpu_s": 2}').usage() == {
            "max_rss_mb": 150.5,
            "cpu_s": 2.0,
        }


class TestHelpers:
    async def test_read_tail_and_head_tail_hold_bounded_bytes(self) -> None:
        reader = asyncio.StreamReader()
        reader.feed_data(b"a" * 100_000 + b"END")
        reader.feed_eof()
        assert await read_tail(reader, 10) == b"aaaaaaaEND"

        reader = asyncio.StreamReader()
        reader.feed_data(b"HEAD" + b"m" * 100_000 + b"TAIL")
        reader.feed_eof()
        head, tail = await read_head_tail(reader, 4, 4)
        assert (head, tail) == (b"HEAD", b"TAIL")

    def test_read_regular_refuses_links_fifos_directories_and_oversize(self, tmp_path: Path) -> None:
        (tmp_path / "ok.png").write_bytes(b"12345")
        os.symlink(tmp_path / "ok.png", tmp_path / "link.png")
        os.mkfifo(tmp_path / "fifo.png")
        (tmp_path / "dir.png").mkdir()

        assert read_regular(tmp_path / "ok.png", 5) == b"12345"
        assert read_regular(tmp_path / "missing.png", 5) is None
        for name in ("link.png", "fifo.png", "dir.png"):
            with pytest.raises(OutputRejected):
                read_regular(tmp_path / name, 5)
        with pytest.raises(OutputRejected, match="limit"):
            read_regular(tmp_path / "ok.png", 4)

    def test_tree_size_does_not_follow_links_and_stops_early(self, tmp_path: Path) -> None:
        big = tmp_path / "outside.bin"
        big.write_bytes(b"x" * 10_000)
        root = tmp_path / "run"
        (root / "work" / "nested").mkdir(parents=True)
        (root / "work" / "nested" / "a.bin").write_bytes(b"y" * 100)
        os.symlink(big, root / "work" / "link")

        usage = tree_size(root, 1_000_000, 1_000)

        listed = [root / "work", root / "work" / "nested", root / "work" / "nested" / "a.bin", root / "work" / "link"]
        assert usage.measurable and usage.entries == 4
        assert usage.bytes == sum(os.lstat(path).st_size for path in listed)  # the link's own size only
        assert tree_size(root, 10, 1_000).bytes > 10  # stops once over budget

    def test_a_tree_too_deep_or_too_long_is_unmeasurable(self, tmp_path: Path) -> None:
        root = tmp_path / "run"
        deep = root.joinpath(*["d"] * 6)
        deep.mkdir(parents=True)

        assert tree_size(root, 1_000_000, 1_000, max_depth=8).measurable
        assert not tree_size(root, 1_000_000, 1_000, max_depth=5).measurable

        # Past PATH_MAX a full-path walk fails with ENAMETOOLONG; that must not read as "nothing here".
        long_root = tmp_path / "long"
        long_root.mkdir()
        descriptor = os.open(long_root, os.O_RDONLY)
        try:
            for _ in range(25):
                os.mkdir("n" * 200, dir_fd=descriptor)
                child = os.open("n" * 200, os.O_RDONLY, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
        finally:
            os.close(descriptor)
        assert not tree_size(long_root, 1_000_000, 1_000).measurable

    def test_runs_volume_ok_needs_a_small_mount_of_its_own(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert runs_volume_ok(tmp_path, 1 << 40, root=tmp_path) is False  # the same filesystem as `/`
        assert runs_volume_ok(tmp_path / "missing", 1 << 40) is False

        real_stat = os.stat

        def other_device(path: str | os.PathLike[str], *args: object, **kwargs: object) -> os.stat_result:
            result = real_stat(path)
            if Path(path) == tmp_path:
                values = list(result)
                values[stat.ST_DEV] = result.st_dev + 1
                return os.stat_result(values)
            return result

        monkeypatch.setattr(executor_module.os, "stat", other_device)
        monkeypatch.setattr(executor_module.shutil, "disk_usage", lambda path: SimpleNamespace(total=512 << 20))
        assert runs_volume_ok(tmp_path, 1024 << 20) is True
        assert runs_volume_ok(tmp_path, 256 << 20) is False  # a mount larger than the volume should be

    def test_mem_available_reads_meminfo(self, tmp_path: Path) -> None:
        meminfo = tmp_path / "meminfo"
        meminfo.write_text("MemTotal:  4194304 kB\nMemFree: 1 kB\nMemAvailable:  3145728 kB\n")

        assert mem_available_mb(meminfo) == 3072
        assert mem_available_mb(tmp_path / "missing") is None
