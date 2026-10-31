"""The harness's figure mode (`harness.py --figure <package> plot.py -- <screenshot command>`, PB-1 of step 4 in
agentic/specs/261024-agent-all-libraries.md): the plot step forked before anything is armed, the plot armed in the
child, the parent never armed, the figure's checks, the final error line of either step, and the renderer's
two-step rows.

The harness runs in a subprocess of its own (an audit hook and a seccomp filter cannot be removed), loaded by a
driver that stands in for the package's lookup, so these cases need neither plotly nor bokeh; the screenshot command
is a Python script that reports what it ran under. `tests/unit/automation/test_js_render_figure.py` draws real
figures through the JavaScript harness.
"""

import contextlib
import json
import os
import platform
import re
import resource
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from agents.anyplot.render import harness
from agents.anyplot.render.runtimes.python import HARNESS_SOURCE
from agents.renderer import commands
from agents.renderer import executor as executor_module
from agents.renderer.commands import (
    FIGURE_FLAG,
    FIGURE_LIBRARIES,
    JS_ENV,
    JS_HARNESS,
    NODE_BINARY,
    RuntimeCommand,
    command_for,
)
from agents.renderer.executor import SANDBOX_PATH, ExecutorConfig, SandboxExecutor, build_argv, sandbox_env
from agents.renderer.wire import RenderRequest

from .conftest import FakeLauncher


KERNEL = pytest.mark.skipif(
    not sys.platform.startswith("linux") or platform.machine() not in harness.EXEC_DENY_MACHINES,
    reason="the filter is installed on Linux on x86_64 and aarch64 only",
)
ERROR_LINE = re.compile(r"^render: error: (plot|figure|crash|harness) ([A-Za-z_][A-Za-z0-9_]*) (\S+:\d+|-): (.*)$")
"""The final error line's grammar for the plot step (`harness.figure_error_line`), `render.mjs`'s own."""
DRIVER = (
    "import importlib.util, sys\n"
    "spec = importlib.util.spec_from_file_location('harness', sys.argv[1])\n"
    "harness = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(harness)\n"
    "package = sys.argv[2]\n"
    "harness.find_figure_package = lambda name: package\n"
    "{patch}"
    "sys.exit(harness.main(['harness.py', *sys.argv[3:]]))\n"
)
"""The harness's `main` with the package's lookup answering a stand-in directory (the image has plotly and bokeh, a
test environment need not) and a case's `{patch}`."""
STATUS = (
    "def status(pid='self'):\n"
    "    with open(f'/proc/{pid}/status') as handle:\n"
    "        pairs = (line.partition(':') for line in handle)\n"
    "        return {key: value.strip() for key, _, value in pairs if key in ('Seccomp_filters', 'NoNewPrivs')}\n"
)
"""A process's seccomp filters and its no-new-privileges bit. The count, not the mode: a test may already run under a
filter of its own sandbox, which every process below it inherits."""
OBSERVING_PLOT = (
    "import json, os, resource\n" + STATUS + "seen = {'pid': os.getpid(), 'ppid': os.getppid(), 'status': status(),\n"
    "        'as': resource.getrlimit(resource.RLIMIT_AS)[0], 'nproc': resource.getrlimit(resource.RLIMIT_NPROC)[0],\n"
    "        'cpu': resource.getrlimit(resource.RLIMIT_CPU)[0]}\n"
    "with open('plot-light.json', 'w') as handle:\n"
    "    json.dump({'data': [], 'layout': {}, 'seen': seen}, handle)\n"
)
"""A plot that writes what it ran under into its figure, the one file it may write."""
SCREENSHOT = (
    "import json, os, resource, subprocess, sys\n" + STATUS + "figure = sys.argv[-1].split('=', 1)[1]\n"
    "report = {'argv': sys.argv[1:], 'harness': os.getppid(), 'harness_status': status(os.getppid()),\n"
    "          'status': status(), 'as': resource.getrlimit(resource.RLIMIT_AS)[0],\n"
    "          'nproc': resource.getrlimit(resource.RLIMIT_NPROC)[0], 'cpu': resource.getrlimit(resource.RLIMIT_CPU)[0],\n"
    "          'env': {key: value for key, value in os.environ.items() if key.startswith('ANYPLOT_')},\n"
    "          'figure': json.load(open(figure)), 'starts': subprocess.run(['/bin/true']).returncode}\n"
    "open('shot.json', 'w').write(json.dumps(report))\n"
    "open('plot-light.png', 'wb').write(b'\\x89PNG\\r\\n\\x1a\\n')\n"
    "code = int(os.environ.get('SHOT_EXIT', '0'))\n"
    "if code:\n"
    "    print('render: error: page TypeError -: the screenshot step failed', file=sys.stderr)\n"
    "sys.exit(code)\n"
)
"""The screenshot step's stand-in: reports its own and its parent's state, then writes a PNG's signature."""


def run_figure(
    tmp_path: Path,
    plot: str,
    *,
    env: dict[str, str] | None = None,
    package: str = "plotly",
    command: list[str] | None = None,
    patch: str = "",
    timeout: float = 120,
) -> subprocess.CompletedProcess[str]:
    """The harness in figure mode on `plot` in `tmp_path`, the stand-in screenshot (or `command`) after it, with the
    driver's `patch` applied before `main`."""
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    (work / "plot.py").write_text(plot, encoding="utf-8")
    (tmp_path / "shot.py").write_text(SCREENSHOT, encoding="utf-8")
    stand_in = tmp_path / "site-packages" / package
    stand_in.mkdir(parents=True, exist_ok=True)
    command = command or [sys.executable, "-I", str(tmp_path / "shot.py")]
    argv = [FIGURE_FLAG, package, "plot.py", "--", *command]
    driver = DRIVER.replace("{patch}", patch)
    return subprocess.run(
        [sys.executable, *harness.INTERPRETER_FLAGS, "-c", driver, str(HARNESS_SOURCE), str(stand_in), *argv],
        cwd=work,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path),
            "ANYPLOT_THEME": "light",
            "ANYPLOT_RLIMIT_CPU_S": "120",
            **(env or {}),
        },
    )


def end_line(stdout: str) -> dict[str, object]:
    lines = [line for line in stdout.splitlines() if line.startswith(f"{harness.MARKER} ")]
    report = json.loads(lines[-1].split(" ", 1)[1])
    assert report["event"] == "end"
    return report


