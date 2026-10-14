"""The harness's audit-hook guards against exec and process routes: `PlotGuard` (plot mode) and `DataGuard`'s
code events (data mode).

Each end-to-end case runs the real harness in a subprocess with the test interpreter, because an audit hook
can never be removed from the process that arms it. The routes are the ones the validator review of 2026-10-14
found (`np.testing.measure` compiles and execs its string), generalised: the harness is the second layer
behind the validator, so these plots and snippets are written as if the validator had missed them.
"""

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
    (tmp_path / "plot.py").write_text(HEADER + body + SAVE, encoding="utf-8")
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
    return done.returncode, done.stderr


def run_data(tmp_path: Path, code: str) -> tuple[int, str | None, str]:
    """Exit code, `out.csv` (None when missing) and stderr of one data-mode run in `tmp_path`."""
    (tmp_path / "snippet.py").write_text(code, encoding="utf-8")
    done = subprocess.run(
        [sys.executable, "-I", str(HARNESS_SOURCE), harness.DATA_FLAG, "snippet.py"],
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

    def test_a_syntax_error_is_reported_before_the_guard(self, tmp_path: Path) -> None:
        exit_code, stderr = render(tmp_path, "x = (\n")
        assert exit_code != 0 and "SyntaxError" in stderr and 'plot.py", line' in stderr


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
        for event in ("import", "os.listdir", "os.putenv", "compile", "sys._getframe", "builtins.id"):
            assert not guard.refuses(event, ()), event

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

    def test_unaudited_calls_are_replaced(self, tmp_path: Path) -> None:
        code = "import os\nimport pandas as pd\nos.mkfifo('fifo')\ndf = pd.DataFrame()\n"
        exit_code, out, stderr = run_data(tmp_path, code)
        assert exit_code != DATA_EXIT["ok"] and out == ""
        assert "audit hook cannot see" in stderr and not (tmp_path / "fifo").exists()

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
