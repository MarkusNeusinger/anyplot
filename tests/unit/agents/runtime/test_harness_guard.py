"""The harness's audit-hook guards against exec and process routes: `PlotGuard` (plot mode) and `DataGuard`'s
code events (data mode).

Each end-to-end case runs the real harness in a subprocess with the test interpreter, because an audit hook
can never be removed from the process that arms it. The routes are the ones the validator review of 2026-10-14
found (`np.testing.measure` compiles and execs its string), generalised: the harness is the second layer
behind the validator, so these plots and snippets are written as if the validator had missed them.
"""

import json
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from agents.anyplot.render import harness
from agents.anyplot.render.runtimes.python import HARNESS_SOURCE


THEME = "light"
HEADER = "import matplotlib\nmatplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nimport numpy as np\n"
SAVE = "\nfig, ax = plt.subplots(figsize=(4, 3))\nax.plot([0, 1], [0, 1])\nplt.savefig('plot-light.png')\n"
MARKER = "pwned"
DATA_EXIT = harness.DATA_EXIT


def render(tmp_path: Path, body: str) -> tuple[int, str]:
    """Exit code and stderr of one plot-mode run of HEADER + body + SAVE in `tmp_path`."""
    return render_file(tmp_path, HEADER + body + SAVE)


def render_file(tmp_path: Path, code: str) -> tuple[int, str]:
    """Exit code and stderr of one plot-mode run of `code`, a whole plot file, in `tmp_path`."""
    (tmp_path / "plot.py").write_text(code, encoding="utf-8")
    done = subprocess.run(
        [sys.executable, *harness.INTERPRETER_FLAGS, str(HARNESS_SOURCE), "plot.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=180,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path),
            "ANYPLOT_THEME": THEME,
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(tmp_path / "mpl"),
            "ANYPLOT_RLIMIT_CPU_S": "120",
        },
    )
    return done.returncode, done.stderr


def run_data(tmp_path: Path, code: str) -> tuple[int, str | None, str]:
    """Exit code, `out.csv` (None when missing) and stderr of one data-mode run in `tmp_path`."""
    (tmp_path / "snippet.py").write_text(code, encoding="utf-8")
    done = subprocess.run(
        [sys.executable, *harness.INTERPRETER_FLAGS, str(HARNESS_SOURCE), harness.DATA_FLAG, "snippet.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
        env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "ANYPLOT_RLIMIT_CPU_S": "60"},
    )
    out = tmp_path / harness.DATA_OUT_FILE
    return done.returncode, out.read_text(encoding="utf-8") if out.exists() else None, done.stderr


