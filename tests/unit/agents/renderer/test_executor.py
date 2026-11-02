"""Tests for agents/renderer/executor.py: the launcher command, the kill path, the retry, the watchdog and the bounds.

The launcher is the fake in `helpers.FAKE_LAUNCHER`; the code runs under the real
probe harness with this interpreter, so every run here is a real subprocess.
"""

import asyncio
import base64
import json
import os
import resource
import signal
import stat
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from agents.anyplot.render import harness
from agents.renderer import executor as executor_module
from agents.renderer.commands import EXEC_DENY_ENV, LIBRARY_LANGUAGES, command_for
from agents.renderer.executor import (
    HARNESS_START,
    SANDBOX_PATH,
    STDERR_HEAD_CHARS,
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
    stderr_tail,
    tree_size,
)
from agents.renderer.settings import RendererSettings
from agents.renderer.wire import MAX_STDERR_CHARS, RenderRequest, ThemeRun

from .conftest import FakeLauncher
from .helpers import PLOT, SLEEPER, convert_job, data_job, job


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
        assert argv[argv.index("--") :] == [
            "--",
            config.python,
            "-I",
            "-X",
            "disable-remote-debug",
            config.harness,
            "plot.py",
        ]
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

    def test_every_run_but_javascript_requires_the_exec_filter_and_the_switch_lifts_it(self) -> None:
        """Renders of every Python row, data runs, conversions and the R and Julia rows (whose harness preloads the
        filter into the child, since 2026-10-29); the JavaScript row has `exec_deny` off. `RENDERER_EXEC_DENY=
        optional` is the switch for a platform that stops admitting the filter."""
        config = ExecutorConfig.from_settings(RendererSettings())
        assert config.exec_deny == "required" == RendererSettings().exec_deny
        filtered = [library for library, language in LIBRARY_LANGUAGES.items() if language != "javascript"]
        runs = [
            sandbox_env(config, "dark", 60, command=command_for(LIBRARY_LANGUAGES[library], library))
            for library in filtered
        ]
        runs += [sandbox_env(config, None, 20), sandbox_env(config, None, 10, convert=True)]
        assert all(run[EXEC_DENY_ENV] == "required" for run in runs)
        assert EXEC_DENY_ENV not in sandbox_env(config, "dark", 60, command=command_for("javascript", "d3"))
        optional = replace(config, exec_deny="optional")
        assert EXEC_DENY_ENV not in sandbox_env(optional, "dark", 60, command=command_for("python", "letsplot"))
        assert EXEC_DENY_ENV not in sandbox_env(optional, "dark", 60, command=command_for("r", "ggplot2"))
        assert EXEC_DENY_ENV not in sandbox_env(optional, None, 20)
        assert ExecutorConfig.from_settings(RendererSettings(exec_deny="optional")).exec_deny == "optional"

    def test_the_exec_filter_switch_is_read_from_its_variable_and_takes_only_its_two_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("RENDERER_EXEC_DENY", "optional")
        assert RendererSettings().exec_deny == "optional"
        monkeypatch.setenv("RENDERER_EXEC_DENY", "off")
        with pytest.raises(ValueError, match="exec_deny"):
            RendererSettings()

    def test_bind_tmp_mounts_a_run_directory_over_tmp(self, config: ExecutorConfig, tmp_path: Path) -> None:
        argv = build_argv(replace(config, bind_tmp=True), "r-abc-light", tmp_path / "r", "light", 60)

        assert f"type=bind,source={tmp_path / 'r' / 'tmp'},destination=/tmp" in argv

    def test_forbidden_flags_never_reach_the_launcher(
        self, config: ExecutorConfig, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(executor_module, "sandbox_env", lambda *args, **kwargs: {"--write": ""})

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
        # The fake launcher execs the harness, so the survivor carries the run's RLIMIT_CPU, which a real
        # `sandbox do` on the host never does. With the one second of a one-second job, the kernel's SIGKILL
        # ended the "stuck" launcher inside the grace window whenever the harness start (matplotlib, a fresh
        # font cache) spent that second, as it did on a loaded CI runner (2026-10-23). The full host cap
        # leaves the survivor nothing but the test's own kill to die of.
        monkeypatch.setattr(executor_module, "run_cpu_seconds", lambda limit_s, timeout_s: limit_s)

        run = await executor.run_theme(job(SLEEPER, timeout_s=1.0), "light")

        assert run.timed_out and executor.stuck == 1
        survivor = executor._stuck[0]
        assert resource.prlimit(survivor.pid, resource.RLIMIT_CPU) == (config.rlimit_cpu_s,) * 2
        with pytest.raises(Unavailable, match="stuck"):
            await executor.run_theme(job(PLOT), "light")
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


ESCAPED_HARNESS = """\
import runpy
import sys

print('HARNESS {"event": "start"}', flush=True)
runpy.run_path(sys.argv[-1], run_name="__main__")
"""
"""A harness without its audit hook: code that got past the in-process guard, which is what the host's watchdog and
output checks must assume. The real harness refuses these writes, links and directories itself
(tests/unit/agents/runtime/test_harness_guard.py); these tests pin the layer behind it."""


@pytest.fixture
def escaped(config: ExecutorConfig, tmp_path: Path) -> SandboxExecutor:
    path = tmp_path / "escaped_harness.py"
    path.write_text(ESCAPED_HARNESS, encoding="utf-8")
    return SandboxExecutor(replace(config, harness=str(path)))


class TestBounds:
    async def test_the_byte_watchdog_kills_a_run_over_its_budget(
        self, escaped: SandboxExecutor, launcher: FakeLauncher, config: ExecutorConfig
    ) -> None:
        source = (
            "import time\n"
            "with open('fill.bin', 'wb') as handle:\n"
            "    for _ in range(400):\n"
            "        handle.write(b'x' * 1024 * 1024)\n"
            "        handle.flush()\n"
            "        time.sleep(0.01)\n"
        )
        run = await escaped.run_theme(job(source), "light")

        assert run.reason == "disk_budget" and run.exit_code is None and not run.timed_out
        assert run.png_base64 is None
        assert launcher.deletes() == launcher.launches()
        assert list(config.runs_dir.iterdir()) == []

    async def test_a_fast_writer_that_exits_between_two_samples_is_still_refused(
        self, config: ExecutorConfig, launcher: FakeLauncher, escaped: SandboxExecutor
    ) -> None:
        """The watchdog sleeps between looks; a run that writes past the budget and exits before the next look must not pass."""
        executor = SandboxExecutor(replace(escaped.config, watch_interval_s=30.0))  # the watchdog never samples
        source = "open('fill.bin', 'wb').write(b'x' * 12 * 1024 * 1024)\n"

        run = await executor.run_theme(job(source), "light")

        assert run.reason == "disk_budget" and run.limit == config.run_budget_bytes
        assert run.measured is not None and run.measured > config.run_budget_bytes
        assert run.exit_code is None and run.png_base64 is None and not run.timed_out
        assert launcher.deletes() == launcher.launches()
        assert list(config.runs_dir.iterdir()) == []

    async def test_the_watchdog_counts_entries_too(
        self, escaped: SandboxExecutor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(executor_module, "MAX_RUN_ENTRIES", 50)
        source = "import time\nfor index in range(5000):\n    open(f'f{index}', 'w').close()\n    time.sleep(0.001)\n"
        run = await escaped.run_theme(job(source), "light")

        assert run.reason == "file_budget" and run.limit == 50
        assert run.measured is not None and run.measured > 50

    async def test_the_byte_watchdog_reports_the_measured_size_and_the_budget(
        self, escaped: SandboxExecutor, config: ExecutorConfig
    ) -> None:
        source = "import time\nopen('fill.bin', 'wb').write(b'x' * 12 * 1024 * 1024)\ntime.sleep(30)\n"

        run = await escaped.run_theme(job(source), "light")

        assert run.reason == "disk_budget" and run.limit == config.run_budget_bytes
        assert run.measured is not None and run.measured > config.run_budget_bytes

    async def test_a_tree_past_path_max_counts_as_over_its_limit(
        self, escaped: SandboxExecutor, launcher: FakeLauncher
    ) -> None:
        """A walk by full paths cannot see past PATH_MAX; what it cannot measure must not escape the budget."""
        source = (
            "import os, time\nfor _ in range(40):\n    os.mkdir('d' * 200)\n    os.chdir('d' * 200)\ntime.sleep(30)\n"
        )

        run = await escaped.run_theme(job(source), "light")

        assert run.reason == "file_budget" and run.measured is None and run.exit_code is None
        assert launcher.deletes() == launcher.launches()

    async def test_the_memory_floor_kills_the_run(
        self, config: ExecutorConfig, launcher: FakeLauncher, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A sandbox's private /tmp counts as instance memory (S2), so the watchdog reads MemAvailable too."""

        def available() -> int:
            # The floor is crossed once the launcher has logged its `do`: a kill before
            # that line (a loaded machine starts the fake launcher slowly) would leave
            # the launch out of the log this test compares the deletes with.
            return 400 if launcher.launches() else 3000

        executor = SandboxExecutor(replace(config, kill_mem_available_mb=512), memory=available)

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

    async def test_the_real_harness_refuses_the_fill_before_the_watchdog(
        self, executor: SandboxExecutor, config: ExecutorConfig
    ) -> None:
        source = "open('fill.bin', 'wb').write(b'x' * 12 * 1024 * 1024)\n"

        run = await executor.run_theme(job(source), "light")

        assert run.reason is None and run.exit_code not in (0, None) and run.png_base64 is None
        assert "blocked by the render sandbox" in run.stderr_tail

    async def test_a_symlinked_png_is_refused(self, escaped: SandboxExecutor) -> None:
        source = "import os\nos.symlink('/etc/hostname', 'plot-light.png')\n"

        run = await escaped.run_theme(job(source), "light")

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

    @pytest.mark.parametrize(
        ("report", "state"),
        [
            ('{"event": "end", "max_rss_mb": 1, "exec_deny": "on"}', "on"),
            ('{"event": "end", "exec_deny": "unavailable"}', "unavailable"),
            ('{"event": "end", "exec_deny": "yes"}', None),
            ('{"event": "end", "exec_deny": ["on"]}', None),
            ('{"event": "end"}', None),
            ('{"event": "end", "exec_deny": ' + "[" * 5000 + "]" * 5000 + "}", None),
        ],
    )
    def test_the_exec_filter_s_state_is_taken_from_the_end_line_and_logged(
        self, caplog: pytest.LogCaptureFixture, report: str, state: str | None
    ) -> None:
        """One production render then shows whether Cloud Run's sandbox lets the harness add its seccomp filter."""
        caplog.set_level("INFO", logger=executor_module.__name__)
        attempt = Attempt("r", exit_code=0, stdout_tail=f"HARNESS {report}\n")

        executor_module._log_attempt(attempt, "light", retry=False)

        assert attempt.exec_deny() == state
        (line,) = [record.getMessage() for record in caplog.records if '"event": "sandbox"' in record.getMessage()]
        assert json.loads(line)["exec_deny"] == state


class TestDataRun:
    def test_argv_runs_the_harness_in_data_mode_without_theme_or_matplotlib(
        self, config: ExecutorConfig, tmp_path: Path
    ) -> None:
        argv = build_argv(config, "r-abc-data", tmp_path / "r", None, 20)

        assert argv[argv.index("--") :] == [
            "--",
            config.python,
            "-I",
            "-X",
            "disable-remote-debug",
            config.harness,
            "--data",
            "snippet.py",
        ]
        assert "--write" not in argv and not any(part.startswith("--allow-egress") for part in argv)
        values = envs(argv)
        assert values["PATH"] == SANDBOX_PATH and values["ANYPLOT_RLIMIT_CPU_S"] == "20"
        assert not {"ANYPLOT_THEME", "MPLBACKEND", "MPLCONFIGDIR", "ANYPLOT_MPL_SEED"} & set(values)

    async def test_a_snippet_returns_its_table(
        self, executor: SandboxExecutor, launcher: FakeLauncher, config: ExecutorConfig
    ) -> None:
        run = await executor.run_data(data_job())

        assert run.exit_code == 0, run.stderr_tail
        assert run.csv_text == "x,y\n1,3\n2,4\n" and run.reason is None and run.attempts == 1
        assert len(launcher.launches()) == 1 and launcher.launches()[0].endswith("-data")
        assert "ANYPLOT_THEME" not in envs(launcher.calls()[0])
        assert list(config.runs_dir.iterdir()) == []

    async def test_an_error_returns_no_table_and_the_traceback_tail(self, executor: SandboxExecutor) -> None:
        run = await executor.run_data(data_job("x = 1\nraise ValueError('a secret')\n"))

        assert run.exit_code == harness.DATA_EXIT["error"] and run.csv_text is None
        assert 'snippet.py", line 2' in run.stderr_tail

    @pytest.mark.parametrize("sigpipe", [False, True], ids=["exit code kept", "launcher dies of SIGPIPE"])
    async def test_a_cap_refusal_reports_the_harness_code_and_its_numbers(
        self,
        executor: SandboxExecutor,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        sigpipe: bool,
    ) -> None:
        """Live case of 2026-10-14: Cloud Run's launcher turned the harness's `too_large` into -13."""
        if sigpipe:
            monkeypatch.setenv("FAKE_SANDBOX_SIGPIPE", "1")
        caplog.set_level("INFO", logger=executor_module.__name__)
        source = (  # 20,000 rows of ten full-precision floats: over the 2 MiB computed-data cap
            "import numpy as np\nimport pandas as pd\n"
            "df = pd.DataFrame({f'v{k}': np.linspace(0, 1, 20000) / (k + 3) for k in range(10)})\n"
        )

        run = await executor.run_data(data_job(source))

        assert run.exit_code == harness.DATA_EXIT["too_large"] and run.reason is None and run.csv_text is None
        assert run.limit == harness.DATA_MAX_CSV_BYTES and run.measured is not None and run.measured > run.limit
        (line,) = [record.getMessage() for record in caplog.records if '"event": "sandbox"' in record.getMessage()]
        assert ('"launcher_signal": 13' in line) is sigpipe and '"harness_exit": 7' in line

    async def test_a_snippet_error_keeps_its_code_behind_a_sigpipe_launcher(
        self, executor: SandboxExecutor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("FAKE_SANDBOX_SIGPIPE", "1")

        run = await executor.run_data(data_job("x = 1\nraise ValueError('a secret')\n"))

        assert run.exit_code == harness.DATA_EXIT["error"] and 'snippet.py", line 2' in run.stderr_tail

    def test_a_status_file_the_snippet_could_not_have_written_is_ignored_when_malformed(
        self, executor: SandboxExecutor, tmp_path: Path
    ) -> None:
        attempt = Attempt("r", exit_code=-13)
        for raw in (b'{"exit": true}', b"not json", b'{"exit": 999}', b'{"exit": 7, "measured": -1}'):
            (tmp_path / "status.json").write_bytes(raw)
            executor._read_status(attempt, tmp_path)
            assert attempt.harness_exit is None and attempt.to_data_wire(1).exit_code == -13

    async def test_the_guard_refuses_a_write_and_nothing_is_collected(self, executor: SandboxExecutor) -> None:
        source = "import pandas as pd\nopen('out.csv', 'w').write('a\\n1\\n')\ndf = pd.DataFrame({'a': [2]})\n"

        run = await executor.run_data(data_job(source))

        assert run.exit_code == harness.DATA_EXIT["blocked"] and run.csv_text is None

    async def test_a_timeout_kills_the_run(self, executor: SandboxExecutor, launcher: FakeLauncher) -> None:
        run = await executor.run_data(data_job(SLEEPER, timeout_s=1.0))

        assert run.timed_out and run.exit_code is None and run.csv_text is None
        assert launcher.deletes() == launcher.launches()

    async def test_an_oversized_table_is_refused(
        self, executor: SandboxExecutor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(executor_module, "MAX_CSV_BYTES", 4)

        run = await executor.run_data(data_job())

        assert run.reason == "output_rejected" and run.limit == 4 and run.csv_text is None

    async def test_a_launcher_failure_is_retried_once(self, executor: SandboxExecutor, launcher: FakeLauncher) -> None:
        launcher.fail_next(1)

        run = await executor.run_data(data_job())

        assert run.exit_code == 0 and run.attempts == 2 and run.csv_text is not None
        assert len(set(launcher.launches())) == 2

    def test_collect_refuses_text_that_is_not_utf8(self, executor: SandboxExecutor, tmp_path: Path) -> None:
        (tmp_path / "out.csv").write_bytes(b"a\n\xff\n")
        attempt = Attempt("r", exit_code=0)

        executor._collect_data(attempt, tmp_path)

        assert attempt.reason == "output_rejected" and attempt.csv_text is None

    def test_collect_refuses_a_link(self, executor: SandboxExecutor, tmp_path: Path) -> None:
        (tmp_path / "out.csv").symlink_to("/etc/hostname")
        attempt = Attempt("r", exit_code=0)

        executor._collect_data(attempt, tmp_path)

        assert attempt.reason == "output_rejected" and attempt.csv_text is None


class TestConvert:
    def test_argv_runs_the_harness_in_convert_mode_with_the_system_allocator(
        self, config: ExecutorConfig, tmp_path: Path
    ) -> None:
        argv = build_argv(config, "r-abc-convert", tmp_path / "r", None, 10, convert=True)

        assert argv[argv.index("--") :] == [
            "--",
            config.python,
            "-I",
            "-X",
            "disable-remote-debug",
            config.harness,
            "--convert",
            "input.bin",
        ]
        values = envs(argv)
        assert values["ARROW_DEFAULT_MEMORY_POOL"] == "system" and values["ANYPLOT_RLIMIT_CPU_S"] == "10"
        assert not {"ANYPLOT_THEME", "MPLBACKEND"} & set(values)
        assert "ARROW_DEFAULT_MEMORY_POOL" not in envs(build_argv(config, "r-abc-data", tmp_path / "r", None, 10))

    async def test_a_workbook_returns_its_text_and_meta(
        self, executor: SandboxExecutor, launcher: FakeLauncher, config: ExecutorConfig
    ) -> None:
        from tests.unit.agents.runtime.convert_fixtures import Sheet, xlsx

        data = xlsx([Sheet("A", [["a"]]), Sheet("B", [["x", "y"], [1, 2]])])
        run = await executor.run_convert(convert_job(data, sheet="B"))

        assert run.exit_code == 0 and run.refusal is None and run.reason is None
        assert run.text == "x,y\n1,2\n"
        assert run.meta is not None and (run.meta.kind, run.meta.sheet, run.meta.sheets) == ("xlsx", "B", ["A", "B"])
        assert launcher.launches()[0].endswith("-convert") and list(config.runs_dir.iterdir()) == []

    @pytest.mark.parametrize("sigpipe", [False, True], ids=["exit code kept", "launcher dies of SIGPIPE"])
    async def test_a_refusal_names_its_reason_and_numbers(
        self, executor: SandboxExecutor, monkeypatch: pytest.MonkeyPatch, sigpipe: bool
    ) -> None:
        from tests.unit.agents.runtime.convert_fixtures import zip_bomb

        if sigpipe:
            monkeypatch.setenv("FAKE_SANDBOX_SIGPIPE", "1")
        run = await executor.run_convert(convert_job(zip_bomb()))

        assert run.refusal == "archive_limits" and run.text is None and run.meta is None
        assert run.limit == 100 * 1024 * 1024 and run.measured is not None and run.measured > run.limit

    def test_collect_needs_both_the_text_and_a_valid_meta(self, executor: SandboxExecutor, tmp_path: Path) -> None:
        (tmp_path / "out.csv").write_text("a\n1\n", encoding="utf-8")
        attempt = Attempt(name="r", exit_code=0)
        executor._collect_convert(attempt, tmp_path)
        assert attempt.reason == "output_rejected" and attempt.csv_text is None
        (tmp_path / "meta.json").write_text('{"kind": "exe", "rows": 1, "columns": 1}', encoding="utf-8")
        attempt = Attempt(name="r", exit_code=0)
        executor._collect_convert(attempt, tmp_path)
        assert attempt.reason == "output_rejected"
        (tmp_path / "meta.json").write_text('{"kind": "xlsx", "rows": 1, "columns": 1}', encoding="utf-8")
        attempt = Attempt(name="r", exit_code=0)
        executor._collect_convert(attempt, tmp_path)
        assert attempt.reason is None and attempt.csv_text == "a\n1\n" and attempt.convert_meta is not None


class TestStderrTail:
    """`stderr_tail`: the last characters, with a row's head line in front (J2b, the Julia row's `ERROR:` line)."""

    LONG = "ERROR: LoadError: MethodError: no method matching f(::Int64)\n" + "frame\n" * 1_000 + "THE-END\n"

    def test_only_the_julia_row_keeps_a_head_line(self) -> None:
        heads = {library: command_for(language, library).stderr_head for library, language in LIBRARY_LANGUAGES.items()}
        assert heads.pop("makie") == "ERROR:"
        assert set(heads.values()) == {""}

    @pytest.mark.parametrize(
        "stderr",
        [
            LONG,
            "x" * 5_000,
            "short\nERROR: kept as it is\n",
            "w\n" * 3_000 + "ERROR: LoadError: inside the tail\n" + "frame\n" * 10,
        ],
        ids=["long", "no-line", "short", "line-in-tail"],
    )
    def test_without_a_head_or_a_lost_line_the_tail_is_the_plain_last_characters(self, stderr: str) -> None:
        plain = stderr[-MAX_STDERR_CHARS:]
        assert stderr_tail(stderr) == plain  # every row but Julia's, byte for byte as before J2b
        if not stderr.startswith("ERROR:"):
            assert stderr_tail(stderr, "ERROR:") == plain

    def test_a_lost_head_line_goes_in_front_within_the_bound(self) -> None:
        kept = stderr_tail(self.LONG, "ERROR:")

        assert len(kept) == MAX_STDERR_CHARS and kept.endswith("THE-END\n")
        head, rest = kept.split("\n", 1)
        assert head == "ERROR: LoadError: MethodError: no method matching f(::Int64)"
        assert self.LONG.endswith(rest) and len(rest) == MAX_STDERR_CHARS - len(head) - 1
        later = "warning\n" * 10 + self.LONG
        assert stderr_tail(later, "ERROR:").startswith("ERROR: LoadError: MethodError")

    def test_a_long_head_line_is_cut(self) -> None:
        stderr = "ERROR: LoadError: MethodError: " + "T" * 5_000 + "\n" + "frame\n" * 1_000
        kept = stderr_tail(stderr, "ERROR:")

        assert len(kept) == MAX_STDERR_CHARS and kept.index("\n") == STDERR_HEAD_CHARS
        assert kept.endswith("frame\n")

    async def test_run_theme_cuts_by_the_jobs_row(
        self, executor: SandboxExecutor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def launch(*args: object, **kwargs: object) -> tuple[Attempt, int]:
            return Attempt("r", exit_code=1, stderr=self.LONG), 1

        monkeypatch.setattr(executor, "_launch", launch)
        julia = RenderRequest(**{**job().model_dump(), "language": "julia", "library": "makie"})

        assert (await executor.run_theme(julia, "light")).stderr_tail.startswith("ERROR: LoadError: MethodError")
        assert (await executor.run_theme(job(), "light")).stderr_tail == self.LONG[-MAX_STDERR_CHARS:]


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