def last_line(stderr: str) -> str:
    lines = stderr.strip().splitlines()
    return lines[-1] if lines else ""


class TestTwoSteps:
    @KERNEL
    def test_the_plot_runs_armed_in_a_fork_and_the_screenshot_after_it_unarmed(self, tmp_path: Path) -> None:
        """Fork before arm: both steps are children of one harness process, which no filter ever reached; the plot
        step runs under the filter and the plot's limits, the screenshot step under neither and without the plot's
        variables, and starts a program."""
        address_space = 4096
        done = run_figure(
            tmp_path, OBSERVING_PLOT, env={"ANYPLOT_DENY_EXEC": "required", "ANYPLOT_RLIMIT_AS_MB": str(address_space)}
        )

        assert done.returncode == 0, done.stderr
        shot = json.loads((tmp_path / "work" / "shot.json").read_text(encoding="utf-8"))
        plot = shot["figure"]["seen"]
        assert plot["ppid"] == shot["harness"]  # a child of the harness, forked, not a program it started anew
        inherited = int(shot["harness_status"]["Seccomp_filters"])  # the test's own sandbox may hold one
        # The kernel filter in the plot step alone; the harness never armed, and the screenshot starts a program.
        assert plot["status"] == {"Seccomp_filters": str(inherited + 1), "NoNewPrivs": "1"}
        assert shot["harness_status"]["NoNewPrivs"] == "0"
        assert shot["status"] == shot["harness_status"] and shot["starts"] == 0
        assert plot["as"] == address_space * 1024 * 1024 and shot["as"] == resource.RLIM_INFINITY
        assert plot["cpu"] == shot["cpu"] == 120  # the run's limits reach both steps
        assert shot["argv"] == ["--figure=plot-light.json"]
        assert shot["env"]["ANYPLOT_FIGURE_PACKAGE"].endswith("site-packages/plotly")
        assert not set(harness.FIGURE_PLOT_ONLY_ENV) & set(shot["env"])
        end = end_line(done.stdout)
        assert end["exec_deny"] == "on" and set(end["steps"]) == {"plot", "screenshot"}
        assert end["max_rss_mb"] >= end["steps"]["plot"]["max_rss_mb"]
        assert end["cpu_s"] >= end["steps"]["plot"]["cpu_s"] + end["steps"]["screenshot"]["cpu_s"] - 0.01

    def test_the_plots_process_limit_is_its_own(self, tmp_path: Path) -> None:
        """`RLIMIT_NPROC` binds the plot step; the screenshot step keeps the harness's own, as the JavaScript row."""
        soft, hard = resource.getrlimit(resource.RLIMIT_NPROC)
        wanted = hard if hard != resource.RLIM_INFINITY else 1_000_000
        done = run_figure(tmp_path, OBSERVING_PLOT, env={"ANYPLOT_RLIMIT_NPROC": str(wanted)})

        assert done.returncode == 0, done.stderr
        shot = json.loads((tmp_path / "work" / "shot.json").read_text(encoding="utf-8"))
        assert shot["figure"]["seen"]["nproc"] == wanted and shot["nproc"] == soft

    def test_without_the_requirement_the_end_line_reports_the_state(self, tmp_path: Path) -> None:
        done = run_figure(tmp_path, OBSERVING_PLOT)

        assert done.returncode == 0, done.stderr
        assert end_line(done.stdout)["exec_deny"] in ("on", "unavailable", "unsupported")

    def test_a_stale_figure_never_reaches_the_screenshot(self, tmp_path: Path) -> None:
        (tmp_path / "work").mkdir()
        (tmp_path / "work" / "plot-light.json").write_text('{"data": [], "layout": {}}', encoding="utf-8")
        done = run_figure(tmp_path, "x = 1\n")

        assert done.returncode == 1
        assert last_line(done.stderr) == "render: error: figure NoFigure -: the plot wrote no plot-light.json"
        assert not (tmp_path / "work" / "shot.json").exists()