# Each writes the marker file (or tries to) through a route the guard must refuse; the payload is text the
# route compiles or runs, so a refusal leaves no marker behind.
WRITE_MARKER = f"open('{MARKER}', 'w').write('x')"
PLOT_ROUTES = [
    pytest.param(f'np.testing.measure("{WRITE_MARKER}")\n', id="numpy.testing.measure (the reported case)"),
    pytest.param(f'np.testing.runstring("{WRITE_MARKER}", {{}})\n', id="numpy.testing.runstring"),
    pytest.param(f'exec("{WRITE_MARKER}")\n', id="exec of text"),
    pytest.param(f'eval(compile("{WRITE_MARKER}", "s", "eval"))\n', id="eval of a compiled code object"),
    pytest.param(
        f'f = lambda: 0\nf.__code__ = compile("{WRITE_MARKER}", "s", "eval")\nf()\n', id="__code__ assignment"
    ),
    pytest.param(
        f'import types\ntypes.FunctionType(compile("{WRITE_MARKER}", "s", "exec"), {{}})()\n', id="FunctionType"
    ),
    pytest.param(f'import os\nos.system("python3 -c \\"{WRITE_MARKER}\\"")\n', id="os.system"),
    pytest.param(f"import subprocess\nsubprocess.run(['touch', '{MARKER}'])\n", id="subprocess"),
    pytest.param(f"import os\nos.posix_spawn('/usr/bin/touch', ['touch', '{MARKER}'], {{}})\n", id="posix_spawn"),
    pytest.param("import socket\nsocket.socket()\n", id="socket"),
    pytest.param("lib = np.zeros(1).ctypes._ctypes.CDLL(None)\n", id="native code through an array"),
    # Python 3.14: every call through a ctypes function pointer raises `ctypes.call_function`; only the `ctypes.cast`
    # an import makes passes (`IMPORT_CTYPES_HELPERS`), so the plot's own cast, memmove and string_at stay refused.
    pytest.param(
        "a = np.zeros(8)\nraw = a.ctypes._ctypes.string_at(a.ctypes.data, 8)\n", id="string_at through an array"
    ),
    pytest.param(
        "import ctypes\np = ctypes.cast(ctypes.c_char_p(b'x'), ctypes.POINTER(ctypes.c_char))\n", id="cast in the plot"
    ),
    pytest.param("import ctypes\nb = (ctypes.c_char * 4)()\nctypes.memmove(b, b'abcd', 4)\n", id="memmove in the plot"),
    pytest.param("import ctypes\nb = (ctypes.c_char * 4)()\nctypes.memset(b, 65, 4)\n", id="memset in the plot"),
    # Python 3.14's PEP 768: `sys.remote_exec` makes a process, this one included, run a script file.
    pytest.param("import os, sys\nsys.remote_exec(os.getpid(), 'plot.py')\n", id="sys.remote_exec into the plot"),
    # PEP 734 subinterpreters (Fable review of the 3.14 bump): the audit hook belongs to one interpreter, so code
    # run in another would write past it; the calls that create or enter one are replaced before arming.
    pytest.param(
        f'import _interpreters\ni = _interpreters.create()\n_interpreters.exec(i, "{WRITE_MARKER}")\n',
        id="_interpreters.exec",
    ),
    pytest.param(
        f'from concurrent import interpreters\ninterpreters.create().exec("{WRITE_MARKER}")\n',
        id="concurrent.interpreters exec",
        marks=pytest.mark.skipif(sys.version_info < (3, 14), reason="concurrent.interpreters is new in 3.14"),
    ),
    pytest.param(
        "from concurrent.futures import InterpreterPoolExecutor\n"
        f'with InterpreterPoolExecutor(1) as pool:\n    pool.submit(exec, "{WRITE_MARKER}").result()\n',
        id="InterpreterPoolExecutor",
        marks=pytest.mark.skipif(sys.version_info < (3, 14), reason="InterpreterPoolExecutor is new in 3.14"),
    ),
    pytest.param(f"{WRITE_MARKER}\n", id="open for writing"),
    pytest.param(f"import os\nos.open('{MARKER}', os.O_CREAT | os.O_WRONLY)\n", id="os.open for writing"),
    pytest.param("plt.figure().savefig('plot-dark.png')\n", id="a save to another name"),
    pytest.param("import os\nos.remove('plot.py')\n", id="remove"),
    pytest.param("import os\nos.chdir('/')\n", id="chdir moves the outputs"),
    # The #12177 review: calls that raise no audit event, and a write that names an output relative to another
    # directory.
    pytest.param(f"import os\nos.mkfifo('{MARKER}')\n", id="mkfifo raises no audit event"),
    pytest.param(f"import os\nos.mknod('{MARKER}')\n", id="mknod raises no audit event"),
    pytest.param(f"import posix\nposix.mkfifo('{MARKER}')\n", id="mkfifo through posix"),
    pytest.param(
        "import os\nd = os.open('mpl', os.O_RDONLY)\nos.open('plot-light.png', os.O_CREAT | os.O_WRONLY, dir_fd=d)\n",
        id="an output name relative to another directory",
    ),
    # The Fable review of #12177: a frame's `f_builtins` hands out `open` and `__import__` past the validator.
    pytest.param(f"g = (i for i in [])\ng.gi_frame.f_builtins['open']('{MARKER}', 'w')\n", id="a generator's frame"),
    pytest.param(f"import sys\nsys._getframe(0).f_builtins['open']('{MARKER}', 'w')\n", id="sys._getframe in the plot"),
    pytest.param("import sys\nframes = sys._current_frames()\n", id="sys._current_frames"),
    pytest.param(
        "try:\n    1 / 0\nexcept ZeroDivisionError as error:\n    f = error.__traceback__.tb_frame\n",
        id="a traceback's frame",
    ),
    pytest.param("async def c():\n    pass\n\nf = c().cr_frame\n", id="a coroutine's frame"),
    pytest.param(
        "import pandas as pd\ng = (i for i in [])\nf = pd.Series([g]).apply(getattr, args=('gi_frame',))\n",
        id="a frame fetched by library code the plot called",
    ),
    # The #12181 review: a worker thread runs a callable the plot submitted with no plot frame above it, and the
    # frames it returns reach `run_plot`'s locals and the guard; `gc` hands out the guard object directly.
    pytest.param(
        "import sys\nfrom concurrent.futures import ThreadPoolExecutor\n"
        "with ThreadPoolExecutor(1) as pool:\n    frames = pool.submit(sys._current_frames).result()\n"
        "for f in frames.values():\n    while f is not None:\n"
        "        if 'guard' in f.f_locals:\n            f.f_locals['guard'].armed = False\n"
        "        f = f.f_back\n"
        f"open('{MARKER}', 'w').write('x')\n",
        id="sys._current_frames in a worker thread",
    ),
    pytest.param(
        f"import gc\nfor o in gc.get_objects():\n    if hasattr(o, 'plot_file'):\n        o.armed = False\n"
        f"open('{MARKER}', 'w').write('x')\n",
        id="gc hands out the guard",
    ),
]
# Fable review of #12181: a trace, profile or signal callback gets the real frame and walks `f_back` (no audit event)
# to `run_plot`'s or `run_data_snippet`'s locals, where the guard sits. Each payload disarms whatever guard it finds,
# then writes the marker.
DISARM = (
    "def disarm(frame, *rest):\n"
    "    while frame is not None:\n"
    "        for value in list(frame.f_locals.values()):\n"
    "            if hasattr(value, 'armed'):\n"
    "                value.armed = False\n"
    "        frame = frame.f_back\n"
    "def touch():\n"
    "    return 1\n"
)
WRITE_AFTER = f"\nopen('{MARKER}', 'w').write('x')\n"
CALLBACK_ROUTES = [
    pytest.param("import sys\nsys.settrace(disarm)\ntouch()\nsys.settrace(None)", id="sys.settrace"),
    pytest.param("import sys\nsys.setprofile(disarm)\ntouch()\nsys.setprofile(None)", id="sys.setprofile"),
    pytest.param(
        "import threading\nthreading.settrace_all_threads(disarm)\ntouch()\nthreading.settrace_all_threads(None)",
        id="threading.settrace_all_threads",
    ),
    pytest.param(
        "import sys\nm = sys.monitoring\nm.use_tool_id(3, 'x')\n"
        "m.register_callback(3, m.events.PY_START, lambda code, offset: disarm(sys._getframe(1)))\n"
        "m.set_events(3, m.events.PY_START)\ntouch()\nm.set_events(3, 0)",
        id="sys.monitoring",
    ),
    pytest.param(
        "import signal\nsignal.signal(signal.SIGUSR1, lambda signum, frame: disarm(frame))\n"
        "signal.raise_signal(signal.SIGUSR1)",
        id="a signal handler",
    ),
]


