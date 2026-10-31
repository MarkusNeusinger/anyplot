"""The harness's figure mode (`harness.py --figure <package> plot.py -- <screenshot command>`, PB-1 of step 4 in
agentic/specs/261024-agent-all-libraries.md): the plot step forked before anything is armed, the plot armed in the
child, the parent never armed, the figure's checks, the final error line of either step, and the renderer's
two-step rows.

The harness runs in a subprocess of its own (an audit hook and a seccomp filter cannot be removed), loaded by a
driver that stands in for the package's lookup, so these cases need neither plotly nor bokeh; the screenshot command
is a Python script that reports what it ran under. `tests/unit/automation/test_js_render_figure.py` draws real
figures through the JavaScript harness.
"""

import json
import os
import platform
import re
import resource
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

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
        ("written", "state", "record"),
        [
            (b"", "off", None),
            (b"exec_deny on\n", "on", None),
            (b"exec_deny forged\n", "unavailable", None),
            (b'error ["SyntaxError", 3, "bad"]\n', "off", ("SyntaxError", 3, "bad")),
            (b'exec_deny on\nerror ["ValueError", 0, "x"]\n', "on", ("ValueError", None, "x")),
            (b'exec_deny on\nerror ["not a class", 2, "x"]\nerror [1, 2]\n', "on", None),
            (b'exec_deny on\nerror ["A", 2, "x"]\nnoise\n', "on", ("A", 2, "x")),
        ],
        ids=["nothing", "on", "a forged state", "before arming", "line 0", "malformed", "noise after"],
    )
    def test_the_report_pipe(self, written: bytes, state: str, record: tuple | None) -> None:
        read_end, write_end = os.pipe()
        os.write(write_end, written)
        os.close(write_end)
        os.set_blocking(read_end, False)
        assert harness._read_figure_report(read_end) == (state, record)

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


class TestTheRows:
    @pytest.mark.parametrize("library", FIGURE_LIBRARIES)
    def test_plotly_and_bokeh_run_in_two_steps(self, library: str) -> None:
        row = command_for("python", library)
        assert row.figure == library and not row.in_process and row.code_file == "plot.py"
        assert row.argv == (NODE_BINARY, JS_HARNESS, f"--library={library}") and row.toolchain == (NODE_BINARY,)
        assert row.env == JS_ENV
        # The plot step's: the filter and the Python limits; the screenshot step drops them.
        assert row.exec_deny and row.rlimit_as and row.rlimit_nproc and row.rlimit_as_mb is None

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