class TestThePlotStep:
    @pytest.mark.parametrize(
        ("body", "line", "event"),
        [
            ("import subprocess\nsubprocess.run(['/bin/true'])\n", 2, "subprocess.Popen"),
            ("import os\nos.posix_spawn('/bin/true', ['true'], {})\n", 2, "os.posix_spawn"),
            ("import os\nos.fork()\n", 2, "os.fork"),
            ("import os\nos.execv('/bin/true', ['true'])\n", 2, "os.exec"),
            ("import socket\nsocket.socketpair()\n", 2, "socket"),
            ("open('plot-light.png', 'wb').write(b'x')\n", 1, "open"),
        ],
        ids=["subprocess", "posix_spawn", "fork", "execv", "a socket pair", "the PNG itself"],
    )
    def test_a_plot_that_starts_a_program_or_writes_the_png_fails_before_the_screenshot(
        self, tmp_path: Path, body: str, line: int, event: str
    ) -> None:
        """No browser from plot code: kaleido's choreographer opens a socket pair, Selenium a socket to chromedriver
        and both start a program; every such start, and the PNG the screenshot step alone writes, are refused."""
        done = run_figure(tmp_path, body)

        assert done.returncode == 1
        match = ERROR_LINE.match(last_line(done.stderr))
        assert match is not None, done.stderr
        assert match.group(1) == "plot" and match.group(3) == f"plot.py:{line}"
        assert match.group(2) == "PermissionError" and event in match.group(4)
        assert not (tmp_path / "work" / "shot.json").exists() and not (tmp_path / "work" / "plot-light.png").exists()
        assert set(end_line(done.stdout)["steps"]) == {"plot"}

    def test_nothing_of_the_plot_runs_after_it(self, tmp_path: Path) -> None:
        """The child ends with `os._exit`: an `atexit` callback and a thread the plot left, each of which would
        overwrite the figure (the one file the guard lets it write), never run on."""
        plot = (
            "import atexit, threading, time\n"
            "atexit.register(lambda: open('plot-light.json', 'w').write('late-atexit'))\n"
            "threading.Thread(target=lambda: (time.sleep(1), open('plot-light.json', 'w').write('late-thread'))).start()\n"
            + OBSERVING_PLOT
        )
        done = run_figure(tmp_path, plot)
        time.sleep(1.5)

        assert done.returncode == 0, done.stderr
        assert "seen" in json.loads((tmp_path / "work" / "plot-light.json").read_text(encoding="utf-8"))

    @KERNEL
    def test_the_kernel_refuses_a_start_the_audit_hook_misses(self, tmp_path: Path) -> None:
        """The plot step's second layer: with the hook made blind to `os.exec` (as it is to native code), the kernel
        filter still refuses the start, so nothing after the arming starts a program in the plot step."""
        blind = "harness.PLOT_BLOCKED_PREFIXES = tuple(p for p in harness.PLOT_BLOCKED_PREFIXES if p != 'os.exec')\n"
        plot = (
            "import json, os\n"
            "try:\n"
            "    os.execv('/bin/true', ['true'])\n"
            "except OSError as exc:\n"
            "    refused = type(exc).__name__\n"
            "json.dump({'data': [], 'refused': refused}, open('plot-light.json', 'w'))\n"
        )
        done = run_figure(tmp_path, plot, env={"ANYPLOT_DENY_EXEC": "required"}, patch=blind)

        assert done.returncode == 0, done.stderr
        shot = json.loads((tmp_path / "work" / "shot.json").read_text(encoding="utf-8"))
        assert shot["figure"]["refused"] == "PermissionError" and shot["starts"] == 0

    @pytest.mark.parametrize(
        ("plot", "code", "line"),
        [
            ("x = 1\nraise ValueError('boom')\n", 1, "render: error: plot ValueError plot.py:2: boom"),
            ("x = (\n", 1, None),
            ("import sys\nsys.exit(4)\n", 4, "render: error: plot SystemExit plot.py:2: 4"),
            ("x = 1\n", 1, "render: error: figure NoFigure -: the plot wrote no plot-light.json"),
            ("import os\nos._exit(0)\n", 1, "render: error: figure NoFigure -: the plot wrote no plot-light.json"),
            (
                "open('plot-light.json', 'w').close()\n",
                1,
                "render: error: figure FigureError -: plot-light.json is empty",
            ),
        ],
        ids=[
            "an exception",
            "a syntax error",
            "sys.exit",
            "no figure",
            "os._exit before the figure",
            "an empty figure",
        ],
    )
    def test_a_failed_plot_step_ends_stderr_with_its_line_and_its_code(
        self, tmp_path: Path, plot: str, code: int, line: str | None
    ) -> None:
        done = run_figure(tmp_path, plot)

        assert done.returncode == code
        last = last_line(done.stderr)
        assert ERROR_LINE.match(last), done.stderr
        if line is not None:
            assert last == line
        else:
            assert last.startswith("render: error: plot SyntaxError plot.py:1: ")
        assert not (tmp_path / "work" / "shot.json").exists()

    def test_a_plot_that_succeeds_with_sys_exit_0_goes_on(self, tmp_path: Path) -> None:
        done = run_figure(tmp_path, OBSERVING_PLOT + "import sys\nsys.exit(0)\n")
        assert done.returncode == 0, done.stderr
        assert (tmp_path / "work" / "shot.json").exists()

    def test_the_traceback_comes_before_the_final_line(self, tmp_path: Path) -> None:
        done = run_figure(tmp_path, "def f():\n    raise KeyError('k')\n\nf()\n")

        lines = done.stderr.strip().splitlines()
        assert "Traceback (most recent call last):" in lines and 'File "plot.py", line 4, in <module>' in done.stderr
        assert lines[-1] == "render: error: plot KeyError plot.py:2: 'k'"

    def test_the_error_record_runs_no_plot_code_paused(self, tmp_path: Path) -> None:
        """The record's traceback walk pauses the guard; a `__traceback__` property of the plot's exception class is
        not called there, and where the interpreter's traceback calls it, the armed guard refuses its write."""
        plot = (
            "class Escape(Exception):\n"
            "    @property\n"
            "    def __traceback__(self):\n"
            "        try:\n"
            "            open('escaped', 'w').write('x')\n"
            "        except OSError:\n"
            "            pass\n"
            "        return None\n"
            "\n"
            "raise Escape('boom')\n"
        )
        done = run_figure(tmp_path, plot)

        assert done.returncode == 1
        assert last_line(done.stderr) == "render: error: plot Escape plot.py:10: boom"
        assert not (tmp_path / "work" / "escaped").exists()

    def test_a_plot_step_killed_by_a_signal_is_a_crash(self, tmp_path: Path) -> None:
        """`RLIMIT_CPU` ends a busy plot: soft and hard limit alike, the kernel kills it with SIGKILL."""
        done = run_figure(tmp_path, "while True:\n    pass\n", env={"ANYPLOT_RLIMIT_CPU_S": "1"}, timeout=60)

        assert done.returncode == 128 + 9
        assert last_line(done.stderr) == "render: error: crash PlotCrashed -: the plot step died of SIGKILL"
        assert set(end_line(done.stdout)["steps"]) == {"plot"}

    def test_the_figure_cap_refuses_one_byte_more(self, tmp_path: Path) -> None:
        plot = f"open('plot-light.json', 'w').write(' ' * {harness.FIGURE_MAX_BYTES} + '{{}}')\n"
        done = run_figure(tmp_path, plot, env={"ANYPLOT_RLIMIT_FSIZE_MB": "64"})

        assert done.returncode == 1
        size = harness.FIGURE_MAX_BYTES + 2
        assert last_line(done.stderr) == (
            f"render: error: figure FigureTooLarge -: plot-light.json is {size} bytes, "
            f"more than the {harness.FIGURE_MAX_BYTES}-byte limit"
        )
        assert not (tmp_path / "work" / "shot.json").exists()

    def test_a_required_filter_that_is_not_in_place_stops_the_plot_step(self, tmp_path: Path) -> None:
        done = run_figure(
            tmp_path,
            "open('plot-light.json', 'w').write('ran')\n" + OBSERVING_PLOT,
            env={"ANYPLOT_DENY_EXEC": "required"},
            patch="harness.install_exec_deny = lambda: 'unavailable'\n",
        )

        assert done.returncode == harness.EXEC_DENY_EXIT
        assert last_line(done.stderr) == (
            "render: error: harness ExecDenyUnavailable -: the sandbox could not refuse process starts (unavailable)"
        )
        assert not (tmp_path / "work" / "plot-light.json").exists() and not (tmp_path / "work" / "shot.json").exists()
        assert end_line(done.stdout)["exec_deny"] == "unavailable"

    @pytest.mark.parametrize(
        ("plot", "env", "patch", "line", "state"),
        [
            pytest.param(
                "import sys\nsys.exit(3)\n",
                {"ANYPLOT_DENY_EXEC": "required"},
                "",
                "render: error: plot SystemExit plot.py:2: 3",
                "on",
                marks=KERNEL,
                id="sys.exit(3) under the filter",
            ),
            pytest.param(
                "import sys\nsys.exit(3)\n",
                {},
                "harness.install_exec_deny = lambda: 'unavailable'\n",
                "render: error: plot SystemExit plot.py:2: 3",
                "unavailable",
                id="sys.exit(3) without a filter it did not require",
            ),
            pytest.param(
                "import os\nos._exit(3)\n",
                {},
                "harness.install_exec_deny = lambda: 'unavailable'\n",
                "render: error: plot Error -: the plot step ended with 3",
                "unavailable",
                id="os._exit(3), no record",
            ),
        ],
    )
    def test_a_plot_that_ends_with_the_filters_exit_code_is_a_plot_error(
        self, tmp_path: Path, plot: str, env: dict[str, str], patch: str, line: str, state: str
    ) -> None:
        """`EXEC_DENY_EXIT` is the harness's refusal only when the report's first line says `refused`: a plot that ran
        armed and chose the same code is the plot's failure, whatever the filter's state."""
        done = run_figure(tmp_path, plot, env=env, patch=patch)

        assert done.returncode == harness.EXEC_DENY_EXIT
        assert last_line(done.stderr) == line
        assert end_line(done.stdout)["exec_deny"] == state
        assert not (tmp_path / "work" / "shot.json").exists()