class TestPlotGuard:
    @pytest.mark.parametrize("body", PLOT_ROUTES)
    def test_route_fails_the_render_and_leaves_no_trace(self, tmp_path: Path, body: str) -> None:
        exit_code, stderr = render(tmp_path, body)
        assert exit_code != 0
        assert "blocked by the" in stderr and "sandbox" in stderr, stderr[-2000:]
        assert not (tmp_path / MARKER).exists()
        assert not (tmp_path / "plot-dark.png").exists() and not (tmp_path / "mpl" / "plot-light.png").exists()
        assert (tmp_path / "plot.py").exists()

    @pytest.mark.parametrize("body", CALLBACK_ROUTES)
    def test_frame_callbacks_are_refused(self, tmp_path: Path, body: str) -> None:
        exit_code, stderr = render(tmp_path, DISARM + body + WRITE_AFTER)
        assert exit_code != 0
        assert "blocked by the" in stderr and "sandbox" in stderr, stderr[-2000:]
        assert not (tmp_path / MARKER).exists()

    def test_a_caught_refusal_refuses_the_action_and_the_plot_still_renders(self, tmp_path: Path) -> None:
        body = f'try:\n    np.testing.measure("{WRITE_MARKER}")\nexcept PermissionError:\n    pass\n'
        exit_code, stderr = render(tmp_path, body)
        assert exit_code == 0, stderr[-2000:]
        assert (tmp_path / "plot-light.png").exists() and (tmp_path / "probe-light.json").exists()
        assert not (tmp_path / MARKER).exists()

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param("", id="a plain plot writes its PNG and probe"),
            pytest.param("import scipy.stats\nimport pandas as pd\n", id="imports that build code"),
            pytest.param(
                "from scipy import stats\nh = stats.rv_histogram(np.histogram([1, 2, 2, 3], bins=3))\n"
                "d = stats.rv_discrete(values=([0, 1], [0.5, 0.5]))\n",
                id="a distribution built at draw time",
            ),
            pytest.param(
                "import collections\nimport dataclasses\nimport pandas as pd\n"
                "P = collections.namedtuple('P', 'x y')\nD = dataclasses.make_dataclass('D', ['a'])\n"
                "rows = list(pd.DataFrame({'a': [1, 2]}).itertuples())\n",
                id="namedtuple, make_dataclass and itertuples",
            ),
            pytest.param(
                "import numpy as np\nfrom sklearn.cluster import KMeans\n"
                "KMeans(n_clusters=2, n_init=2, random_state=0).fit(np.array([[0.0], [0.1], [5.0], [5.1]]))\n",
                id="scikit-learn with threadpoolctl and loky",
            ),
            pytest.param("import asyncio\n", id="an import that assigns __code__"),
            pytest.param(
                "fig, ax = plt.subplots()\nax.set_title(r'$\\alpha^2$')\nax.legend(['a'])\n", id="mathtext and a legend"
            ),
            # Library code that reads frames while the plot runs (`FRAME_READERS`, `hide_frames`).
            pytest.param(
                "fig, ax = plt.subplots()\nax.set_title(r'$\\alpha^2$')\nfig.canvas.draw()\n",
                id="mathtext drawn: pyparsing's traceback summaries",
            ),
            pytest.param(
                "import pandas as pd\ndf = pd.DataFrame({'a': [1.0, None]})\ndf['a'].fillna(0, inplace=True)\n",
                id="pandas' chained-assignment check",
            ),
            pytest.param(
                "import pandas as pd\nd = pd.to_datetime(['10/11/12', '13/11/12'])\n",
                id="a pandas warning's stack level",
            ),
            pytest.param(
                "import statsmodels.api as sm\nsm.qqplot(np.array([1.0, 2.0, 3.0, 4.5]), line='s')\n",
                id="a statsmodels graphic names its caller",
            ),
            pytest.param(
                "plt.rcParams['font.family'] = 'NoSuchFamily'\nfig, ax = plt.subplots()\nax.set_title('x')\n"
                "fig.canvas.draw()\n",
                id="a logged findfont warning",
            ),
        ],
    )
    def test_ordinary_plots_still_render(self, tmp_path: Path, body: str) -> None:
        exit_code, stderr = render(tmp_path, body)
        assert exit_code == 0, stderr[-3000:]
        assert (tmp_path / "plot-light.png").exists() and (tmp_path / "probe-light.json").exists()

    def test_seaborn_still_renders(self, tmp_path: Path) -> None:
        pytest.importorskip("seaborn")
        body = "import pandas as pd\nimport seaborn as sns\nsns.set_theme(style='white')\n"
        body += "sns.histplot(pd.DataFrame({'v': [1, 2, 2, 3]}), x='v')\n"
        exit_code, stderr = render(tmp_path, body)
        assert exit_code == 0, stderr[-3000:]

    def test_the_html_twin_may_be_written(self, tmp_path: Path) -> None:
        """`plot-<theme>.html` (altair's second file) is the one write allowed beside the PNG and the probe."""
        exit_code, stderr = render(tmp_path, "open('plot-light.html', 'w').write('<html></html>')\n")
        assert exit_code == 0, stderr[-2000:]
        assert (tmp_path / "plot-light.html").read_text(encoding="utf-8") == "<html></html>"
        assert (tmp_path / "plot-light.png").exists() and (tmp_path / "probe-light.json").exists()

    @pytest.mark.parametrize(
        "name", [pytest.param("other.html", id="another name"), pytest.param("plot-dark.html", id="the other theme")]
    )
    def test_any_other_html_is_refused(self, tmp_path: Path, name: str) -> None:
        exit_code, stderr = render(tmp_path, f"open('{name}', 'w').write('<html></html>')\n")
        assert exit_code != 0
        assert "blocked by the render sandbox" in stderr, stderr[-2000:]
        assert not (tmp_path / name).exists()

    def test_inspect_currentframe_answers_none_to_the_plot(self, tmp_path: Path) -> None:
        """`hide_frames` replaces `inspect.currentframe` with `frame_for_readers`, which hands a frame to
        `FRAME_READERS` alone: plot code gets None, not a refusal, so the run goes on."""
        body = "import inspect\nassert inspect.currentframe() is None\n"
        body += "def nested():\n    return inspect.currentframe()\nassert nested() is None\n"
        exit_code, stderr = render(tmp_path, body)
        assert exit_code == 0, stderr[-2000:]
        assert "blocked by the" not in stderr
        assert (tmp_path / "plot-light.png").exists()

    def test_pandas_chained_assignment_on_a_copy_warns_and_renders(self, tmp_path: Path) -> None:
        """pandas' check (`is_local_in_caller_frame`, a `FRAME_READERS` entry) reads the plot's frame, decides the
        Series is a temporary and warns; the warning names the plot's line and the plot renders."""
        body = "import pandas as pd\ndf = pd.DataFrame({'a': [1.0, None], 'b': [1, 2]})\nsub = df[df['b'] > 0]\n"
        body += "sub['a'].fillna(0, inplace=True)\n"
        exit_code, stderr = render(tmp_path, body)
        assert exit_code == 0, stderr[-2000:]
        assert "plot.py:8: ChainedAssignmentError" in stderr, stderr[-2000:]
        assert "blocked by the" not in stderr
        assert (tmp_path / "plot-light.png").exists() and (tmp_path / "probe-light.json").exists()

    def test_plotnine_renders_and_probes(self, tmp_path: Path) -> None:
        """plotnine's `Environment.capture` reads the plot's frame (`FRAME_READERS`) to look `aes("x", "y")` up, and
        the probe measures the figure plotnine builds without a canvas (`_renderer` attaches Agg's)."""
        pytest.importorskip("plotnine")
        code = (
            "import os\n\nimport pandas as pd\nfrom plotnine import aes, geom_point, ggplot\n\n"
            "THEME = os.environ['ANYPLOT_THEME']\n"
            "df = pd.DataFrame({'x': [1.0, 2.0, 3.0], 'y': [2.0, 1.0, 3.0]})\n"
            "plot = ggplot(df, aes('x', 'y')) + geom_point()\n"
            "plot.save(f'plot-{THEME}.png', dpi=100, width=4, height=3, units='in', verbose=False)\n"
        )
        exit_code, stderr = render_file(tmp_path, code)
        assert exit_code == 0, stderr[-3000:]
        assert "blocked by the" not in stderr
        png = (tmp_path / "plot-light.png").read_bytes()
        assert struct.unpack(">II", png[16:24]) == (400, 300)
        probe = json.loads((tmp_path / "probe-light.json").read_text(encoding="utf-8"))
        assert probe.get("canvas") == [400, 300] and probe.get("points") == 3, probe

    def test_altair_renders_its_png_and_html(self, tmp_path: Path) -> None:
        """altair draws through vl-convert, not a matplotlib figure, so the run writes no probe and needs none."""
        pytest.importorskip("altair")
        pytest.importorskip("vl_convert")
        code = (
            "import os\n\nimport altair as alt\nimport pandas as pd\n\n"
            "THEME = os.environ['ANYPLOT_THEME']\n"
            "df = pd.DataFrame({'x': ['a', 'b', 'c'], 'y': [1, 3, 2]})\n"
            "chart = alt.Chart(df).mark_bar().encode(x='x:N', y='y:Q').properties(width=200, height=150)\n"
            "chart.save(f'plot-{THEME}.png', scale_factor=2.0)\n"
            "chart.save(f'plot-{THEME}.html')\n"
        )
        exit_code, stderr = render_file(tmp_path, code)
        assert exit_code == 0, stderr[-3000:]
        assert "blocked by the" not in stderr
        assert (tmp_path / "plot-light.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        assert "<html" in (tmp_path / "plot-light.html").read_text(encoding="utf-8")

    def test_a_syntax_error_is_reported_before_the_guard(self, tmp_path: Path) -> None:
        exit_code, stderr = render(tmp_path, "x = (\n")
        assert exit_code != 0 and "SyntaxError" in stderr and 'plot.py", line' in stderr

    def test_a_plot_error_keeps_its_traceback(self, tmp_path: Path) -> None:
        """The interpreter reads the traceback's frames through `traceback`'s summary builder (`FRAME_READERS`), so
        the frame refusal never hides the line the repair needs."""
        exit_code, stderr = render(tmp_path, "raise ValueError('boom')\n")
        assert exit_code != 0 and "ValueError: boom" in stderr and 'plot.py", line 5' in stderr
        assert "blocked by the" not in stderr

    def test_a_caught_frame_refusal_still_renders(self, tmp_path: Path) -> None:
        body = "g = (i for i in [])\ntry:\n    f = g.gi_frame\nexcept PermissionError:\n    f = None\n"
        exit_code, stderr = render(tmp_path, body)
        assert exit_code == 0, stderr[-2000:]
        assert (tmp_path / "plot-light.png").exists()


REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOGUE_UNDER_GUARD = [
    pytest.param("ice-basic", "matplotlib", id="ice-basic/matplotlib: scikit-learn GradientBoostingRegressor"),
    pytest.param("mosaic-categorical", "matplotlib", id="mosaic-categorical/matplotlib: a statsmodels graphic"),
    pytest.param("line-arrhenius", "matplotlib", id="line-arrhenius/matplotlib: mathtext"),
    pytest.param("silhouette-basic", "seaborn", id="silhouette-basic/seaborn: KMeans"),
    pytest.param("scatter-basic", "plotnine", id="scatter-basic/plotnine: aes through Environment.capture"),
    pytest.param("scatter-basic", "altair", id="scatter-basic/altair: vl-convert, PIL padding and the HTML"),
]
LIBRARY_MODULES = {"seaborn": ("seaborn",), "plotnine": ("plotnine",), "altair": ("altair", "vl_convert")}
"""The modules a library's catalogue case needs beyond matplotlib's stack; CI's test environment installs none."""


@pytest.mark.parametrize(("spec_id", "library"), CATALOGUE_UNDER_GUARD)
def test_catalogue_files_render_under_the_guard(tmp_path: Path, spec_id: str, library: str) -> None:
    """Real catalogue files, normalised as a session opening does, render under the plot guard: a guard change that
    breaks scikit-learn, statsmodels, mathtext, plotnine's frame read or altair's vl-convert fails here. The seaborn,
    plotnine and altair cases need their libraries, which CI's test environment does not install; the renderer-image
    job of `ci-image.yml` renders all three through the harness in the image. altair draws no matplotlib figure, so its
    run writes no probe: the PNG and its HTML twin are what the case checks."""
    from agents.anyplot.code.normalise import normalise
    from core.utils import strip_noqa_comments

    for module in LIBRARY_MODULES.get(library, ()):
        pytest.importorskip(module)
    source = REPO_ROOT / "plots" / spec_id / "implementations" / "python" / f"{library}.py"
    if not source.exists():
        pytest.skip(f"{spec_id}/{library} is absent")
    code = normalise(strip_noqa_comments(source.read_text(encoding="utf-8")) or "", library=library)
    (tmp_path / "plot.py").write_text(code, encoding="utf-8")
    done = subprocess.run(
        [sys.executable, "-I", str(HARNESS_SOURCE), "plot.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=180,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path),
            "ANYPLOT_THEME": THEME,
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(tmp_path / "mpl"),
            "ANYPLOT_RLIMIT_CPU_S": "120",
        },
    )
    assert done.returncode == 0, done.stderr[-3000:]
    assert "blocked by the" not in done.stderr
    assert (tmp_path / "plot-light.png").exists()
    if library == "altair":
        assert (tmp_path / "plot-light.html").exists()
    else:
        assert (tmp_path / "probe-light.json").exists()


class TestPlotGuardUnit:
    def guard(self, tmp_path: Path) -> harness.PlotGuard:
        return harness.PlotGuard((str(tmp_path / "plot-light.png"), str(tmp_path / "probe-light.json")))

    def test_writes_only_the_outputs(self, tmp_path: Path) -> None:
        guard = self.guard(tmp_path)
        assert not guard.refuses("open", (str(tmp_path / "plot-light.png"), "wb", 577))
        assert not guard.refuses("open", (str(tmp_path / "probe-light.json"), "w", 577))
        assert not guard.refuses("open", ("/etc/hostname", "r", 0))
        assert not guard.refuses("open", ("/etc/hostname", None, harness.os.O_RDONLY))
        assert guard.refuses("open", (str(tmp_path / "x.txt"), "w", 577))
        assert guard.refuses("open", (str(tmp_path / "x.txt"), "r+", 2))
        assert guard.refuses("open", (str(tmp_path / "x.txt"), None, harness.os.O_WRONLY | harness.os.O_CREAT))
        assert guard.refuses("open", (1, "w", 1))
        write = harness.os.O_WRONLY | harness.os.O_CREAT
        assert not guard.refuses("open", (str(tmp_path / "plot-light.png"), None, write))
        assert guard.refuses("open", ("plot-light.png", None, write))  # os.open: the event carries no dir_fd

    def test_refuses_processes_and_sockets_but_not_imports_or_reads(self, tmp_path: Path) -> None:
        guard = self.guard(tmp_path)
        for event in ("subprocess.Popen", "os.system", "os.posix_spawn", "os.fork", "socket.connect", "os.chdir"):
            assert guard.refuses(event, ()), event
        for event in ("import", "os.listdir", "os.putenv", "compile", "builtins.id", "sys._getframemodulename"):
            assert not guard.refuses(event, ()), event

    def test_refuses_frames_outside_readers_and_imports(self, tmp_path: Path) -> None:
        """A frame event raised here, with no plot frame on the stack (a worker thread's case) or with this test
        file standing in for the plot, is refused; a module name or a non-frame attribute is not."""
        guard = self.guard(tmp_path)
        frame_events = (("sys._getframe", (0,)), ("sys._current_frames", ()), ("object.__getattr__", (1, "tb_frame")))
        for plot_file in (None, __file__):
            guard.plot_file = plot_file
            for event, args in frame_events:
                assert guard.refuses(event, args), (plot_file, event)
        assert not guard.refuses("object.__getattr__", (1, "__code__"))
        assert not guard.refuses("sys._getframemodulename", (0,))
        assert guard.refuses("gc.get_objects", ()) and guard.refuses("gc.get_referrers", ())

    def test_frame_readers_match_their_whole_chain(self) -> None:
        reader = type("Code", (), {"co_filename": "/usr/lib/python3.13/traceback.py", "co_name": "extract_stack"})
        frame = type("Frame", (), {"f_code": reader, "f_back": None})
        assert harness.reads_frames(frame)
        walker = type(
            "Code", (), {"co_filename": "/usr/lib/python3.13/traceback.py", "co_name": "_walk_tb_with_full_positions"}
        )
        assert not harness.reads_frames(type("Frame", (), {"f_code": walker, "f_back": None}))
        builder = type(
            "Code",
            (),
            {"co_filename": "/usr/lib/python3.13/traceback.py", "co_name": "_extract_from_extended_frame_gen"},
        )
        consumed = type("Frame", (), {"f_code": builder, "f_back": None})
        assert harness.reads_frames(type("Frame", (), {"f_code": walker, "f_back": consumed}))
        assert not harness.reads_frames(None)

    def test_refuses_remote_debugging(self, tmp_path: Path) -> None:
        guard = self.guard(tmp_path)
        assert guard.refuses("sys.remote_exec", (1, "x.py")) and guard.refuses("cpython.remote_debugger_script", ())

    def test_exec_from_the_test_is_refused_but_the_entry_runs_once(self, tmp_path: Path) -> None:
        guard = self.guard(tmp_path)
        code = compile("1", "plot.py", "eval")
        guard.armed = True  # never `arm()` in the test process: an audit hook cannot be removed
        guard.entry, guard.plot_file = code, "plot.py"
        guard("exec", (code,))
        with pytest.raises(PermissionError):
            guard("exec", (code,))
        with pytest.raises(PermissionError):
            guard("ctypes.dlopen", ("libc",))
        assert guard.blocked == "exec"


class TestDataGuardCode:
    @pytest.mark.parametrize(
        "code",
        [
            pytest.param('exec("x = 1")\n', id="exec"),
            pytest.param('x = eval("1")\n', id="eval"),
            pytest.param('c = compile("1", "s", "eval")\n', id="compile"),
            pytest.param('import numpy as np\nnp.testing.measure("1")\n', id="numpy.testing.measure"),
        ],
    )
    def test_code_routes_fail_the_run(self, tmp_path: Path, code: str) -> None:
        exit_code, out, stderr = run_data(tmp_path, "import pandas as pd\n" + code + "df = pd.DataFrame()\n")
        assert exit_code == DATA_EXIT["blocked"], stderr
        assert out == ""

    @pytest.mark.parametrize("body", CALLBACK_ROUTES)
    def test_frame_callbacks_are_refused(self, tmp_path: Path, body: str) -> None:
        code = "import pandas as pd\n" + DISARM + body + WRITE_AFTER + "df = pd.DataFrame({'a': [1]})\n"
        exit_code, out, stderr = run_data(tmp_path, code)
        assert exit_code in (DATA_EXIT["blocked"], DATA_EXIT["error"]), stderr
        assert out == "" and not (tmp_path / MARKER).exists()

    def test_unaudited_calls_are_replaced(self, tmp_path: Path) -> None:
        code = "import os\nimport pandas as pd\nos.mkfifo('fifo')\ndf = pd.DataFrame()\n"
        exit_code, out, stderr = run_data(tmp_path, code)
        assert exit_code != DATA_EXIT["ok"] and out == ""
        assert "audit hook cannot see" in stderr and not (tmp_path / "fifo").exists()

    def test_a_subinterpreter_cannot_be_created(self, tmp_path: Path) -> None:
        """`_interpreters` is loaded before arming, so its import raises no event; creating an interpreter is refused."""
        code = "import _interpreters\nimport pandas as pd\ni = _interpreters.create()\ndf = pd.DataFrame({'a': [1]})\n"
        exit_code, out, stderr = run_data(tmp_path, code)
        assert exit_code != DATA_EXIT["ok"] and out == ""
        assert "audit hook cannot see" in stderr

    def test_builders_still_run(self, tmp_path: Path) -> None:
        code = (
            "import collections\nimport dataclasses\nimport pandas as pd\n"
            "P = collections.namedtuple('P', 'x y')\nD = dataclasses.make_dataclass('D', ['a'])\n"
            "rows = list(pd.DataFrame({'a': [1, 2]}).itertuples())\n"
            "df = pd.DataFrame({'x': [r.a for r in rows], 'y': [P(1, 2).y, D(3).a]})\n"
        )
        exit_code, out, stderr = run_data(tmp_path, code)
        assert exit_code == DATA_EXIT["ok"], stderr
        assert out == "x,y\n1,2\n2,3\n"

    def test_the_entry_runs_once(self) -> None:
        guard = harness.DataGuard()
        code = compile("1", "snippet.py", "eval")
        guard.armed, guard.entry = True, code
        guard("exec", (code,))
        with pytest.raises(RuntimeError):
            guard("exec", (code,))
        assert guard.blocked == "exec"

    @pytest.mark.parametrize(
        "code",
        [
            pytest.param(
                "import numpy as np\na = np.zeros(8)\nraw = a.ctypes._ctypes.string_at(a.ctypes.data, 8)\n",
                id="string_at through an array",
            ),
            pytest.param(
                "import ctypes\np = ctypes.cast(ctypes.c_char_p(b'x'), ctypes.POINTER(ctypes.c_char))\n", id="cast"
            ),
            pytest.param("import ctypes\nb = (ctypes.c_char * 4)()\nctypes.memmove(b, b'abcd', 4)\n", id="memmove"),
            pytest.param("import os, sys\nsys.remote_exec(os.getpid(), 'snippet.py')\n", id="sys.remote_exec"),
        ],
    )
    def test_native_and_remote_routes_fail_the_run(self, tmp_path: Path, code: str) -> None:
        exit_code, out, stderr = run_data(tmp_path, "import pandas as pd\n" + code + "df = pd.DataFrame({'a': [1]})\n")
        assert exit_code == DATA_EXIT["blocked"], stderr
        assert out == ""


def test_ctypes_helper_addresses_are_empty_without_ctypes(monkeypatch: pytest.MonkeyPatch) -> None:
    """An interpreter without `_ctypes` gives the plot guard no address to let through."""
    monkeypatch.setitem(sys.modules, "_ctypes", None)  # `import _ctypes` raises ImportError
    assert harness.ctypes_helper_addresses() == frozenset()


def test_subinterpreter_calls_are_replaced_in_a_module_nothing_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    """`disable_unaudited_calls` imports `_interpreters` when no one has and replaces its five calls. Run on a fresh
    import with the original module's attributes registered for restore, never by arming a guard: an audit hook
    cannot be removed from the test process."""
    original = pytest.importorskip("_interpreters")
    entries = tuple(entry for entry in harness.UNAUDITED_CALLS if entry[0] == "_interpreters")
    assert {name for _, name in entries} == {"create", "exec", "run_string", "run_func", "call"}
    for _, name in entries:
        monkeypatch.setattr(original, name, getattr(original, name))
    monkeypatch.setattr(harness, "UNAUDITED_CALLS", entries)
    monkeypatch.delitem(sys.modules, "_interpreters")

    harness.disable_unaudited_calls()

    loaded = sys.modules["_interpreters"]
    for _, name in entries:
        assert getattr(loaded, name) is harness.refused_call, name
    with pytest.raises(PermissionError, match="audit hook cannot see"):
        loaded.create()


HELPER_NAMES = ("_cast_addr", "_memmove_addr", "_memset_addr", "_string_at_addr", "_wstring_at_addr")


def helper_calls() -> dict[str, tuple[int, tuple]]:
    """`ctypes.call_function` arguments for each of ctypes' own helpers present in this interpreter."""
    import _ctypes

    names = (*HELPER_NAMES, "_memoryview_at_addr")
    return {name: (getattr(_ctypes, name), ()) for name in names if hasattr(_ctypes, name)}


@pytest.mark.parametrize(
    "make_guard",
    [
        pytest.param(lambda tmp_path: harness.DataGuard(), id="DataGuard"),
        pytest.param(lambda tmp_path: harness.ConvertGuard(), id="ConvertGuard"),
    ],
)
def test_data_and_convert_guards_refuse_every_ctypes_call(tmp_path: Path, make_guard) -> None:
    """Data mode imports scipy before it arms and neither mode imports after, so neither guard lets any foreign
    function through on Python 3.14, ctypes' own cast, memmove and memset included."""
    guard = make_guard(tmp_path)
    for name, args in helper_calls().items():
        assert guard.refuses("ctypes.call_function", args), name
    assert guard.refuses("ctypes.call_function", ())
    assert guard.refuses("sys.remote_exec", (1, "x.py"))


def test_the_plot_guard_lets_only_an_imports_cast_through(tmp_path: Path) -> None:
    """Python 3.14 raises `ctypes.call_function` for every call through a ctypes function pointer, and scipy's import
    calls `ctypes.cast`. The plot guard lets `IMPORT_CTYPES_HELPERS` through only when the caller's nearest origin is
    an import; the same cast from anywhere else, memmove, memset, string_at and every other address stay refused."""
    guard = harness.PlotGuard((str(tmp_path / "plot-light.png"),))
    calls = helper_calls()
    assert harness.IMPORT_CTYPES_HELPERS == ("_cast_addr",)
    for origin in (None, "plot"):
        guard.nearest_origin = lambda frame, origin=origin: origin
        for name, args in calls.items():
            assert guard.refuses("ctypes.call_function", args), (origin, name)
    guard.nearest_origin = lambda frame: "import"
    for name, args in calls.items():
        assert guard.refuses("ctypes.call_function", args) == (name != "_cast_addr"), name
    assert guard.refuses("ctypes.call_function", (0, ())) and guard.refuses("ctypes.call_function", ())
    assert guard.refuses("ctypes.dlopen", ("libc.so.6",))


def test_the_sandbox_flags_turn_remote_debugging_off(tmp_path: Path) -> None:
    """`INTERPRETER_FLAGS` (`-X disable-remote-debug`): `sys.remote_exec` against the interpreter's own pid is refused
    by the interpreter itself, before any guard, and the script never runs."""
    payload = tmp_path / "payload.py"
    payload.write_text(f"open({str(tmp_path / MARKER)!r}, 'w').write('x')\n", encoding="utf-8")
    code = (
        "import os, sys, time\nprint(sys.is_remote_debug_enabled())\n"
        f"try:\n    sys.remote_exec(os.getpid(), {str(payload)!r})\nexcept RuntimeError as error:\n    print(error)\n"
        "time.sleep(0.2)\n"
    )
    done = subprocess.run(
        [sys.executable, *harness.INTERPRETER_FLAGS, "-c", code], capture_output=True, text=True, timeout=60
    )
    assert done.stdout.splitlines() == ["False", "Remote debugging is not enabled"], done.stderr
    assert not (tmp_path / MARKER).exists()
