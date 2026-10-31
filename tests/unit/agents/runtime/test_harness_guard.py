"""The harness's audit-hook guards against exec and process routes: `PlotGuard` (plot mode) and `DataGuard`'s
code events (data mode).

Each end-to-end case runs the real harness in a subprocess with the test interpreter, because an audit hook
can never be removed from the process that arms it. The routes are the ones the validator review of 2026-10-14
found (`np.testing.measure` compiles and execs its string), generalised: the harness is the second layer
behind the validator, so these plots and snippets are written as if the validator had missed them.
"""

import importlib.util
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


def import_or_skip(module: str) -> None:
    """Skip the test unless `module` imports here: `pytest.importorskip` skips only an ImportError, but cairosvg's
    import raises OSError when cairocffi finds no libcairo on the machine."""
    try:
        importlib.import_module(module)
    except (ImportError, OSError) as exc:
        pytest.skip(f"{module} does not import here: {type(exc).__name__}: {exc}")


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
NO_CSSSELECT2 = pytest.mark.skipif(
    importlib.util.find_spec("cssselect2") is None, reason="needs cssselect2 (lib-pygal)"
)


TEXT_PATH = (
    "class Text(str):\n"
    "    pass\n"
    "def _tries(name):\n"
    "    method = getattr(str, name)\n"
    "    def override(self, *args, **kwargs):\n"
    "        try:\n"
    f"            {WRITE_MARKER}\n"
    "        except OSError:\n"
    "            pass\n"
    "        return method(self, *args, **kwargs)\n"
    "    return override\n"
    "for _name in ('split', 'rsplit', 'startswith', 'endswith', 'partition', 'rpartition', 'rstrip', 'lstrip', 'strip',\n"
    "              '__getitem__', '__add__', '__eq__', '__hash__', '__contains__', '__len__', '__iter__', 'find', 'rfind',\n"
    "              'join', 'replace', '__str__', '__format__', 'removesuffix', 'count', 'encode', '__fspath__'):\n"
    "    if hasattr(str, _name):\n"
    "        setattr(Text, _name, _tries(_name))\n"
)
"""A `str` subclass every method of which tries to write the marker: armed, the guard refuses the write; paused, it
would pass. A path of this class may reach the guard's own path handling."""
DISARMING_PAYLOAD = (
    "import sys\n"
    "frame = sys._getframe(0)\n"
    "while frame is not None:\n"
    "    for value in list(frame.f_locals.values()):\n"
    "        if hasattr(value, 'armed') and hasattr(value, 'outputs'):\n"
    "            value.armed = False\n"
    "    frame = frame.f_back\n"
    f"{WRITE_MARKER}\n"
)
"""Module source a plot hands the import machinery (F6): with an import's trust it reads the frames up to the guard,
disarms it and writes the marker."""
STOCK_LOADER = (
    "import importlib, importlib.abc, os\n"
    "import importlib.machinery as machinery\n"
    "import importlib.util as util\n"
    f"PAYLOAD = {DISARMING_PAYLOAD!r}\n"
    "def write_source(name):\n"
    "    path = os.path.abspath(name)\n"
    "    open(path, 'w').write(PAYLOAD)\n"
    "    return path\n"
)
"""The F6 routes' preamble: the machinery's modules and `write_source`, which puts the payload into an output file the
guard lets the plot write and returns its absolute path."""
RUN_LOADER = "loader.exec_module(util.module_from_spec(util.spec_from_loader('evil', loader)))\n"


