"""The harness's exec mode (`harness.py --exec -- <command>`): the start and end lines, the limits, the exit code.

Runs the real harness with this interpreter, as the renderer's fake launcher does, with a
child that reports the limits it inherited.
"""

import json
import os
import subprocess
import sys

import pytest

from agents.anyplot.render import harness
from agents.anyplot.render.runtimes.python import HARNESS_SOURCE
from agents.renderer.commands import EXEC_FLAG
from agents.renderer.executor import HARNESS_END, HARNESS_START


def run_exec(*command: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(HARNESS_SOURCE), EXEC_FLAG, "--", *command],
        capture_output=True,
        text=True,
        timeout=60,
        env={"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "/tmp"), **(env or {})},
    )


class TestExecMode:
    def test_the_child_runs_under_the_limits_between_the_start_and_end_lines(self) -> None:
        child = "import resource, sys; print(resource.getrlimit(resource.RLIMIT_CPU)[0]); sys.exit(3)"
        done = run_exec(sys.executable, "-c", child, env={"ANYPLOT_RLIMIT_CPU_S": "42"})

        lines = done.stdout.splitlines()
        assert lines[0] == HARNESS_START and lines[1] == "42" and lines[2].startswith(HARNESS_END)
        end = json.loads(lines[2].split(" ", 1)[1])
        assert end["event"] == "end" and end["max_rss_mb"] >= 0 and end["cpu_s"] >= 0
        assert done.returncode == 3

    def test_a_signal_death_becomes_a_shell_exit_code(self) -> None:
        done = run_exec(sys.executable, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGKILL)")

        assert done.returncode == 137 and done.stdout.startswith(HARNESS_START)
        assert HARNESS_END in done.stdout  # the end line still goes out

    def test_a_missing_command_is_127_after_the_start_line(self) -> None:
        done = run_exec("/nonexistent/anyplot-runtime", "plot.x")

        assert done.returncode == 127 and done.stdout.startswith(HARNESS_START)
        assert "cannot run /nonexistent/anyplot-runtime" in done.stderr

    def test_no_command_is_a_usage_error(self) -> None:
        done = subprocess.run(
            [sys.executable, "-I", str(HARNESS_SOURCE), EXEC_FLAG],
            capture_output=True,
            text=True,
            timeout=60,
            env={"PATH": os.environ.get("PATH", "")},
        )

        assert done.returncode == 2 and "usage" in done.stderr


class TestExecModeInProcess:
    """The same contract through `harness.main` in this process, where the test run's coverage sees it. `set_limits`
    is patched out: the limits it sets would stay on this test process."""

    @pytest.fixture(autouse=True)
    def no_limits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(harness, "set_limits", lambda: None)

    def run(self, *command: str) -> int:
        return int(harness.main(["harness.py", EXEC_FLAG, "--", *command]))

    def test_the_lines_frame_the_child_and_its_exit_code_is_the_harness_s(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = self.run(sys.executable, "-c", "import sys; sys.exit(3)")

        lines = capsys.readouterr().out.splitlines()
        assert code == 3 and lines[0] == HARNESS_START and lines[-1].startswith(HARNESS_END)
        end = json.loads(lines[-1].split(" ", 1)[1])
        assert end["event"] == "end" and end["max_rss_mb"] >= 0 and end["cpu_s"] >= 0

    def test_a_signal_death_becomes_a_shell_exit_code(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = self.run(sys.executable, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGKILL)")

        out = capsys.readouterr().out
        assert code == 137 and out.startswith(HARNESS_START) and HARNESS_END in out

    def test_a_missing_command_is_127_after_the_start_line(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = self.run("/nonexistent/anyplot-runtime", "plot.x")

        captured = capsys.readouterr()
        assert code == 127 and captured.out.startswith(HARNESS_START) and HARNESS_END in captured.out
        assert "cannot run /nonexistent/anyplot-runtime" in captured.err

    @pytest.mark.parametrize("argv", [[EXEC_FLAG], [EXEC_FLAG, "--"]], ids=["no separator", "separator only"])
    def test_no_command_is_a_usage_error_after_the_start_line(
        self, argv: list[str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = harness.main(["harness.py", *argv])

        captured = capsys.readouterr()
        assert code == 2 and captured.out.splitlines() == [HARNESS_START] and "usage" in captured.err