class TestTheScreenshotStep:
    def test_its_failure_is_the_runs_and_its_line_stays_last(self, tmp_path: Path) -> None:
        done = run_figure(tmp_path, OBSERVING_PLOT, env={"SHOT_EXIT": "5"})

        assert done.returncode == 5
        assert last_line(done.stderr) == "render: error: page TypeError -: the screenshot step failed"
        assert set(end_line(done.stdout)["steps"]) == {"plot", "screenshot"}

    def test_a_command_that_cannot_start_is_127(self, tmp_path: Path) -> None:
        missing = str(tmp_path / "no-such-node")
        done = run_figure(tmp_path, OBSERVING_PLOT, command=[missing, "render.mjs"])

        assert done.returncode == 127
        assert (
            last_line(done.stderr) == f"render: error: harness SpawnError -: cannot run {missing} (FileNotFoundError)"
        )


class TestHarnessUsage:
    @pytest.mark.parametrize(
        "argv",
        [[FIGURE_FLAG], [FIGURE_FLAG, "plotly", "plot.py"], [FIGURE_FLAG, "matplotlib", "plot.py", "--", "x"]],
        ids=["nothing", "no command", "another package"],
    )
    def test_a_bad_call_is_a_usage_error_after_the_start_line(
        self, argv: list[str], capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(harness, "set_run_limits", lambda: None)
        assert harness.main(["harness.py", *argv]) == 2
        captured = capsys.readouterr()
        assert captured.out.splitlines()[0] == executor_module.HARNESS_START
        assert last_line(captured.err).startswith("render: error: harness UsageError -: ")

    def test_a_missing_package_stops_before_the_plot(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(harness, "set_run_limits", lambda: None)
        monkeypatch.setattr(harness, "find_figure_package", lambda name: None)
        monkeypatch.setattr(harness, "plot_step", lambda *args: pytest.fail("the plot step started"))
        monkeypatch.chdir(tmp_path)
        assert harness.main(["harness.py", FIGURE_FLAG, "bokeh", "plot.py", "--", "x"]) == 2
        assert last_line(capsys.readouterr().err) == (
            "render: error: harness PackageMissing -: bokeh is not installed where the harness runs"
        )


class TestHelpers:
    def test_the_package_is_found_without_importing_it(self) -> None:
        found = harness.find_figure_package("json")
        assert found is not None and Path(found, "__init__.py").is_file()
        assert harness.find_figure_package("anyplot_no_such_package") is None
        assert harness.find_figure_package("os") is None  # a module, not a package

    def test_check_figure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert harness.check_figure("plot-light.json") == ("NoFigure", None, "the plot wrote no plot-light.json")
        Path("plot-light.json").write_text("{}", encoding="utf-8")
        assert harness.check_figure("plot-light.json") is None
        Path("real.json").write_text("{}", encoding="utf-8")
        Path("plot-dark.json").symlink_to("real.json")
        name, _, message = harness.check_figure("plot-dark.json")
        assert name == "FigureError" and "could not be opened as a regular file" in message
        Path("dir.json").mkdir()
        assert harness.check_figure("dir.json") == ("FigureError", None, "dir.json is not a regular file")
        with open("at-cap.json", "wb") as handle:
            handle.truncate(harness.FIGURE_MAX_BYTES)
        assert harness.check_figure("at-cap.json") is None

    @pytest.mark.parametrize(
        ("written", "state", "refused", "record"),
        [
            (b"", "off", False, None),
            (b"armed on\n", "on", False, None),
            (b"armed unavailable\n", "unavailable", False, None),
            (b"refused unavailable\n", "unavailable", True, None),
            (b"armed forged\n", "unavailable", False, None),
            (b"exec_deny on\n", "off", False, None),
            (b"armed on\nrefused unavailable\n", "on", False, None),
            (b'error ["SyntaxError", 3, "bad"]\n', "off", False, ("SyntaxError", 3, "bad")),
            (b'armed on\nerror ["ValueError", 0, "x"]\n', "on", False, ("ValueError", None, "x")),
            (b'armed on\nerror ["not a class", 2, "x"]\nerror [1, 2]\n', "on", False, None),
            (b'armed on\nerror ["A", 2, "x"]\nnoise\n', "on", False, ("A", 2, "x")),
            (b'armed on\nerror ["A", true, "x"]\nerror {"a": 1}\n', "on", False, ("A", None, "x")),
        ],
        ids=[
            "nothing",
            "on",
            "unavailable and not required",
            "refused",
            "a forged state",
            "an unknown first line",
            "a refusal after the arming",
            "before arming",
            "line 0",
            "malformed",
            "noise after",
            "a flag for a line",
        ],
    )
    def test_the_report_pipe(self, written: bytes, state: str, refused: bool, record: tuple | None) -> None:
        """The first line is the harness's own: a later `refused` line is the plot's, and changes nothing."""
        read_end, write_end = os.pipe()
        os.write(write_end, written)
        os.close(write_end)
        os.set_blocking(read_end, False)
        report = harness._read_figure_report(read_end)
        assert (report.state, report.refused, report.record) == (state, refused, record)

    def test_an_empty_open_pipe_reads_as_nothing(self) -> None:
        """A write end a stray process of the plot kept open: the reader takes what is there and does not wait."""
        read_end, write_end = os.pipe()
        os.set_blocking(read_end, False)
        try:
            report = harness._read_figure_report(read_end)
        finally:
            os.close(write_end)
        assert (report.state, report.refused, report.record) == ("off", False, None)

    def test_the_final_line_is_one_line_within_its_cap(self, capsys: pytest.CaptureFixture[str]) -> None:
        harness.figure_error_line("plot", "ValueError", "plot.py:3", "a\nb\t c" + "x" * 500)
        line = capsys.readouterr().err.rstrip("\n")
        assert "\n" not in line and ERROR_LINE.match(line)
        assert line.startswith("render: error: plot ValueError plot.py:3: a b c")
        assert len(line.split(": ", 3)[3]) == harness.FIGURE_ERROR_CHARS and line.endswith("…")

    def test_the_constants_the_javascript_harness_shares(self) -> None:
        render = (Path(__file__).resolve().parents[4] / "automation" / "js-render" / "render.mjs").read_text()
        cap = re.search(r"^const FIGURE_MAX_BYTES = (\d+) \* (\d+) \* (\d+);$", render, re.MULTILINE)
        assert cap is not None and int(cap[1]) * int(cap[2]) * int(cap[3]) == harness.FIGURE_MAX_BYTES
        assert re.search(r"^const ERROR_MESSAGE_CHARS = (\d+);", render, re.MULTILINE)[1] == str(
            harness.FIGURE_ERROR_CHARS
        )
        assert re.search(r"process\.env\.(ANYPLOT_FIGURE_PACKAGE)", render)[1] == harness.FIGURE_PACKAGE_ENV
        figures = render[render.index("const FIGURES = {") : render.index("\n};", render.index("const FIGURES = {"))]
        assert set(re.findall(r"^  (\w+): \{", figures, re.MULTILINE)) == set(harness.FIGURE_PACKAGES)
        assert harness.EXEC_DENY_ENV in harness.FIGURE_PLOT_ONLY_ENV

    def test_the_figure_mode_flag_and_packages_are_the_renderers(self) -> None:
        assert FIGURE_FLAG == harness.FIGURE_FLAG and FIGURE_LIBRARIES == harness.FIGURE_PACKAGES

    def test_plotlys_validator_builder_is_a_code_builder_and_nothing_else_of_it_is(self) -> None:
        def frame(path: str, name: str) -> object:
            code = type("Code", (), {"co_filename": path, "co_name": name})
            return type("Frame", (), {"f_code": code, "f_back": None})

        site = "/app/.venv/lib/python3.14/site-packages"
        assert harness.builds_code(frame(f"{site}/_plotly_utils/basevalidators.py", "build_validator"))
        assert not harness.builds_code(frame(f"{site}/_plotly_utils/basevalidators.py", "__init__"))
        assert not harness.builds_code(frame(f"{site}/plotly/basedatatypes.py", "build_validator"))


class Exited(Exception):
    """`os._exit` in an in-process call of the plot step's child: the code, instead of the end of the test process."""

    def __init__(self, code: int) -> None:
        super().__init__(code)
        self.code = code


class StandInGuard:
    """`PlotGuard`'s part the plot step's child uses: the filter's state and `paused`."""

    def __init__(self, allowed: tuple[str, ...], exec_deny: str) -> None:
        self.allowed = allowed
        self.exec_deny = exec_deny

    @contextlib.contextmanager
    def paused(self) -> Iterator[None]:
        yield


def wait_status(code: int = 0, signal_number: int = 0) -> int:
    """A wait status as `os.wait4` returns it: an exit code, or a death by a signal."""
    return signal_number or code << 8


def raise_in_plot(source: str) -> None:
    """Run `source` as code of `plot.py`, so a traceback through it has the plot's frames."""
    exec(compile(source, "plot.py", "exec"), {})


class TestInProcess:
    """The figure mode's logic in the test process, where the coverage of a run counts: the parent's judgement, the
    child's exit codes and report, the records, the screenshot step's start and the steps' order, with `os.fork`,
    `os._exit`, the guard and the plot stood in. The fork, the arming and the kernel filter themselves run only in the
    subprocess cases above (an audit hook and a seccomp filter cannot be removed from the test process)."""

    @pytest.mark.parametrize(
        ("status", "report", "verdict"),
        [
            (wait_status(0), harness.FigureReport("on"), (0, None)),
            (
                wait_status(3),
                harness.FigureReport("on", record=("SystemExit", 2, "3")),
                (3, ("plot", "SystemExit", "plot.py:2", "3")),
            ),
            (
                wait_status(3),
                harness.FigureReport("unavailable"),
                (3, ("plot", "Error", None, "the plot step ended with 3")),
            ),
            (
                wait_status(3),
                harness.FigureReport("unavailable", refused=True),
                (
                    3,
                    (
                        "harness",
                        "ExecDenyUnavailable",
                        None,
                        "the sandbox could not refuse process starts (unavailable)",
                    ),
                ),
            ),
            (
                wait_status(1),
                harness.FigureReport(record=("SyntaxError", 1, "bad")),
                (1, ("plot", "SyntaxError", "plot.py:1", "bad")),
            ),
            (wait_status(1), harness.FigureReport(), (1, ("plot", "Error", None, "the plot step ended with 1"))),
            (
                wait_status(signal_number=9),
                harness.FigureReport("unavailable", refused=True),
                (137, ("crash", "PlotCrashed", None, "the plot step died of SIGKILL")),
            ),
        ],
        ids=[
            "success",
            "sys.exit(3) armed",
            "exit 3 without a filter it did not require",
            "refused",
            "a syntax error before the arming",
            "the harness's own failure",
            "a signal",
        ],
    )
    def test_the_verdict(self, status: int, report: harness.FigureReport, verdict: tuple) -> None:
        assert harness.plot_step_verdict(status, report, "work/plot.py") == verdict

    def test_the_parent_reads_the_report_after_the_wait(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        read_end, write_end = os.pipe()
        os.write(write_end, b'armed on\nerror ["SystemExit", 2, "3"]\n')
        waited: list[int] = []

        def wait4(pid: int, options: int) -> tuple[int, int, SimpleNamespace]:
            waited.append(pid)
            return pid, wait_status(3), SimpleNamespace(ru_maxrss=204800, ru_utime=0.5, ru_stime=0.25)

        monkeypatch.setattr(os, "pipe", lambda: (read_end, write_end))
        monkeypatch.setattr(os, "fork", lambda: 4242)
        monkeypatch.setattr(os, "wait4", wait4)
        run: dict = {"exec_deny": "off", "steps": {}}

        assert harness.plot_step("plot.py", "plot-light.json", run) == 3
        assert waited == [4242] and run["exec_deny"] == "on"
        assert run["steps"]["plot"]["max_rss_mb"] == 200.0 and run["steps"]["plot"]["cpu_s"] == 0.75
        assert last_line(capsys.readouterr().err) == "render: error: plot SystemExit plot.py:2: 3"

    @staticmethod
    def child(
        monkeypatch: pytest.MonkeyPatch, run_plot: Callable[..., None], *, exec_deny: str = "on"
    ) -> tuple[int, harness.FigureReport]:
        """`plot_child` with the plot `run_plot(path, guard, armed)`: its exit code and its report."""
        monkeypatch.setattr(harness, "set_plot_limits", lambda: None)
        monkeypatch.setattr(harness, "seed_mplconfig", lambda: None)
        monkeypatch.setattr(harness, "PlotGuard", lambda allowed: StandInGuard(allowed, exec_deny))
        monkeypatch.setattr(harness, "run_plot", run_plot)

        def exit_(code: int) -> None:
            raise Exited(code)

        monkeypatch.setattr(os, "_exit", exit_)
        read_end, write_end = os.pipe()
        try:
            with pytest.raises(Exited) as exited:
                harness.plot_child("plot.py", "plot-light.json", write_end)
        finally:
            os.close(write_end)
        os.set_blocking(read_end, False)
        return exited.value.code, harness._read_figure_report(read_end)

    @pytest.mark.parametrize(
        ("raised", "code", "record"),
        [
            (None, 0, None),
            ("raise SystemExit(3)", 3, ("SystemExit", 1, "3")),
            ("raise SystemExit(259)", 3, ("SystemExit", 1, "259")),
            ("raise SystemExit(256)", 0, None),
            ("raise SystemExit(None)", 0, None),
            ("raise SystemExit('no data')", 1, ("SystemExit", 1, "no data")),
            ("x = 1\nraise ValueError('boom')", 1, ("ValueError", 2, "boom")),
        ],
        ids=["success", "sys.exit(3)", "a code past 255", "256", "None", "a message", "an exception"],
    )
    def test_the_childs_code_and_report_after_the_arming(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        raised: str | None,
        code: int,
        record: tuple | None,
    ) -> None:
        def run_plot(path: str, guard: StandInGuard, armed: Callable[[str], None]) -> None:
            assert guard.allowed == ("plot-light.json",)
            armed(guard.exec_deny)
            if raised is not None:
                raise_in_plot(raised)

        exit_code, report = self.child(monkeypatch, run_plot)

        assert exit_code == code
        assert (report.state, report.refused, report.record) == ("on", False, record)
        stderr = capsys.readouterr().err
        assert ("Traceback (most recent call last):" in stderr) == (record is not None and record[0] == "ValueError")
        assert ("no data" in stderr) == (record is not None and record[2] == "no data")

    def test_a_refused_arming_is_reported_before_any_plot_code(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        def run_plot(path: str, guard: StandInGuard, armed: Callable[[str], None]) -> None:
            raise harness.ExecDenyUnavailable(guard.exec_deny)

        code, report = self.child(monkeypatch, run_plot, exec_deny="unavailable")

        assert code == harness.EXEC_DENY_EXIT
        assert (report.state, report.refused, report.record) == ("unavailable", True, None)
        assert "could not refuse process starts (unavailable)" in capsys.readouterr().err
        assert harness.plot_step_verdict(wait_status(code), report, "plot.py")[1][:2] == (
            "harness",
            "ExecDenyUnavailable",
        )

    def test_the_harnesss_own_failure_in_the_child_is_1_without_a_report(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def run_plot(path: str, guard: StandInGuard, armed: Callable[[str], None]) -> None:
            pytest.fail("the plot ran")

        def limits() -> None:
            raise OSError("setrlimit")

        monkeypatch.setattr(harness, "set_plot_limits", limits)
        monkeypatch.setattr(harness, "seed_mplconfig", lambda: None)
        monkeypatch.setattr(harness, "run_plot", run_plot)

        def exit_(code: int) -> None:
            raise Exited(code)

        monkeypatch.setattr(os, "_exit", exit_)
        read_end, write_end = os.pipe()
        with pytest.raises(Exited) as exited:
            harness.plot_child("plot.py", "plot-light.json", write_end)
        os.close(write_end)
        os.set_blocking(read_end, False)
        report = harness._read_figure_report(read_end)

        assert exited.value.code == 1 and (report.state, report.refused, report.record) == ("off", False, None)

    def test_the_error_record(self) -> None:
        guard = StandInGuard((), "on")
        try:
            raise_in_plot("def f():\n    raise KeyError('k')\n\nf()\n")
        except KeyError as exc:
            assert harness._error_record("plot.py", exc, guard) == ["KeyError", 2, "'k'"]
        try:
            compile("x = (\n", "plot.py", "exec")
        except SyntaxError as exc:
            name, line, _ = harness._error_record("plot.py", exc, guard)
            assert (name, line) == ("SyntaxError", 1)
        odd = type("not a class name", (Exception,), {})("x" * 1000)
        assert harness._error_record("plot.py", odd, guard) == ["Error", None, "x" * harness.FIGURE_ERROR_CHARS]

        class Unprintable(Exception):
            def __str__(self) -> str:
                raise RuntimeError("no text")

        assert harness._error_record("plot.py", Unprintable(), guard) == ["Unprintable", None, ""]
        assert harness._error_record("plot.py", SystemExit(4), guard, "4") == ["SystemExit", None, "4"]

    def test_the_screenshot_step_starts_without_the_plots_variables(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        for key in harness.FIGURE_PLOT_ONLY_ENV:
            monkeypatch.setenv(key, "1")
        monkeypatch.setenv("ANYPLOT_THEME", "dark")
        script = (
            "import json, os, sys\n"
            "json.dump({'argv': sys.argv[1:], 'env': dict(os.environ)}, open('seen.json', 'w'))\n"
            "sys.exit(5)\n"
        )
        run: dict = {"steps": {}}

        code = harness.screenshot_step([sys.executable, "-I", "-c", script], "plot-dark.json", "/pkg/plotly", run)

        assert code == 5
        seen = json.loads((tmp_path / "seen.json").read_text(encoding="utf-8"))
        assert seen["argv"] == ["--figure=plot-dark.json"]
        assert not set(harness.FIGURE_PLOT_ONLY_ENV) & set(seen["env"])
        assert seen["env"][harness.FIGURE_PACKAGE_ENV] == "/pkg/plotly" and seen["env"]["ANYPLOT_THEME"] == "dark"
        assert set(run["steps"]["screenshot"]) == {"max_rss_mb", "cpu_s", "wall_s"}

    def test_a_screenshot_step_killed_by_a_signal_is_128_plus_it(self, tmp_path: Path) -> None:
        script = "import os, signal\nos.kill(os.getpid(), signal.SIGTERM)\n"
        run: dict = {"steps": {}}
        assert harness.screenshot_step([sys.executable, "-I", "-c", script], "plot-light.json", "/pkg", run) == 143

    def test_a_screenshot_step_that_cannot_start_is_127(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        missing = str(tmp_path / "no-such-node")
        assert harness.screenshot_step([missing], "plot-light.json", "/pkg", {"steps": {}}) == 127
        assert last_line(capsys.readouterr().err) == (
            f"render: error: harness SpawnError -: cannot run {missing} (FileNotFoundError)"
        )

    @pytest.fixture
    def steps(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, list]:
        """`run_figure` with the limits, the package's lookup and both steps stood in: what each step was given."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("ANYPLOT_THEME", "light")
        monkeypatch.setattr(harness, "set_run_limits", lambda: None)
        monkeypatch.setattr(harness, "find_figure_package", lambda name: f"/pkg/{name}")
        given: dict[str, list] = {"plot": [], "screenshot": []}

        def plot_step(path: str, figure: str, run: dict) -> int:
            given["plot"].append((path, figure, Path(figure).exists()))
            if "TEST_FIGURE" in os.environ:
                Path(figure).write_text(os.environ["TEST_FIGURE"], encoding="utf-8")
            return int(os.environ.get("TEST_PLOT_EXIT", "0"))

        def screenshot_step(command: list[str], figure: str, package_dir: str, run: dict) -> int:
            given["screenshot"].append((command, figure, package_dir))
            return 7

        monkeypatch.setattr(harness, "plot_step", plot_step)
        monkeypatch.setattr(harness, "screenshot_step", screenshot_step)
        return given

    def test_run_figure_takes_the_steps_in_order(
        self, steps: dict[str, list], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / "plot-light.json").write_text("stale", encoding="utf-8")
        monkeypatch.setenv("TEST_FIGURE", "{}")

        assert harness.run_figure(["bokeh", "plot.py", "--", "node", "render.mjs"], {"steps": {}}) == 7
        assert steps["plot"] == [("plot.py", "plot-light.json", False)]  # the stale figure removed before
        assert steps["screenshot"] == [(["node", "render.mjs"], "plot-light.json", "/pkg/bokeh")]

    @pytest.mark.parametrize(
        ("env", "code", "line"),
        [
            ({"TEST_PLOT_EXIT": "3"}, 3, None),
            ({}, 1, "render: error: figure NoFigure -: the plot wrote no plot-light.json"),
            ({"TEST_FIGURE": ""}, 1, "render: error: figure FigureError -: plot-light.json is empty"),
            ({"ANYPLOT_THEME": "blue"}, 2, "render: error: harness UsageError -: ANYPLOT_THEME must be light or dark"),
        ],
        ids=["the plot step failed", "no figure", "an empty figure", "a bad theme"],
    )
    def test_run_figure_stops_at_the_first_failure(
        self,
        steps: dict[str, list],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        env: dict[str, str],
        code: int,
        line: str | None,
    ) -> None:
        for key, value in env.items():
            monkeypatch.setenv(key, value)

        assert harness.run_figure(["plotly", "plot.py", "--", "node"], {"steps": {}}) == code
        assert steps["screenshot"] == []
        if line is not None:
            assert last_line(capsys.readouterr().err) == line

    def test_the_end_line_carries_the_steps_even_when_a_step_raises(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        def run_figure(argv: list[str], run: dict) -> int:
            run["exec_deny"] = "on"
            run["steps"]["plot"] = {"max_rss_mb": 1.0, "cpu_s": 0.1, "wall_s": 0.2}
            raise RuntimeError("the screenshot step broke")

        monkeypatch.setattr(harness, "run_figure", run_figure)
        with pytest.raises(RuntimeError):
            harness.main_figure(["plotly", "plot.py", "--", "node"])
        lines = capsys.readouterr().out.splitlines()

        assert lines[0] == executor_module.HARNESS_START
        end = end_line("\n".join(lines))
        assert end["exec_deny"] == "on" and end["steps"] == {"plot": {"max_rss_mb": 1.0, "cpu_s": 0.1, "wall_s": 0.2}}

    def test_signal_names(self) -> None:
        assert harness._signal_name(9) == "SIGKILL" and harness._signal_name(250) == "signal 250"


class TestTheRows:
    @pytest.mark.parametrize("library", FIGURE_LIBRARIES)
    def test_plotly_and_bokeh_run_in_two_steps(self, library: str) -> None:
        row = command_for("python", library)
        assert row.figure == library and not row.in_process and row.code_file == "plot.py"
        assert row.argv == (NODE_BINARY, JS_HARNESS, f"--library={library}") and row.toolchain == (NODE_BINARY,)
        assert row.env == JS_ENV
        # The plot step's: the filter and the Python limits; the screenshot step drops them.
        assert row.exec_deny and row.rlimit_as and row.rlimit_nproc and row.rlimit_as_mb is None

    @pytest.mark.parametrize("node", [True, False], ids=["with Node", "without Node"])
    def test_a_two_step_row_is_served_only_where_node_is(
        self, config: ExecutorConfig, monkeypatch: pytest.MonkeyPatch, node: bool
    ) -> None:
        """The Python language's toolchain names no Node, so the row's own does: without it plotly and bokeh are
        `runtime_unavailable` (`Renderer._render`), matplotlib still runs, and `GET /status` still lists Python."""

        def which(binary: str, mode: int = os.F_OK | os.X_OK, path: str | None = None) -> str | None:
            return None if binary == NODE_BINARY and not node else binary

        monkeypatch.setattr(executor_module.shutil, "which", which)
        executor = SandboxExecutor(config)

        assert executor.languages()["python"] is True
        assert executor.serves("python", "matplotlib") is True
        assert all(executor.serves("python", library) is node for library in FIGURE_LIBRARIES)
        # A language without its toolchain serves none of its rows.
        monkeypatch.setattr(executor, "languages", lambda: {"python": False})
        assert executor.serves("python", "matplotlib") is False

    def test_no_other_row_runs_in_two_steps(self) -> None:
        for library, language in commands.LIBRARY_LANGUAGES.items():
            assert bool(command_for(language, library).figure) == (library in FIGURE_LIBRARIES), library

    def test_a_two_step_row_is_a_python_plot_with_a_command(self) -> None:
        with pytest.raises(ValueError, match="two-step"):
            RuntimeCommand("javascript", "plot.js", ("node",), figure="plotly")
        with pytest.raises(ValueError, match="two-step"):
            RuntimeCommand("python", "plot.py", (), figure="plotly")

    def test_the_argv_runs_the_harness_in_figure_mode(self, config: ExecutorConfig, tmp_path: Path) -> None:
        row = command_for("python", "bokeh")
        argv = build_argv(config, "r-a-dark", tmp_path, "dark", 60, command=row)

        assert argv[argv.index(config.harness) :] == [
            config.harness,
            FIGURE_FLAG,
            "bokeh",
            "plot.py",
            "--",
            NODE_BINARY,
            JS_HARNESS,
            "--library=bokeh",
        ]

    def test_the_environment_is_a_python_rows_plus_the_javascript_rows(self, config: ExecutorConfig) -> None:
        limited = replace(config, rlimit_as_mb=1024, rlimit_nproc=64)
        env = sandbox_env(limited, "dark", 60, command=command_for("python", "plotly"))

        assert env["ANYPLOT_THEME"] == "dark" and env["MPLBACKEND"] == "Agg"
        assert {key: env[key] for key in JS_ENV} == dict(JS_ENV)
        assert env["ANYPLOT_DENY_EXEC"] == "required"
        assert env["ANYPLOT_RLIMIT_AS_MB"] == "1024" and env["ANYPLOT_RLIMIT_NPROC"] == "64"
        assert env["PATH"] == SANDBOX_PATH and env["HOME"] == "/tmp"
        # Every other row's environment is what it was.
        matplotlib = sandbox_env(limited, "dark", 60, command=command_for("python", "matplotlib"))
        assert "ANYPLOT_SANDBOX" not in matplotlib and "PLAYWRIGHT_BROWSERS_PATH" not in matplotlib


WRAPPER = (
    "import importlib.util, sys\n"
    "spec = importlib.util.spec_from_file_location('harness', {harness!r})\n"
    "harness = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(harness)\n"
    "harness.find_figure_package = lambda name: {package!r}\n"
    "sys.exit(harness.main(sys.argv))\n"
)
"""The harness for the executor's runs: the image's, with the package's lookup standing in."""


class TestTheRenderersTimeout:
    """The job's one timeout covers both steps: the executor kills the launcher's process group, the harness and both
    of its children with it, whichever step runs."""

    @pytest.fixture
    def figure_executor(
        self, config: ExecutorConfig, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> SandboxExecutor:
        wrapper = tmp_path / "harness_wrapper.py"
        stand_in = tmp_path / "site-packages" / "plotly"
        stand_in.mkdir(parents=True)
        wrapper.write_text(WRAPPER.format(harness=str(HARNESS_SOURCE), package=str(stand_in)), encoding="utf-8")
        shot = tmp_path / "shot.py"
        shot.write_text(
            "import os, sys, time\n"
            "if os.environ.get('ANYPLOT_THEME') == 'dark':\n"
            "    time.sleep(60)\n"
            "open('plot-' + os.environ['ANYPLOT_THEME'] + '.png', 'wb').write(b'\\x89PNG\\r\\n\\x1a\\n')\n",
            encoding="utf-8",
        )
        row = replace(command_for("python", "plotly"), argv=(sys.executable, "-I", str(shot)), env={})
        monkeypatch.setattr(executor_module, "command_for", lambda language, library: row)
        return SandboxExecutor(replace(config, harness=str(wrapper)))

    @staticmethod
    def job(source: str, timeout_s: float) -> RenderRequest:
        return RenderRequest(
            job_id="figure1",
            language="python",
            library="plotly",
            source=source,
            data_csv="x\n1\n",
            themes=["light"],
            timeout_s=timeout_s,
        )

    async def test_a_plot_step_that_runs_on_is_stopped(
        self, figure_executor: SandboxExecutor, launcher: FakeLauncher, config: ExecutorConfig
    ) -> None:
        started = time.monotonic()
        run = await figure_executor.run_theme(self.job("import time\ntime.sleep(60)\n", 1.5), "light")

        assert run.timed_out and run.reason == "timeout" and run.exit_code is None
        assert time.monotonic() - started < 15
        assert launcher.deletes() == launcher.launches()
        assert list(config.runs_dir.iterdir()) == []

    async def test_a_screenshot_step_that_runs_on_is_stopped(
        self, figure_executor: SandboxExecutor, launcher: FakeLauncher
    ) -> None:
        started = time.monotonic()
        plot = "open('plot-dark.json', 'w').write('{}')\n"
        run = await figure_executor.run_theme(self.job(plot, 2.5), "dark")

        assert run.timed_out and run.reason == "timeout" and run.png_base64 is None
        assert time.monotonic() - started < 15
        assert launcher.deletes() == launcher.launches()

    async def test_both_steps_within_the_timeout_render(self, figure_executor: SandboxExecutor) -> None:
        run = await figure_executor.run_theme(self.job("open('plot-light.json', 'w').write('{}')\n", 30), "light")

        assert run.exit_code == 0 and not run.timed_out, run.stderr_tail
        assert run.png_base64 is not None and run.probe is None