def forged_selector(payload: str) -> str:
    """A plot body that hands cssselect2's compiler Python objects in place of tokens: a `dimension` whose `int_value`
    is `payload` lands unquoted in the `eval` text `CompiledSelector.__init__` builds (`CODE_BUILDERS`), and the
    lambda runs it when it tests an element (the pygal spike of 2026-10-26; without a guard it writes the marker)."""
    return (
        f"import cssselect2.compiler as compiler\nPAYLOAD = {payload!r}\n"
        "class Token:\n    def __init__(self, **fields):\n        self.__dict__.update(fields)\n"
        "    def __eq__(self, other):\n        return other == self.__dict__.get('eq')\n"
        "dimension = Token(type='dimension', is_integer=True, lower_unit='n', int_value=PAYLOAD)\n"
        "nth = Token(type='function', lower_name='nth-child', arguments=[dimension], value=None)\n"
        "[selector] = compiler.compile_selector_list([Token(type='literal', value=':', eq=':'), nth])\n"
        "class Element:\n    index = 0\nselector.test(Element())\n"
    )


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
    # PB-1's review of the paused paths (2026-10-31): `writes_elsewhere` ran `realpath` on the event's path with the
    # guard paused, and a `str` subclass's `split` and `startswith` wrote the marker there; every method of `Text` tries.
    pytest.param(TEXT_PATH + "open(Text('/tmp/escape'), 'w')\n", id="a str subclass path to open"),
    pytest.param(
        TEXT_PATH + "import os\nos.open(Text('/tmp/escape'), os.O_WRONLY | os.O_CREAT)\n", id="... to os.open"
    ),
    pytest.param(
        TEXT_PATH + "class P:\n    def __fspath__(self):\n        return Text('/tmp/escape')\nopen(P(), 'w')\n",
        id="a path object that returns one",
    ),
    # F6 of PB-1's review (Fable, 2026-10-31): the import machinery driven by the plot. A module body the plot supplies
    # would run with an import's trust, read the frames up to the guard, disarm it and write the marker.
    pytest.param(
        STOCK_LOADER + "loader = machinery.SourceFileLoader('evil', write_source('plot-light.html'))\n" + RUN_LOADER,
        id="a stock source loader on a file the plot wrote",
    ),
    pytest.param(
        STOCK_LOADER + "loader = type(np.__loader__)('evil', write_source('plot-light.html'))\n" + RUN_LOADER,
        id="the loader class of an admitted module",
    ),
    pytest.param(
        STOCK_LOADER
        + "import marshal\npath = os.path.abspath('plot-light.png')\n"
        + "code = marshal.dumps(compile(PAYLOAD, 'evil', 'exec'))\n"
        + "open(path, 'wb').write(util.MAGIC_NUMBER + bytes(12) + code)\n"
        + "loader = machinery.SourcelessFileLoader('evil', path)\n"
        + RUN_LOADER,
        id="a stock bytecode loader on a file the plot wrote",
    ),
    pytest.param(
        STOCK_LOADER
        + "import zipfile, zipimport\npath = os.path.abspath('plot-light.png')\n"
        + "with zipfile.ZipFile(path, 'w') as archive:\n    archive.writestr('evil.py', PAYLOAD)\n"
        + "spec = zipimport.zipimporter(path).find_spec('evil')\nspec.loader.exec_module(util.module_from_spec(spec))\n",
        id="zipimport on an archive the plot wrote",
    ),
    pytest.param(
        STOCK_LOADER
        + "class Loader(importlib.abc.SourceLoader):\n"
        + "    def get_filename(self, name):\n        return os.__file__\n"
        + "    def get_data(self, path):\n        return PAYLOAD.encode()\n"
        + "loader = Loader()\n"
        + RUN_LOADER,
        id="a loader of the plot's own (Fable's proof of concept)",
    ),
    pytest.param(
        STOCK_LOADER
        + "loader = machinery.SourceFileLoader('evil', os.path.join(os.path.dirname(os.__file__), 'colorsys.py'))\n"
        + "loader.get_code = lambda name: compile(PAYLOAD, loader.path, 'exec')\n"
        + RUN_LOADER,
        id="a stock loader whose instance overrides get_code",
    ),
    pytest.param(
        STOCK_LOADER + "import sys\nsys.path_hooks.insert(0, exec)\nsys.path.insert(0, PAYLOAD)\n"
        "try:\n    importlib.import_module('anyplot_no_such_module')\nexcept ImportError:\n    pass\n",
        id="exec as a path hook",
    ),
    pytest.param(
        STOCK_LOADER
        + "import numpy.random.mtrand as native\n"
        + "open('plot-light.png', 'wb').write(open(native.__file__, 'rb').read())\n"
        + "loader = machinery.ExtensionFileLoader('mtrand', os.path.abspath('plot-light.png'))\n"
        + "util.module_from_spec(util.spec_from_file_location('mtrand', loader.path, loader=loader))\n",
        id="an extension module the plot wrote",
    ),
    pytest.param(
        "import pkgutil\nraw = pkgutil.get_data('matplotlib', '../../../../../../../../etc/hostname')\n",
        id="pkgutil.get_data past its package",
    ),
    # Flash's review of PB-1: stdout and stderr are one open file description across figure mode's fork.
    pytest.param("import fcntl, os\nfcntl.fcntl(1, fcntl.F_SETFL, os.O_NONBLOCK)\n", id="fcntl on stdout"),
    pytest.param("import os\nos.set_blocking(1, False)\n", id="os.set_blocking on stdout"),
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
    # cssselect2's compiler is a `CODE_BUILDERS` entry (pygal's PNG export): an `__init__` anywhere else is not it,
    # and code its `eval` built runs under the guard like the plot's own.
    pytest.param(
        f'class Builder:\n    def __init__(self):\n        exec("{WRITE_MARKER}")\nBuilder()\n',
        id="exec from an __init__ that is not cssselect2's",
    ),
    pytest.param(
        forged_selector(f"1) and {WRITE_MARKER} or (1"),
        id="a forged cssselect2 token writes from the built lambda",
        marks=NO_CSSSELECT2,
    ),
    pytest.param(
        forged_selector(f'1) and exec("{WRITE_MARKER}") or (1'),
        id="a forged cssselect2 token execs from the built lambda",
        marks=NO_CSSSELECT2,
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

    def test_imports_from_the_install_still_run_under_the_guard(self, tmp_path: Path) -> None:
        """F6's rules keep every import of the interpreter's own loaders: a site package with extension modules and an
        import-time `ctypes.cast` (scipy.stats), a stdlib module with an extension of `lib-dynload` (lzma), a stdlib
        package (zoneinfo) and a frozen module (`__hello__`), each imported first with the guard armed."""
        exit_code, stderr = render(tmp_path, "import scipy.stats\nimport lzma\nimport zoneinfo\nimport __hello__\n")

        assert exit_code == 0, stderr[-2000:]
        assert (tmp_path / "plot-light.png").stat().st_size > 0

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

    @pytest.mark.parametrize(
        ("imports", "size", "save"),
        [
            pytest.param("", (400, 300), "chart.render_to_png(f'plot-{THEME}.png')\n", id="render_to_png"),
            pytest.param(
                "import cairosvg\n",
                (600, 450),
                "cairosvg.svg2png(bytestring=chart.render(), write_to=f'plot-{THEME}.png', output_width=400, "
                "output_height=300)\n",
                id="svg2png, the canvas rewrite's form",
            ),
        ],
    )
    def test_pygal_renders_its_png_and_html(
        self, tmp_path: Path, imports: str, size: tuple[int, int], save: str
    ) -> None:
        """pygal's PNG goes through cairosvg: `warm_cairo` loads libcairo before the guard, and cssselect2 compiles the
        chart's stylesheet into lambdas through `eval` (`CODE_BUILDERS`). No matplotlib figure, so no probe."""
        pytest.importorskip("pygal")
        import_or_skip("cairosvg")
        code = (
            f"import os\n\n{imports}import pygal\n\nTHEME = os.environ['ANYPLOT_THEME']\n"
            f"chart = pygal.Bar(width={size[0]}, height={size[1]}, title='t')\nchart.add('y', [1, 3, 2])\n"
            f"{save}chart.render_to_file(f'plot-{{THEME}}.html')\n"
        )
        exit_code, stderr = render_file(tmp_path, code)
        assert exit_code == 0, stderr[-3000:]
        assert "blocked by the" not in stderr
        png = (tmp_path / "plot-light.png").read_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", png[16:24]) == (400, 300)
        assert "<svg" in (tmp_path / "plot-light.html").read_text(encoding="utf-8")
        assert not (tmp_path / "probe-light.json").exists()

    LETS_PLOT = (
        "import os\n\nimport pandas as pd\nfrom lets_plot import LetsPlot, aes, geom_point, ggplot, ggsize\n"
        "from lets_plot.export import ggsave\n\nLetsPlot.setup_html()\nTHEME = os.environ['ANYPLOT_THEME']\n"
        "df = pd.DataFrame({'x': ['a', 'b', 'c'], 'y': [1.0, 3.0, 2.0]})\n"
        "plot = ggplot(df, aes(x='x', y='y')) + geom_point() + ggsize(200, 150)\n"
    )

    def test_lets_plot_renders_its_png_and_html(self, tmp_path: Path) -> None:
        """lets-plot rasterises in its native bridge, loaded at import: the guard needs no entry for it, and the two
        files `path="."` names are the only writes. No matplotlib figure, so no probe."""
        pytest.importorskip("lets_plot")
        code = self.LETS_PLOT + (
            "ggsave(plot, f'plot-{THEME}.png', path='.', scale=2)\nggsave(plot, f'plot-{THEME}.html', path='.')\n"
        )
        exit_code, stderr = render_file(tmp_path, code)
        assert exit_code == 0, stderr[-3000:]
        assert "blocked by the" not in stderr
        png = (tmp_path / "plot-light.png").read_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", png[16:24]) == (400, 300)
        assert "data-lets-plot-script" in (tmp_path / "plot-light.html").read_text(encoding="utf-8")
        assert not (tmp_path / "probe-light.json").exists()

    def test_a_lets_plot_save_without_path_is_refused(self, tmp_path: Path) -> None:
        """Without `path=`, `ggsave` creates `./lets-plot-images` (`os.mkdir`), which the guard refuses; the
        normaliser adds `path="."` to every save."""
        pytest.importorskip("lets_plot")
        exit_code, stderr = render_file(tmp_path, self.LETS_PLOT + "ggsave(plot, f'plot-{THEME}.png', scale=2)\n")
        assert exit_code != 0 and "blocked by the render sandbox: os.mkdir" in stderr, stderr[-2000:]
        assert not (tmp_path / "lets-plot-images").exists() and not (tmp_path / "plot-light.png").exists()

    def test_a_cssselect2_selector_compiles_and_runs_under_the_guard(self, tmp_path: Path) -> None:
        """`CompiledSelector.__init__` builds each selector's test with `eval` (`CODE_BUILDERS`), and the lambda it
        built runs under the guard like any plot code."""
        pytest.importorskip("cssselect2")
        body = (
            "import xml.etree.ElementTree as ET\n\nimport cssselect2\n\n"
            "[selector] = cssselect2.compile_selector_list('rect.a')\n"
            "root = cssselect2.ElementWrapper.from_xml_root(ET.fromstring('<svg><rect class=\"a\"/><g/></svg>'))\n"
            "assert [element.local_name for element in root.iter_subtree() if selector.test(element)] == ['rect']\n"
        )
        exit_code, stderr = render(tmp_path, body)
        assert exit_code == 0, stderr[-3000:]
        assert "blocked by the" not in stderr

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


@pytest.mark.parametrize("error", [ModuleNotFoundError("No module named 'cairosvg'"), OSError("no library called")])
def test_a_library_that_does_not_import_skips_its_case(monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
    """A missing module and a missing libcairo under an installed cairosvg (cairocffi's OSError) both skip."""

    def fail(name: str) -> None:
        raise error

    monkeypatch.setattr(importlib, "import_module", fail)
    with pytest.raises(pytest.skip.Exception, match=type(error).__name__):
        import_or_skip("cairosvg")


REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOGUE_UNDER_GUARD = [
    pytest.param("ice-basic", "matplotlib", id="ice-basic/matplotlib: scikit-learn GradientBoostingRegressor"),
    pytest.param("mosaic-categorical", "matplotlib", id="mosaic-categorical/matplotlib: a statsmodels graphic"),
    pytest.param("line-arrhenius", "matplotlib", id="line-arrhenius/matplotlib: mathtext"),
    pytest.param("silhouette-basic", "seaborn", id="silhouette-basic/seaborn: KMeans"),
    pytest.param("scatter-basic", "plotnine", id="scatter-basic/plotnine: aes through Environment.capture"),
    pytest.param("scatter-basic", "altair", id="scatter-basic/altair: vl-convert, PIL padding and the HTML"),
    pytest.param("scatter-basic", "pygal", id="scatter-basic/pygal: cairosvg, cssselect2 and the HTML"),
    pytest.param("line-basic", "pygal", id="line-basic/pygal: a 4800x2700 chart saved through svg2png at 3200x1800"),
    pytest.param("scatter-basic", "letsplot", id="scatter-basic/letsplot: the native bridge and the HTML"),
]
LIBRARY_MODULES = {
    "seaborn": ("seaborn",),
    "plotnine": ("plotnine",),
    "altair": ("altair", "vl_convert"),
    "pygal": ("pygal", "cairosvg"),
    "letsplot": ("lets_plot",),
}
"""The modules a library's catalogue case needs beyond matplotlib's stack; CI's test environment installs none."""
WITHOUT_PROBE = frozenset({"altair", "pygal", "letsplot"})
"""The libraries that draw no matplotlib figure, so their runs write no probe but an HTML twin."""
ON_CANVAS = frozenset({"pygal", "letsplot"})
"""The libraries whose cases the normaliser's canvas rewrite holds to 3200x1800 (the 1c decisions)."""


@pytest.mark.parametrize(("spec_id", "library"), CATALOGUE_UNDER_GUARD)
def test_catalogue_files_render_under_the_guard(tmp_path: Path, spec_id: str, library: str) -> None:
    """Real catalogue files, normalised as a session opening does, render under the plot guard: a guard change that
    breaks scikit-learn, statsmodels, mathtext, plotnine's frame read, altair's vl-convert, pygal's cairosvg or
    lets-plot's bridge fails here. The seaborn, plotnine, altair, pygal and lets-plot cases need their libraries, which
    CI's test environment does not install; the renderer-image job of `ci-image.yml` renders all five through the
    harness in the image. altair, pygal and lets-plot draw no matplotlib figure, so their runs write no probe: the PNG
    and its HTML twin are what the case checks."""
    from agents.anyplot.code.normalise import normalise
    from core.utils import strip_noqa_comments

    for module in LIBRARY_MODULES.get(library, ()):
        import_or_skip(module)
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
    if library in WITHOUT_PROBE:
        assert (tmp_path / "plot-light.html").exists()
    else:
        assert (tmp_path / "probe-light.json").exists()
    if library in ON_CANVAS:
        assert struct.unpack(">II", (tmp_path / "plot-light.png").read_bytes()[16:24]) == (3200, 1800)


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

    def test_cssselect2s_compiler_builds_code_and_nothing_else_of_it_does(self) -> None:
        """The entry is the compiler's `CompiledSelector.__init__` alone: another function of the file, an `__init__`
        elsewhere and a directory that merely ends in the package name do not match."""

        def frame(path: str, name: str) -> object:
            code = type("Code", (), {"co_filename": path, "co_name": name})
            return type("Frame", (), {"f_code": code, "f_back": None})

        site = "/app/.venv/lib/python3.14/site-packages"
        assert ("cssselect2/compiler.py", "__init__") in harness.CODE_BUILDERS
        assert harness.builds_code(frame(f"{site}/cssselect2/compiler.py", "__init__"))
        assert not harness.builds_code(frame(f"{site}/cssselect2/compiler.py", "compile_selector_list"))
        assert not harness.builds_code(frame("plot.py", "__init__"))
        assert not harness.builds_code(frame(f"{site}/not_cssselect2/compiler.py", "__init__"))

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


class TestPlotModeHelpers:
    """The helpers plot mode installs, called in this process (the render tests see them only through the sandbox)."""

    def test_frame_for_readers_answers_the_caller_frame_or_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`inspect.currentframe` in plot mode: the caller's frame while the guard lets `sys._getframe` through,
        None when it refuses, because the callers expect a frame or None and never an error."""
        frame = harness.frame_for_readers()
        assert frame is not None and frame.f_code.co_name == "test_frame_for_readers_answers_the_caller_frame_or_none"

        def refused(depth: int = 0) -> None:
            raise PermissionError("blocked by the render sandbox: sys._getframe")

        with monkeypatch.context() as patched:
            patched.setattr(harness.sys, "_getframe", refused)
            assert harness.frame_for_readers() is None

    def test_the_probe_attaches_an_agg_canvas_to_a_bare_figure(self) -> None:
        """plotnine saves a figure it built with `Figure()`, whose base canvas has no renderer: `_renderer` switches
        it to Agg as `savefig` would, and leaves a figure that has an Agg canvas on it."""
        from matplotlib.backends.backend_agg import FigureCanvasAgg, RendererAgg
        from matplotlib.figure import Figure

        bare = Figure()
        assert not hasattr(bare.canvas, "get_renderer")
        renderer = harness._renderer(bare)
        assert isinstance(bare.canvas, FigureCanvasAgg) and isinstance(renderer, RendererAgg)

        with_agg = Figure()
        canvas = FigureCanvasAgg(with_agg)
        assert harness._renderer(with_agg) is canvas.get_renderer() and with_agg.canvas is canvas


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

    def test_the_traceback_is_read_without_the_snippets_code(self, tmp_path: Path) -> None:
        """`print_snippet_error` reads the traceback with the guard paused: through `exc.__traceback__`, a property of
        the snippet's exception class ran there and wrote the marker under the armed guard (F1 of PB-1, 2026-10-31).
        `BaseException`'s own descriptor never calls it."""
        code = (
            "class Escape(Exception):\n"
            "    @property\n"
            "    def __traceback__(self):\n"
            "        try:\n"
            f"            {WRITE_MARKER}\n"
            "        except RuntimeError:\n"
            "            pass\n"
            "        return None\n"
            "\n"
            "raise Escape('boom')\n"
        )
        exit_code, out, stderr = run_data(tmp_path, code)

        assert exit_code == DATA_EXIT["error"], stderr
        assert out == "" and not (tmp_path / MARKER).exists()
        assert 'File "snippet.py", line 10, in <module>' in stderr
        assert stderr.strip().splitlines()[-1] == "__main__.Escape: boom"

    def test_the_message_runs_armed(self, tmp_path: Path) -> None:
        """The exception's message is the snippet's code too (`__str__`): it runs with the guard armed."""
        code = f"class Escape(Exception):\n    def __str__(self):\n        {WRITE_MARKER}\n        return 'x'\n\nraise Escape()\n"
        exit_code, out, stderr = run_data(tmp_path, code)

        assert exit_code == DATA_EXIT["blocked"], stderr
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


class TestImportMachinery:
    """What an import must look like for the plot guard to trust it (`harness.ImportMachinery`, F6 of PB-1's review);
    the routes above run the same rules armed."""

    STDLIB_FILE = str(Path(json.__file__).parent.parent / "colorsys.py")

    def test_the_install_holds_the_stdlib_and_the_site_packages_and_not_the_run(self, tmp_path: Path) -> None:
        prefixes = harness.install_prefixes()
        assert harness.under_prefixes(self.STDLIB_FILE, prefixes)
        assert harness.under_prefixes(pytest.__file__, prefixes)
        assert not harness.under_prefixes(str(tmp_path / "plot-light.html"), prefixes)
        assert not harness.under_prefixes("/tmp/evil.py", prefixes)
        (tmp_path / "link.py").symlink_to(self.STDLIB_FILE)
        assert harness.under_prefixes(str(tmp_path / "link.py"), prefixes)  # its real path is the stdlib's
        (tmp_path / "out.py").write_text("x = 1\n", encoding="utf-8")
        climbing = str(Path(self.STDLIB_FILE).parent) + "/.." * 20 + str(tmp_path / "out.py")
        assert not harness.under_prefixes(climbing, prefixes)  # starts with a prefix, resolves outside

    def test_only_an_exact_stock_loader_of_the_install_is_trusted(self, tmp_path: Path) -> None:
        import importlib.abc
        import importlib.machinery
        import zipimport

        machinery = harness.ImportMachinery()
        stock = importlib.machinery.SourceFileLoader("colorsys", self.STDLIB_FILE)
        assert machinery.trusted_loader(stock)

        class Subclass(importlib.machinery.SourceFileLoader):
            pass

        class Own(importlib.abc.SourceLoader):
            def get_filename(self, name: str) -> str:
                return "colorsys.py"

            def get_data(self, path: str) -> bytes:
                return b""

        overridden = importlib.machinery.SourceFileLoader("colorsys", self.STDLIB_FILE)
        overridden.get_code = lambda name: None  # type: ignore[method-assign]
        assert not machinery.trusted_loader(Subclass("colorsys", self.STDLIB_FILE))
        assert not machinery.trusted_loader(Own())
        assert not machinery.trusted_loader(overridden)
        assert not machinery.trusted_loader(importlib.machinery.SourceFileLoader("x", str(tmp_path / "x.py")))
        assert not machinery.trusted_loader(object())
        archive = tmp_path / "evil.zip"
        import zipfile

        with zipfile.ZipFile(archive, "w") as handle:
            handle.writestr("evil.py", "x = 1\n")
        assert not machinery.trusted_loader(zipimport.zipimporter(str(archive)))

    def test_only_the_interpreters_own_import_frames_earn_trust(self) -> None:
        machinery = harness.ImportMachinery()

        def frame(code: object, back: object = None, local_self: object = None) -> object:
            return type("Frame", (), {"f_code": code, "f_back": back, "f_locals": {"self": local_self}})

        import importlib.machinery

        stock = importlib.machinery.SourceFileLoader("colorsys", self.STDLIB_FILE)
        exec_module = frame(next(iter(machinery.loader_entries)), local_self=stock)
        assert machinery.trusts(frame(machinery.trampoline, back=exec_module))
        assert machinery.trusts(frame(machinery.frozen_exec))
        assert machinery.trusts(frame(machinery.trampoline, back=frame(next(iter(machinery.static_entries)))))
        assert not machinery.trusts(frame(machinery.trampoline, back=frame((lambda: 0).__code__)))
        assert not machinery.trusts(frame(machinery.trampoline))
        assert not machinery.trusts(frame((lambda: 0).__code__))  # `_path_hooks`, `_find_spec` and the like
        untrusted = frame(next(iter(machinery.loader_entries)), local_self=object())
        assert not machinery.trusts(frame(machinery.trampoline, back=untrusted))


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
