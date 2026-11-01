"""The harness's exec mode (`harness.py --exec -- <command>`): the start and end lines, the limits, the exit code.

Runs the real harness with this interpreter, as the renderer's fake launcher does, with a
child that reports the limits it inherited.
"""

import json
import os
import signal
import subprocess
import sys
from pathlib import Path

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


WRITES_TEXTS = (
    "import json, sys; open('texts-dark.json', 'w').write(json.dumps({'entries': "
    "[['x tick label', 'Bern'], ['title', 'Umsatz'], ['x tick label', 'Zug'], [1, 'tampered']]})); "
    "sys.exit(int(sys.argv[1]))"
)
"""A child that leaves drawn texts as R's and Julia's text probes do (`text_probe.R`, `text_probe.jl`)."""


class TestExecModeTextProbe:
    """After a run that counts, the harness turns the drawn texts an R or Julia probe left into the probe, under the
    probe's caps; anything else is best-effort and never changes the exit code (2026-11-01)."""

    @pytest.fixture(autouse=True)
    def in_a_run_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(harness, "set_limits", lambda: None)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv(harness.THEME_ENV, "dark")

    def probe(self) -> dict[str, object]:
        return json.loads(Path("probe-dark.json").read_text(encoding="utf-8"))

    def test_the_drawn_texts_become_the_probe_after_exit_code_0(self) -> None:
        code = harness.main(["harness.py", EXEC_FLAG, "--", sys.executable, "-c", WRITES_TEXTS, "0"])

        assert code == 0
        assert self.probe() == {
            "labels": [
                {"kind": "title", "text": "Umsatz"},
                {"kind": "x tick label", "text": "Bern"},
                {"kind": "x tick label", "text": "Zug"},
            ],
            "labels_truncated": True,  # an entry that is no pair of strings was left out
        }

    def test_a_failed_run_leaves_no_probe(self) -> None:
        code = harness.main(["harness.py", EXEC_FLAG, "--", sys.executable, "-c", WRITES_TEXTS, "1"])

        assert code == 1 and not Path("probe-dark.json").exists()

    @pytest.mark.parametrize(
        ("content", "error"),
        [
            ('{"error": "Error"}', "Error"),
            ("{not json", "JSONDecodeError"),
            ("[1, 2]", "ValueError"),
            ('{"entries": "Bern"}', "ValueError"),
        ],
        ids=["the probe's own error", "broken", "no object", "no entries"],
    )
    def test_a_probe_that_failed_or_a_broken_file_is_an_error_probe(self, content: str, error: str) -> None:
        Path("texts-dark.json").write_text(content, encoding="utf-8")

        harness.collect_text_probe("dark")

        assert self.probe() == {"error": error}

    def test_a_link_a_pipe_or_an_oversized_file_is_never_read_as_texts(self, tmp_path: Path) -> None:
        (tmp_path / "elsewhere.json").write_text('{"entries": [["title", "Umsatz"]]}', encoding="utf-8")
        Path("texts-dark.json").symlink_to(tmp_path / "elsewhere.json")
        harness.collect_text_probe("dark")
        assert self.probe() == {"error": "OSError"}  # O_NOFOLLOW refuses the link (ELOOP)

        Path("texts-dark.json").unlink()
        os.mkfifo("texts-dark.json")
        harness.collect_text_probe("dark")  # opened without blocking, refused as no regular file
        assert self.probe() == {"error": "ValueError"}

        Path("texts-dark.json").unlink()
        Path("texts-dark.json").write_bytes(b" " * (harness.TEXT_ENTRIES_MAX_BYTES + 1))
        harness.collect_text_probe("dark")
        assert self.probe() == {"error": "ValueError"}

    def test_no_file_no_probe(self) -> None:
        harness.collect_text_probe("dark")

        assert not Path("probe-dark.json").exists()

    def test_the_probe_is_never_written_through_a_link(self, tmp_path: Path) -> None:
        """The child ran first and could leave a link at the probe's name: the write does not follow it."""
        target = tmp_path / "elsewhere.txt"
        target.write_text("untouched", encoding="utf-8")
        Path("probe-dark.json").symlink_to(target)
        Path("texts-dark.json").write_text('{"entries": [["title", "Umsatz"]]}', encoding="utf-8")

        harness.collect_text_probe("dark")

        assert target.read_text(encoding="utf-8") == "untouched" and Path("probe-dark.json").is_symlink()


def end_line(stdout: str) -> dict[str, object]:
    line = next(line for line in stdout.splitlines() if line.startswith(HARNESS_END))
    return json.loads(line.split(" ", 1)[1])


# `/bin/sh` starts a program the way R's `system()` and `popen` do; the filter kills that start (128 + SIGSYS).
STARTS_A_PROGRAM = "/bin/true; echo status:$?"
KILLED = f"status:{128 + signal.SIGSYS}"


class TestExecModeFilter:
    """`ANYPLOT_DENY_EXEC=required`: the child alone gets the exec filter's preload library, and the run counts only
    when the library reported `on` (step 2b of agentic/specs/261024-agent-all-libraries.md)."""

    def test_the_child_runs_under_the_filter_and_the_end_line_says_on(self, execdeny_library: Path) -> None:
        done = run_exec(
            "/bin/sh",
            "-c",
            STARTS_A_PROGRAM,
            env={harness.EXEC_DENY_ENV: "required", harness.EXEC_DENY_PRELOAD_ENV: str(execdeny_library)},
        )

        assert done.returncode == 0, done.stderr
        assert KILLED in done.stdout
        assert end_line(done.stdout)["exec_deny"] == "on"

    def test_a_preload_that_does_not_load_stops_before_the_code_runs(self, tmp_path: Path) -> None:
        """ld.so only warns about a missing preload object and would run the program unfiltered: the preflight
        (the program alone, ended by the library before its main) proves the filter first, so the code never runs
        (the Copilot review of #12428)."""
        done = run_exec(
            "/bin/sh",
            "-c",
            STARTS_A_PROGRAM,
            env={harness.EXEC_DENY_ENV: "required", harness.EXEC_DENY_PRELOAD_ENV: str(tmp_path / "missing.so")},
        )

        assert done.returncode == harness.EXEC_DENY_EXIT
        assert "status:" not in done.stdout  # the code never ran
        assert end_line(done.stdout)["exec_deny"] == "unavailable"
        assert "the exec filter does not take in /bin/sh (unavailable); the code did not run" in done.stderr

    def test_without_the_variable_the_child_runs_unfiltered_and_the_end_line_says_off(self) -> None:
        done = run_exec("/bin/sh", "-c", STARTS_A_PROGRAM)

        assert done.returncode == 0 and "status:0" in done.stdout
        assert end_line(done.stdout)["exec_deny"] == "off"


class TestExecModeFilterInProcess:
    """The filter's paths through `harness.main` in this process, where the coverage sees them."""

    @pytest.fixture(autouse=True)
    def no_limits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(harness, "set_limits", lambda: None)

    def test_on_counts_and_passes_the_child_s_code(
        self, execdeny_library: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setenv(harness.EXEC_DENY_ENV, "required")
        monkeypatch.setenv(harness.EXEC_DENY_PRELOAD_ENV, str(execdeny_library))

        code = harness.main(["harness.py", EXEC_FLAG, "--", "/bin/sh", "-c", f"{STARTS_A_PROGRAM}; exit 4"])

        out = capfd.readouterr().out
        assert code == 4 and KILLED in out and end_line(out)["exec_deny"] == "on"
        assert harness.EXEC_DENY_FD_ENV not in os.environ and "LD_PRELOAD" not in os.environ

    def test_a_preflight_without_the_filter_stops_before_the_code(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setenv(harness.EXEC_DENY_ENV, "required")
        monkeypatch.setenv(harness.EXEC_DENY_PRELOAD_ENV, str(tmp_path / "missing.so"))

        code = harness.main(["harness.py", EXEC_FLAG, "--", "/bin/sh", "-c", "echo ran"])

        captured = capfd.readouterr()
        assert code == harness.EXEC_DENY_EXIT and end_line(captured.out)["exec_deny"] == "unavailable"
        assert "ran" not in captured.out and "does not take in /bin/sh" in captured.err

    def test_a_preflight_that_outlives_its_constructor_is_killed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
    ) -> None:
        """Only a program that ignored the preload runs past its constructor; the preflight does not wait for it."""
        program = tmp_path / "runtime"
        program.write_text("#!/bin/sh\nsleep 30\n", encoding="utf-8")
        program.chmod(0o755)
        monkeypatch.setenv(harness.EXEC_DENY_ENV, "required")
        monkeypatch.setenv(harness.EXEC_DENY_PRELOAD_ENV, str(tmp_path / "missing.so"))
        monkeypatch.setattr(harness, "EXEC_DENY_PREFLIGHT_TIMEOUT_S", 0.5)

        code = harness.main(["harness.py", EXEC_FLAG, "--", str(program), "plot.x"])

        captured = capfd.readouterr()
        assert code == harness.EXEC_DENY_EXIT and end_line(captured.out)["exec_deny"] == "unavailable"

    def test_a_run_whose_filter_did_not_report_on_is_refused_after_a_passing_preflight(
        self, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
    ) -> None:
        """The second check: the run's own report counts too, whatever the preflight said."""
        monkeypatch.setenv(harness.EXEC_DENY_ENV, "required")
        reports = iter([(0, "on"), (0, "unavailable")])
        monkeypatch.setattr(harness, "_run_child", lambda command, **_: next(reports))

        code = harness.main(["harness.py", EXEC_FLAG, "--", "/bin/sh", "-c", "exit 0"])

        captured = capfd.readouterr()
        assert code == harness.EXEC_DENY_EXIT and end_line(captured.out)["exec_deny"] == "unavailable"
        assert "the exec filter is not in place (unavailable); the run does not count" in captured.err

    def test_a_command_that_never_started_keeps_127_under_the_filter(
        self, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setenv(harness.EXEC_DENY_ENV, "required")

        code = harness.main(["harness.py", EXEC_FLAG, "--", "/nonexistent/anyplot-runtime", "plot.x"])

        captured = capfd.readouterr()
        assert code == 127 and "cannot run /nonexistent/anyplot-runtime" in captured.err

    @pytest.mark.parametrize(
        ("written", "state"),
        [(b"on", "on"), (b"unsupported", "unsupported"), (b"unavailable", "unavailable"), (b"", "unavailable")],
    )
    def test_the_pipe_s_content_is_the_state(self, written: bytes, state: str) -> None:
        read_end, write_end = os.pipe()
        os.set_blocking(read_end, False)
        os.write(write_end, written)
        os.close(write_end)
        assert harness._exec_deny_report(read_end) == state

    def test_a_pipe_still_open_and_empty_is_unavailable(self) -> None:
        """A grandchild of an unfiltered child could keep the write end: the read must not block."""
        read_end, write_end = os.pipe()
        os.set_blocking(read_end, False)
        try:
            assert harness._exec_deny_report(read_end) == "unavailable"
        finally:
            os.close(write_end)
