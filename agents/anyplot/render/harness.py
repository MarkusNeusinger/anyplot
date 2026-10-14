"""Render harness: runs one plot file inside the sandbox with resource limits and a savefig probe.

Usage, from the run directory (the CI render command with the harness in front):

    python -I /opt/anyplot/harness.py plot.py

It is a standalone script with no anyplot import, because it runs inside the
sandbox with the isolated interpreter (`-I`: no user site, no current directory on
`sys.path`, no `PYTHON*` environment). The renderer service
(`agents/renderer/`) and the local Docker backend both run it; the renderer's image
copies it to `/opt/anyplot/harness.py`. In order it:

1. prints `HARNESS {"event": "start"}` on stdout before anything else, so the host
   can tell a harness that ran (and failed in the plot code) from a launcher that
   never started it; the renderer retries only the second kind;
2. sets resource limits, soft and hard alike so the code cannot raise them again:
   CPU seconds (`ANYPLOT_RLIMIT_CPU_S`, default 60), the largest file it may write
   (`ANYPLOT_RLIMIT_FSIZE_MB`, default 32) and, only when set, the address space
   (`ANYPLOT_RLIMIT_AS_MB`) and the number of processes (`ANYPLOT_RLIMIT_NPROC`).
   The last two are opt-in because outside a sandbox they bind the whole user:
   `RLIMIT_NPROC` counts every process of the real user id on a developer machine;
3. when `ANYPLOT_MPL_SEED` names a directory, copies it into `MPLCONFIGDIR`, so
   matplotlib starts from the font cache baked into the image instead of
   rebuilding it in the sandbox's empty private `/tmp` (spike S measured the copy
   as the faster variant); then appends the installed fallback families
   (`FALLBACK_FAMILIES`) to every font lookup after the font the code chose, so
   text in the installed scripts draws without changing the catalogue's first
   font, and records every code point matplotlib reports as having no glyph
   (`missing_glyphs` in the probe);
4. wraps `matplotlib.figure.Figure.savefig` so that every save also writes
   `probe-<theme>.json` next to the plot: the figure size and dpi, the bounding
   boxes in display pixels of the texts the probe's own draw rendered (it measures
   the first `PROBE_MEASURE_LIMIT` in draw order and keeps at most `PROBE_LIMIT`,
   the ones past a canvas edge first; `texts_total` counts every drawn text), overlaps
   between the measured tick labels per axis, overlaps of every other measured text
   (axis labels, titles, legend texts, annotations) with any measured text by more
   than `TEXT_OVERLAP_TOLERANCE_PX` (`text_overlaps`, the deepest pairs by role, and
   `text_overlaps_total`), annotations outside their axes, the
   number of drawn point marks (scatter offsets) and the number of vertices of the
   visible `plot()` lines (`line_points`). Only rendered text counts: matplotlib keeps tick
   labels for locator positions outside the view interval and for hidden axes
   (`axis("off")`, a twin's), which report themselves visible but are never drawn,
   and an edge label one tick step past the view sat beyond the canvas in every
   line plot of spike X (a false G3); for a figure with polar axes, `polar` adds each
   one's radial-label angle, its visible theta span and a histogram of the plotted
   points by angle and radius (`polar_report`), from which the host computes the free direction for the
   radial labels (`agents/anyplot/render/polar.py`);
5. compiles the plot file and runs it as `__main__` (`run_plot`, which `runpy.run_path`
   did before) under `PlotGuard`, an audit hook armed just before: from there on the
   interpreter refuses every `exec` but the plot's own run, the module bodies of an import
   and `CODE_BUILDERS` (`namedtuple`, dataclasses, scipy's distributions), a code object or
   function built by hand or a `__code__` assignment, every `open` that writes anything but
   `plot-<theme>.png` and `probe-<theme>.json`, `subprocess.*`, `os.system`, `os.exec*`,
   `os.posix_spawn`, `os.spawn*`, `os.fork*`, `socket.*`, `ctypes.*` (but threadpoolctl's,
   `NATIVE_CALLERS`), filesystem changes and `os.chdir`. Imports, reads and `compile` stay
   allowed, because the plot imports its libraries lazily and matplotlib reads fonts and
   style sheets and compiles colour strings while it draws; a refusal raises
   `PermissionError`. The validator review of 2026-10-14 found `np.testing.measure`, which
   compiles and runs any string, past the validator: this is the layer behind it. A sweep
   of the 650 catalogue matplotlib and seaborn files rendered all 474 the validator passes
   under the guard (the seven it newly failed are ones the validator refuses: a fetch, a
   `chdir`, `load_dataset`);
6. prints `HARNESS {"event": "end", "max_rss_mb": ..., "cpu_s": ...}` when the plot
   file returns or raises; an exception still propagates, so its traceback reaches
   stderr and the exit code stays non-zero.

**Data mode** (`python -I /opt/anyplot/harness.py --data snippet.py`, the renderer's
`POST /run-data`): the harness runs a data-generating snippet (`run_data_code`,
`agents/anyplot/tools/session.py`) instead of a plot. It prints the start line, sets the
same limits, imports everything the validator's DATA profile allows (`DATA_PRELOAD`, every
module of `pandas.core`, `pandas.tseries` and `pandas.api`, which pandas would otherwise
load lazily, and every time zone), reads and compiles the snippet, opens `out.csv` for
writing, and only then arms `DataGuard` with `sys.addaudithook`: from there on the
interpreter refuses every `open` (reading too) and every `import`, `ctypes.*`,
`os.system`, `os.exec*`, `os.posix_spawn`, `os.spawn*`, `os.fork*`, `subprocess.*`,
`socket.*`, every filesystem change and listing (`os.remove`, `os.listdir`,
`os.scandir`, ...), every route to a frame (`gi_frame`, `cr_frame`, `ag_frame`,
`tb_frame`, `sys._getframe`), whose `f_builtins` would hand out `open` and `__import__`
past the validator (Fable review of 2026-10-14), and every `exec` and `compile` but the
snippet's own run and `CODE_BUILDERS` (validator review of 2026-10-14). An audit hook cannot be removed, and the
snippet cannot reach it. It runs the snippet with `exec`, catches everything it raises
(the frames and the exception line go to stderr, the exit code is
`DATA_EXIT["error"]`, so the snippet cannot choose an exit code), and
takes `df` from the returned globals: a pandas DataFrame whose columns are no
MultiIndex, with a non-default index turned into columns (`reset_index`), its column
names as text, at most `DATA_MAX_ROWS` rows and `DATA_MAX_COLUMNS` columns and at most
`DATA_MAX_CSV_BYTES` of CSV (the parser's caps for computed data: `agents/anyplot/schemas.py`
and `data/parse.py` `MAX_COMPUTED_BYTES`, 2 MiB, twice the 1 MiB paste cap; a test pins them equal). It writes the CSV through the handle it opened
before the guard; a run the guard refused at any point writes nothing, even when the
snippet caught the error. Each refusal has its own exit code (`DATA_EXIT`); the host
maps a code to a fixed message and trusts nothing the snippet printed. The same code,
with the measured value and the cap for a broken row, column or byte cap, also goes to
`status.json` (opened before the guard, written last), because Cloud Run's sandbox
launcher reports every non-zero exit as its own SIGPIPE (-13) and so loses the code. The plot mode
arms `PlotGuard` instead (step 5), which lets imports and reads through and refuses with
`PermissionError`, so a plot that catches a refusal renders without what was refused.

The probe feeds the advisory gates G3 (clipped text), G5 (annotation outside its
axes), G7 (overlapping text: tick labels among themselves, any other text with any), G8 (more point marks than data rows), G9 (more
plotted points than any dataset within the parser's caps can hold) and G10
(characters without a glyph in any font of the text). It is
advisory because the code under test could tamper with it; the host never fails a
render on it. The same holds for the `HARNESS` lines: the code under test shares
stdout, so the host reads them as hints (a retry decision, a memory figure), never
as a verdict.
"""

import functools
import io
import itertools
import json
import logging
import math
import os
import resource
import shutil
import sys
import traceback


PROBE_LIMIT = 400  # text boxes recorded per figure
PROBE_MEASURE_LIMIT = 2_000
"""Texts the probe measures per figure, in draw order. Each `get_window_extent` costs CPU time
under the sandbox's `RLIMIT_CPU`, on top of the three full draws a render already pays (the
probe's, the save's and pyplot's trailing one): measured on WSL2, the extents of 2,000 labels
took 0.07 s and those of 20,000 took 6.5 s, past matplotlib's text-metrics cache. A clipped
text drawn after the first 2,000 is not seen by G3, nor a tick label by G7: G7 reuses these
extents and measures none of its own. G5 reuses them too and measures the annotations
missing from them, at most this many again: matplotlib draws no annotation whose point
lies outside the view, which is the case G5 is there for."""
TEXT_OVERLAP_TOLERANCE_PX = 3.0
"""How deep (in the saved image's pixels, on a 3200 x 1800 canvas) two texts must overlap before
G7 names them: the ink of a glyph sits inside its box, so boxes that share a few pixels at a
corner or an edge (a title on its axes' top tick label, an axis label beside its ticks) do not
touch on the canvas. The owner's polar case overlapped by far more than this."""
TEXT_OVERLAP_CANDIDATES = 200  # texts other than tick labels compared with every measured text
TEXT_OVERLAP_LIMIT = 5  # the deepest pairs the probe reports
THEME_ENV = "ANYPLOT_THEME"
MARKER = "HARNESS"
FALLBACK_FAMILIES = (
    "Noto Sans",  # Latin, Greek and Cyrillic the code's serif or monospace choice may lack
    "Noto Sans CJK JP",  # Chinese, Japanese, Korean: every CJK code point in one face (the TTC's first)
    "Noto Sans Arabic",  # Arabic, Persian, Urdu (DejaVu Sans lacks the Urdu letters)
    "Noto Sans Hebrew",
    "Noto Sans Devanagari",
    "Noto Sans Bengali",
    "Noto Sans Tamil",
    "Noto Sans Telugu",
    "Noto Sans Gujarati",
    "Noto Sans Gurmukhi",
    "Noto Sans Kannada",
    "Noto Sans Malayalam",
    "Noto Sans Sinhala",
    "Noto Sans Thai",
    "Noto Sans Khmer",
    "Noto Sans Myanmar",
    "Noto Sans Ethiopic",
    "Noto Sans Symbols",
    "Noto Sans Symbols2",
)
"""The families appended to every font lookup, after the font the code chose, in this order. Each
name is the name-table family of a file the renderer image installs (agents/renderer/Dockerfile,
stage `fonts`); `check_fonts` fails the image build when one is missing, and a family that is not
installed where the harness runs (a developer machine) is skipped without a `findfont` warning.
One CJK face is enough: the five regional faces share one character map and differ only in the
default forms of shared Han characters; JP is the TTC's first face, and the forms follow
`text.language` once a caller sets it (not yet: see the agent-network doc)."""
POLAR_BIN_DEG = 5  # width of one angle bin of the plotted points in the probe's `polar` field
POLAR_RINGS = 10  # radius bins: tenths of the visible radius range, centre to edge
POLAR_AXES_LIMIT = 4  # polar axes the probe describes per figure
GLYPH_SAMPLE_LIMIT = 16  # code points the probe lists; the host shows a few of them
MISSING_GLYPHS: set[int] = set()  # code points reported by matplotlib's text layout, this process
MISSING_MATH_GLYPHS: set[int] = set()  # code points reported by mathtext (no fallback inside `$…$`)

DATA_FLAG = "--data"
DATA_OUT_FILE = "out.csv"
DATA_STATUS_FILE = "status.json"
"""The data run's outcome for the host (`write_status`): `{"exit", "reason", "measured"?, "limit"?}`."""
DATA_MAX_ROWS = 20_000  # agents/anyplot/schemas.py MAX_ROWS
DATA_MAX_COLUMNS = 50  # agents/anyplot/schemas.py MAX_COLUMNS
DATA_MAX_CSV_BYTES = 2 * 1024 * 1024  # agents/anyplot/data/parse.py MAX_COMPUTED_BYTES (pastes take 1 MiB)
DATA_EXIT = {
    "ok": 0,
    "error": 1,
    "usage": 2,
    "no_frame": 3,
    "frame_shape": 4,
    "too_many_rows": 5,
    "too_many_columns": 6,
    "too_large": 7,
    "blocked": 8,
}
"""Exit codes of data mode: `error` is an exception in the snippet (its traceback on stderr), `no_frame` no `df`
or one that is no DataFrame, `frame_shape` MultiIndex columns or an index that cannot become columns,
`blocked` an operation `DataGuard` refused."""
DATA_BLOCKED_PREFIXES = (
    "ctypes.",
    "os.system",
    "os.exec",
    "os.posix_spawn",
    "os.spawn",
    "os.fork",
    "os.kill",
    "os.killpg",
    "os.remove",
    "os.rename",
    "os.rmdir",
    "os.mkdir",
    "os.symlink",
    "os.link",
    "os.chmod",
    "os.chown",
    "os.chflags",
    "os.truncate",
    "os.utime",
    "os.putenv",
    "os.unsetenv",
    "subprocess.",
    "socket.",
    "shutil.",
    "pty.",
    "webbrowser.",
    "urllib.Request",
    "http.client.",
    "ftplib.",
    "smtplib.",
    "sys.addaudithook",
    "resource.setrlimit",
    "resource.prlimit",
    "sys._getframe",
    "sys._current_frames",
    "sys._current_exceptions",
    "os.listdir",
    "os.scandir",
    "os.chdir",
    "os.listxattr",
    "os.getxattr",
    "glob.",
    "marshal.",
    "pickle.",
    "code.__new__",
    "function.__new__",
    "builtins.input",
)
"""Audit events `DataGuard` refuses once it is armed (https://docs.python.org/3/library/audit_events.html), next to
every `open` and every `import`. CPython 3.13 raises no event for `os.stat` and its family (`os.path.exists`,
`os.lstat`), for reading `os.environ` or calling `os.getenv`, or for `function.__globals__`: those are the
validator's (`os` is a banned import, dunder attributes are banned), and the sandbox has no secrets in its
environment and a read-only image. An `import` of a module that is loaded already raises no event either (`import
os`, which numpy loaded), so the hook stops new modules only; the validator's import rules stop the rest, and with
every route to a frame refused a snippet cannot reach `__import__` past them."""
CODE_EVENTS = ("exec", "compile")
"""Audit events that run or build code: `exec` and `eval` raise `compile` for text and then `exec` for the code
object, `compile` and `ast.parse` raise `compile` only. `numpy.testing.measure` and `runstring` compile and exec any
string (validator review of 2026-10-14), so both guards refuse `exec` once armed, except for the one run of the plot or
snippet itself, `CODE_BUILDERS` and, in plot mode, an import (`PlotGuard`). The data guard refuses `compile` the same
way; the plot guard lets it through, because a code object runs only through `exec` (or the refused
`function.__new__`, `code.__new__` and `__code__` assignment), and matplotlib compiles at draw time
(`ast.literal_eval` of colour strings, cycler strings) and `typing` at import time."""
CODE_BUILDERS = frozenset(
    {
        ("collections/__init__.py", "namedtuple"),
        ("dataclasses.py", "add_fns_to_class"),
        ("scipy/stats/_distn_infrastructure.py", "_attach_argparser_methods"),
    }
)
"""The `(file suffix, function)` pairs whose `exec` and `compile` both guards let through when they call them: each
builds methods from a fixed template and names it checked as identifiers. `namedtuple` runs inside
`DataFrame.itertuples()`, `add_fns_to_class` whenever a dataclass is created (`make_dataclass`), and scipy's
`_attach_argparser_methods` whenever a distribution is created (`stats.rv_histogram`, `rv_discrete(values=...)`). The
caller is the frame that called `exec`, which the code under test cannot forge without running code it compiled."""
IMPORT_FRAME_FILES = ("<frozen importlib._bootstrap>", "<frozen importlib._bootstrap_external>")
"""The files of the frames that run an import. The plot guard lets an `exec` through when, walking up from its caller,
it meets one of these frames before a frame of the plot: a module body the plot imports runs (and builds code: scipy's
distributions, numpy's `f2py` rule tables, `typing.NamedTuple`) with no plot code between it and the import."""
CODE_OBJECT_EVENTS = ("code.__new__", "function.__new__")
"""Building a code object or a function from one: the plot guard treats them, and a `__code__` assignment, like
`exec`. `types.coroutine` assigns `__code__` when `asyncio` is imported, which a library may do lazily."""
NATIVE_CALLERS = ("/threadpoolctl.py",)
"""The files whose `ctypes.*` events the plot guard lets through: scikit-learn limits the BLAS threads around
`KMeans` and its kin with threadpoolctl, which opens the BLAS libraries the process loaded already and calls their
thread setters. Every other `ctypes.*` event is refused, so a NumPy array's `.ctypes` cannot reach `CDLL`."""
PLOT_BLOCKED_PREFIXES = (
    "ctypes.",
    "os.system",
    "os.exec",
    "os.posix_spawn",
    "os.spawn",
    "os.fork",
    "os.kill",
    "os.killpg",
    "os.remove",
    "os.rename",
    "os.rmdir",
    "os.mkdir",
    "os.symlink",
    "os.link",
    "os.chmod",
    "os.chown",
    "os.chflags",
    "os.chdir",
    "os.truncate",
    "os.utime",
    "subprocess.",
    "socket.",
    "shutil.",
    "pty.",
    "webbrowser.",
    "urllib.Request",
    "http.client.",
    "ftplib.",
    "smtplib.",
    "sys.addaudithook",
    "resource.setrlimit",
    "resource.prlimit",
    "builtins.input",
)
"""Audit events `PlotGuard` refuses once it is armed (`ctypes.*` but `NATIVE_CALLERS`), next to `exec` and
`CODE_OBJECT_EVENTS` and every `open` that writes anywhere but the plot's PNG and its probe. Unlike data mode it lets
imports, file reads and environment writes through: the plot imports its libraries lazily, matplotlib and seaborn read
fonts, style sheets and their own data files while drawing, and scikit-learn's import sets `KMP_DUPLICATE_LIB_OK`
(`os.putenv`), which matters to no process the guard lets start. A refusal raises `PermissionError`, an `OSError`, so
library code that already tolerates a read-only filesystem or a missing tool (matplotlib's cache writes,
`os.makedirs(..., exist_ok=True)`, `ctypes.util.find_library`, loky's `lscpu` call) carries on."""
FRAME_ATTRIBUTES = frozenset({"gi_frame", "cr_frame", "ag_frame", "tb_frame"})
"""Attributes that hand out a frame, whose `f_builtins` and `f_globals` reach `open` and `__import__`
(`(i for i in []).gi_frame.f_builtins`). CPython raises `object.__getattr__` for each; every other route to a frame
needs `sys._getframe` (refused) or `inspect` (a banned import, and `inspect.currentframe` is replaced)."""
DATA_PRELOAD = (
    "math",
    "statistics",
    "datetime",
    "collections",
    "itertools",
    "functools",
    "textwrap",
    "colorsys",
    "re",
    "warnings",
    "typing",
    "calendar",
    "decimal",
    "fractions",
    "zoneinfo",
    "enum",
    "dataclasses",
    "operator",
    "bisect",
    "heapq",
    "numbers",
    "cmath",
    "random",
    "numpy",
    "numpy.fft",
    "numpy.linalg",
    "numpy.polynomial",
    "numpy.random",
    "numpy.ma",
    "pandas",
    "scipy.stats",
    "scipy.interpolate",
    "scipy.signal",
    "scipy.cluster.hierarchy",
    "scipy.spatial",
    "scipy.optimize",
    "scipy.special",
    "scipy.integrate",
    "scipy.ndimage",
    "scipy.fft",
    "scipy.linalg",
    "scipy.constants",
)
"""Everything the validator's DATA profile lets a snippet import (`validate.DATA_IMPORTS`, pinned by a test), plus
the numpy subpackages numpy loads lazily: imported before the guard, because it refuses every later import."""
PANDAS_WARM_PACKAGES = ("pandas.core", "pandas.tseries", "pandas.api")
"""pandas imports some modules on first use (`DataFrame.pivot` loads `pandas.core.reshape.reshape`); every module
under these packages is imported before the guard, so no snippet meets a lazy import."""


def builds_code(frame):
    """Whether `frame`, the caller of an `exec` or `compile`, is one of `CODE_BUILDERS`."""
    if frame is None:
        return False
    code = frame.f_code
    file_name = code.co_filename.replace("\\", "/")
    return any(file_name.endswith("/" + suffix) and code.co_name == name for suffix, name in CODE_BUILDERS)


UNAUDITED_CALLS = (
    ("os", "mkfifo"),
    ("os", "mknod"),
    ("posix", "mkfifo"),
    ("posix", "mknod"),
    ("_posixsubprocess", "fork_exec"),
    ("subprocess", "_fork_exec"),
)
"""Callables that create a directory entry or start a process with no audit event in CPython 3.13 (#12177 review:
`os.mkfifo` and `os.mknod`; `_posixsubprocess.fork_exec` is what `subprocess.Popen` runs after its own event). The
guards replace them with `refused_call` before arming, in every module that holds them, so code past the validator
cannot reach them through `os`, `posix` or a module that imported them by name."""


def refused_call(*args, **kwargs):
    raise PermissionError("blocked by the sandbox: a call the audit hook cannot see")


def disable_unaudited_calls():
    """Replace `UNAUDITED_CALLS` in the modules that are loaded or load without side effects."""
    import importlib

    for module_name, name in UNAUDITED_CALLS:
        module = sys.modules.get(module_name)
        if module is None and module_name.startswith(("posix", "_posix")):
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                continue
        if module is not None and hasattr(module, name):
            setattr(module, name, refused_call)


def sets_code(event, args):
    """A `function.__code__` assignment, which would run a compiled code object without an `exec` event."""
    return event == "object.__setattr__" and len(args) > 1 and args[1] == "__code__"


class DataGuard:
    """The audit hook of data mode: once armed, refuses every `open` and every `import`, native code, processes,
    sockets, filesystem changes and listings, every route to a frame, and every `exec` and `compile` but the
    snippet's own run and `CODE_BUILDERS`.

    `blocked` keeps the first refused event's family, so a run whose snippet caught the
    error is refused all the same. `paused()` lets the harness itself read frames while it
    prints a traceback, when no snippet code runs.
    """

    def __init__(self):
        self.armed = False
        self.blocked = None
        self.paused_depth = 0
        self.entry = None  # the code object `arm` lets run once

    def refuses(self, event, args):
        """Whether `event` with `args` is one the armed guard refuses."""
        if event in ("open", "import"):
            return True
        if event == "object.__getattr__":
            return len(args) > 1 and args[1] in FRAME_ATTRIBUTES
        if event in CODE_EVENTS:
            return not self.lets_code_run(event, args)
        if event == "sys._getframemodulename":
            return False  # a module name, no frame: `namedtuple` asks for it (`DataFrame.itertuples()`)
        return sets_code(event, args) or event.startswith(DATA_BLOCKED_PREFIXES)

    def lets_code_run(self, event, args):
        """Whether an `exec` or `compile` may run: the entry code object once, then only `CODE_BUILDERS`."""
        if self.is_entry(event, args):
            return True
        return builds_code(self.caller())

    def is_entry(self, event, args):
        """The `exec` of the entry code object, which `arm` lets run exactly once."""
        if event == "exec" and self.entry is not None and args and args[0] is self.entry:
            self.entry = None
            return True
        return False

    def caller(self):
        """The frame that raised the event: the first frame above the guard's own (`sys._getframe` raises an audit
        event of its own, which the data guard refuses, so the lookup runs paused)."""
        with self.paused():
            frame = sys._getframe(1)
            while frame is not None and frame.f_code.co_filename == __file__:
                frame = frame.f_back
        return frame

    def __call__(self, event, args):
        if not self.armed or self.paused_depth or not self.refuses(event, args):
            return
        if self.blocked is None:
            self.blocked = event.split(".", 1)[0]
        raise RuntimeError("blocked by the data sandbox")

    def arm(self, entry=None):
        """Install the hook (it can never be removed) and let `entry`, the compiled code, run once under it.

        The calls that change the filesystem or start a process without raising an audit event are
        replaced first (`disable_unaudited_calls`), because the hook cannot see them.
        """
        self.entry = entry
        disable_unaudited_calls()
        sys.addaudithook(self)
        self.armed = True

    def paused(self):
        guard = self

        class _Paused:
            def __enter__(self):
                guard.paused_depth += 1

            def __exit__(self, *exc):
                guard.paused_depth -= 1
                return False

        return _Paused()


WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC


class PlotGuard(DataGuard):
    """The audit hook of plot mode: once armed, refuses `PLOT_BLOCKED_PREFIXES` (processes, sockets, native code,
    filesystem changes), every `open` that writes anywhere but `outputs`, a `__code__` assignment, and every `exec`
    but the plot's own run, `CODE_BUILDERS` and the module bodies of an import.

    Imports, reads and `compile` stay allowed (`PLOT_BLOCKED_PREFIXES`, `CODE_EVENTS`). A refusal raises
    `PermissionError`; `blocked` keeps the first refused event's family for a caller that wants it.
    """

    def __init__(self, outputs):
        super().__init__()
        self.outputs = frozenset(os.path.realpath(path) for path in outputs)
        self.plot_file = None

    def arm(self, entry=None):
        self.plot_file = entry.co_filename if entry is not None else None
        super().arm(entry)

    def refuses(self, event, args):
        if event == "open":
            return self.writes_elsewhere(args)
        if event == "compile":
            return False
        if event == "exec" or event in CODE_OBJECT_EVENTS or sets_code(event, args):
            return not self.lets_code_run(event, args)
        if event.startswith("ctypes."):
            return not self.native_caller()
        return event.startswith(PLOT_BLOCKED_PREFIXES)

    def lets_code_run(self, event, args):
        """The plot's code object once, `CODE_BUILDERS`, and code an import runs: walking up from the caller, an
        import frame (`IMPORT_FRAME_FILES`) comes before any frame of the plot file, so no plot code (a callback the
        plot handed to a library) sits between the import and the `exec`."""
        if self.is_entry(event, args):
            return True
        frame = self.caller()
        if builds_code(frame):
            return True
        while frame is not None:
            file_name = frame.f_code.co_filename
            if file_name == self.plot_file:
                return False
            if file_name in IMPORT_FRAME_FILES:
                return True
            frame = frame.f_back
        return False

    def native_caller(self):
        """Whether the first frame outside the `ctypes` package that raised a `ctypes.*` event is one of
        `NATIVE_CALLERS`."""
        frame = self.caller()
        while frame is not None and "/ctypes/" in frame.f_code.co_filename.replace("\\", "/"):
            frame = frame.f_back
        return frame is not None and frame.f_code.co_filename.replace("\\", "/").endswith(NATIVE_CALLERS)

    def writes_elsewhere(self, args):
        """Whether an `open` event (path, mode, flags) writes to anything but `outputs`: `open` passes its mode
        text and the flags it derived, `os.open` only flags.

        The event carries no `dir_fd`, so a relative path of `os.open` (`mode` None) may name a file
        in another directory than the working one (`os.open("plot-light.png", flags, dir_fd=fd)`, or
        `open(..., opener=...)`, whose opener calls `os.open`): an `os.open` write passes only with an
        absolute path (#12177 review). `open` itself, which savefig and the probe use, takes no `dir_fd`.
        """
        path, mode, flags = (*args, None, None, None)[:3]
        writes = (isinstance(mode, str) and any(letter in mode for letter in "wax+")) or (
            isinstance(flags, int) and bool(flags & WRITE_FLAGS)
        )
        if not writes:
            return False
        if not isinstance(path, str | bytes | os.PathLike):
            return True  # a file descriptor, or anything else that names no path
        if mode is None and not os.path.isabs(os.fsdecode(path)):
            return True
        with self.paused():
            try:
                return os.path.realpath(os.fsdecode(path)) not in self.outputs
            except (OSError, ValueError, TypeError):
                return True

    def __call__(self, event, args):
        if not self.armed or self.paused_depth or not self.refuses(event, args):
            return
        if self.blocked is None:
            self.blocked = event.split(".", 1)[0]
        raise PermissionError(f"blocked by the render sandbox: {event}")


def preload_data_modules():
    """Import what a snippet may use, warm pandas' lazy paths and the time zones, before the guard refuses imports
    and file reads; a module missing here (a developer machine) is skipped."""
    import importlib
    import pkgutil

    for name in DATA_PRELOAD:
        try:
            importlib.import_module(name)
        except ImportError:
            continue
    for package_name in PANDAS_WARM_PACKAGES:
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            continue
        for info in pkgutil.walk_packages(package.__path__, package_name + "."):
            if ".tests" in info.name:
                continue
            try:
                importlib.import_module(info.name)
            except Exception:
                continue  # optional dependencies (numba, pyarrow) that the image does not install
    import pandas as pd

    warm = pd.DataFrame({"a": [1.0, 2.0], "t": pd.to_datetime(["2020-01-01", "2020-01-02"])})
    warm.set_index("t").reset_index().to_csv(io.StringIO(), index=False)
    zones = []
    try:
        import zoneinfo

        keys = sorted(zoneinfo.available_timezones())
        # The C class and the pure-Python one (`zoneinfo._zoneinfo`, which pandas' tslibs can reach) cache apart.
        classes = {zoneinfo.ZoneInfo, getattr(sys.modules.get("zoneinfo._zoneinfo"), "ZoneInfo", zoneinfo.ZoneInfo)}
        zones = [kind(key) for kind in classes for key in keys]
    except Exception:
        pass
    # pandas' `find_stack_level` walks frames through `inspect.currentframe()` before every warning; the guard
    # refuses `sys._getframe`, so the lookup answers None and pandas reports its warning at level 0.
    import inspect

    inspect.currentframe = lambda: None
    return zones


def print_snippet_error(guard, exc):
    """The traceback of a snippet error on stderr: its frames' files and lines and the exception line.

    Written by hand, with the guard paused only to read the traceback's frames: the
    `traceback` module reads source lines from files, which the armed guard refuses.
    """
    lines = ["Traceback (most recent call last):"]
    with guard.paused():
        tb = exc.__traceback__
        while tb is not None:
            code = tb.tb_frame.f_code
            lines.append(f'  File "{code.co_filename}", line {tb.tb_lineno}, in {code.co_name}')
            tb = tb.tb_next
    kind = type(exc)
    name = kind.__qualname__ if kind.__module__ == "builtins" else f"{kind.__module__}.{kind.__qualname__}"
    try:
        text = str(exc)
    except Exception:
        text = ""
    lines.append(f"{name}: {text}" if text else name)
    try:
        print("\n".join(lines), file=sys.stderr, flush=True)
    except Exception:
        pass


def _limit(kind: int, value: int) -> None:
    try:
        soft, hard = resource.getrlimit(kind)
        if hard != resource.RLIM_INFINITY:
            value = min(value, hard)
        resource.setrlimit(kind, (value, value))
    except (ValueError, OSError):
        pass  # a limit the platform refuses is left to the sandbox and the host timeout


def set_limits() -> None:
    cpu = int(os.environ.get("ANYPLOT_RLIMIT_CPU_S", "60"))
    fsize = int(os.environ.get("ANYPLOT_RLIMIT_FSIZE_MB", "32")) * 1024 * 1024
    _limit(resource.RLIMIT_CPU, cpu)
    _limit(resource.RLIMIT_FSIZE, fsize)
    address_space = os.environ.get("ANYPLOT_RLIMIT_AS_MB")
    if address_space:
        _limit(resource.RLIMIT_AS, int(address_space) * 1024 * 1024)
    processes = os.environ.get("ANYPLOT_RLIMIT_NPROC")
    if processes:
        _limit(resource.RLIMIT_NPROC, int(processes))


def seed_mplconfig() -> None:
    """Copy the baked matplotlib cache into the writable `MPLCONFIGDIR`, before matplotlib is imported."""
    seed = os.environ.get("ANYPLOT_MPL_SEED")
    target = os.environ.get("MPLCONFIGDIR")
    if not seed or not target or not os.path.isdir(seed):
        return
    try:
        shutil.copytree(seed, target, dirs_exist_ok=True)
    except OSError:
        pass  # matplotlib rebuilds a missing cache itself, only slower


def install_fallback_fonts():
    """Append the installed fallback families to every font lookup, after the font the code chose.

    matplotlib falls back per glyph across the list `FontManager._find_fonts_by_props` returns
    (every Agg text path calls it: `RendererAgg._prepare_font`, `Text`, `TextPath`), and it builds
    that list from `font.family` only: a list in `font.sans-serif` resolves to one font, seaborn's
    `set_theme` rewrites `font.family` (306 catalogue files call it) and `fontfamily="monospace"`
    on a text bypasses the rc list. Wrapping the lookup keeps whatever the code chose first, so the
    catalogue look is unchanged, and cannot be undone by rcParams. Each fallback family is asked for
    the nearest weight it has (a bold title gets the bold CJK face; Noto Sans Symbols2 has only
    Regular), because `findfont` does not raise for a weight a family lacks: it takes the nearest
    and logs a WARNING once per lookup key, size included. `_find_fonts_by_props` is private API,
    pinned by uv.lock; a unit test and the CI image job catch a rename.
    """
    try:
        import matplotlib.font_manager as fm
    except ImportError:
        return
    weights = {}  # family → the weights its installed files have, such as {400, 700}
    for entry in fm.fontManager.ttflist:
        if entry.name in FALLBACK_FAMILIES and isinstance(entry.weight, int):
            weights.setdefault(entry.name, set()).add(entry.weight)
    families = [name for name in FALLBACK_FAMILIES if name in weights]
    if not families:
        return
    original = fm.FontManager._find_fonts_by_props

    @functools.wraps(original)
    def with_fallbacks(self, prop, fontext="ttf", directory=None, fallback_to_default=True, rebuild_if_missing=True):
        paths = list(original(self, prop, fontext, directory, fallback_to_default, rebuild_if_missing))
        base = fm.FontProperties._from_any(prop)
        wanted = base.get_weight()
        if not isinstance(wanted, int):
            wanted = fm.weight_dict.get(wanted, 400)  # "bold" → 700, the names matplotlib accepts
        for family in families:
            fallback = base.copy()
            fallback.set_family(family)
            fallback.set_weight(min(weights[family], key=lambda weight: abs(weight - wanted)))
            try:
                path = self.findfont(fallback, fontext, directory, fallback_to_default=False, rebuild_if_missing=False)
            except ValueError:
                continue  # the family is in no file of the cache any more, or its file is gone from disk
            if path not in paths:  # FontPath compares path and face index, so a TTC face is one entry
                paths.append(path)
        return paths

    fm.FontManager._find_fonts_by_props = with_fallbacks


def check_fonts():
    """Build the font cache into `MPLCONFIGDIR` and fail when a fallback family is not installed (the image build)."""
    import matplotlib.font_manager as fm

    installed = {entry.name for entry in fm.fontManager.ttflist}
    missing = [name for name in ("DejaVu Sans", *FALLBACK_FAMILIES) if name not in installed]
    if missing:
        raise SystemExit(f"fonts missing from the image: {', '.join(missing)}")
    print(f"font cache: {len(fm.fontManager.ttflist)} faces; fallback families: {', '.join(FALLBACK_FAMILIES)}")


def install_glyph_capture():
    """Record every code point matplotlib reports as having no glyph in the fonts of a text.

    matplotlib reports a missing glyph of plain text as a `UserWarning` from
    `_text_helpers.warn_on_missing_glyph`, which `ft2font` looks up by name at call time, so
    replacing the attribute sees every report even when the plot code ignores warnings; the
    original still runs, so stderr keeps matplotlib's message. Mathtext reports through the
    `matplotlib.mathtext` logger instead, with the code point as the record's third argument;
    the logger's own level is pinned, because `matplotlib.set_loglevel("error")` sets the parent.
    """
    try:
        import matplotlib._text_helpers as text_helpers
    except ImportError:
        return
    original = text_helpers.warn_on_missing_glyph

    @functools.wraps(original)
    def recording(codepoint, fontnames):
        if isinstance(codepoint, int) and not isinstance(codepoint, bool):
            MISSING_GLYPHS.add(codepoint)
        return original(codepoint, fontnames)

    text_helpers.warn_on_missing_glyph = recording

    class MathGlyphs(logging.Handler):
        def emit(self, record):
            args = record.args
            if (
                isinstance(args, tuple)
                and len(args) == 3
                and isinstance(args[2], int)
                and "does not have a glyph" in str(record.msg)
            ):
                MISSING_MATH_GLYPHS.add(args[2])

    logger = logging.getLogger("matplotlib.mathtext")
    logger.addHandler(MathGlyphs())
    logger.setLevel(logging.WARNING)


def glyph_report():
    """The probe's `missing_glyphs` field: distinct code points without a glyph so far in this process."""
    every = MISSING_GLYPHS | MISSING_MATH_GLYPHS
    return {"count": len(every), "math": len(MISSING_MATH_GLYPHS), "sample": sorted(every)[:GLYPH_SAMPLE_LIMIT]}


def _report(event, **fields):
    print(f"{MARKER} {json.dumps({'event': event, **fields})}", flush=True)


def _usage():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {"max_rss_mb": round(usage.ru_maxrss / 1024, 1), "cpu_s": round(usage.ru_utime + usage.ru_stime, 3)}


def _box(extent):
    return [round(extent.x0, 1), round(extent.y0, 1), round(extent.x1, 1), round(extent.y1, 1)]


def _overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _overlap_px(a, b):
    """How deep two boxes overlap: the smaller of the shared width and height, 0 when they do not touch."""
    return max(0.0, min(min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])))


def _text_kinds(figure):
    """The role of every text artist of the figure, by id: tick labels, axis labels, titles, legends, annotations.

    A polar axes names its axis labels by what they label (the angular and the radial
    axis), and its ids are collected in the second set, so a line can name the cause.
    The third map names the legend a legend text belongs to: texts of one legend are
    laid out by it, texts of two legends can collide. A drawn text no role names (an
    axis offset text, a table cell) is "text" to the caller.
    """
    kinds = {}
    polar = set()
    legend_of = {}

    def add_legend(legend):
        for text in [*legend.get_texts(), legend.get_title()]:
            kinds[id(text)] = "legend text"
            legend_of[id(text)] = id(legend)

    for axes in figure.get_axes():
        is_polar = getattr(axes, "name", "") == "polar"
        axis_names = (("x", "angular"), ("y", "radial"), ("z", "z"))
        for attribute, polar_name in axis_names:
            axis = getattr(axes, f"{attribute}axis", None)
            if axis is None:
                continue
            for label in axis.get_ticklabels():
                kinds[id(label)] = "tick label"
            name = polar_name if is_polar else attribute
            kinds[id(axis.label)] = f"{name} axis label"
            if is_polar:
                polar.add(id(axis.label))
        for title in (getattr(axes, name, None) for name in ("title", "_left_title", "_right_title")):
            if title is not None:
                kinds[id(title)] = "title"
        for child in axes.texts:
            kinds[id(child)] = "annotation" if type(child).__name__ == "Annotation" else "text"
        legend = axes.get_legend()
        if legend is not None:
            add_legend(legend)
        for artist in axes.artists:  # an earlier legend kept with `ax.add_artist(legend)`
            if type(artist).__name__ == "Legend":
                add_legend(artist)
    for legend in getattr(figure, "legends", []):
        add_legend(legend)
    for text in getattr(figure, "texts", []):
        kinds[id(text)] = "text"
    for name in ("_suptitle", "_supxlabel", "_supylabel"):
        text = getattr(figure, name, None)
        if text is not None:
            kinds[id(text)] = "suptitle" if name == "_suptitle" else "figure axis label"
    return kinds, polar, legend_of


def text_overlaps(figure, extents, scale):
    """Pairs of measured texts that overlap by more than `TEXT_OVERLAP_TOLERANCE_PX`, one of them no tick label.

    Every measured text takes part; one no role names (an axis offset text, a table
    cell) is "text". Tick label against tick label stays `tick_overlaps`. Two texts of
    one legend are laid out by that legend and never compared; texts of two legends
    are. At most `TEXT_OVERLAP_CANDIDATES` texts that are no tick label are compared
    with every measured text; the deepest `TEXT_OVERLAP_LIMIT` pairs are returned with
    the total count. Depths are in the saved image's pixels.
    """
    kinds, polar, legend_of = _text_kinds(figure)
    known = [(key, kinds.get(key, "text"), box) for key, box in extents.items()]
    others = [item for item in known if item[1] != "tick label"][:TEXT_OVERLAP_CANDIDATES]
    pairs = []
    seen = set()
    for key, kind, box in others:
        for other_key, other_kind, other_box in known:
            if other_key == key or frozenset((key, other_key)) in seen:
                continue
            if key in legend_of and legend_of.get(other_key) == legend_of[key]:
                continue
            depth = float(_overlap_px(box, other_box) * scale)
            if depth > TEXT_OVERLAP_TOLERANCE_PX and math.isfinite(depth):
                seen.add(frozenset((key, other_key)))
                pairs.append(
                    {"a": kind, "b": other_kind, "px": round(depth, 1), "polar": key in polar or other_key in polar}
                )
    pairs.sort(key=lambda pair: -pair["px"])
    return pairs[:TEXT_OVERLAP_LIMIT], len(pairs)


def _beyond(box, width, height):
    """Whether a text box reaches past an edge of the `width` x `height` canvas."""
    return box[0] < 0 or box[1] < 0 or box[2] > width or box[3] > height


def _draw_recording_texts(figure):
    """Draw the figure once and return the texts that rendered, by id.

    Every way matplotlib draws text (tick labels, titles, legends, annotations, table
    cells) goes through `Text.draw`, so wrapping it for this one draw sees exactly
    what reaches the canvas. The wrapper is removed in `finally`; `functools.wraps`
    keeps the attributes matplotlib's rasterization decorator set on the original.
    """
    from matplotlib.text import Text

    drawn = {}
    original = Text.draw

    @functools.wraps(original)
    def recording(self, renderer):
        if self.get_visible() and self.get_text().strip():  # the cases Text.draw itself returns early on
            drawn[id(self)] = self
        return original(self, renderer)

    Text.draw = recording
    try:
        figure.canvas.draw()
    finally:
        Text.draw = original
    return drawn


def probe(figure, dpi):
    """What the figure will look like on the canvas, measured before it is saved."""
    drawn = _draw_recording_texts(figure)
    renderer = figure.canvas.get_renderer()
    width_in, height_in = figure.get_size_inches()
    scale = (dpi or figure.dpi) / figure.dpi
    width_px, height_px = float(width_in) * float(dpi or figure.dpi), float(height_in) * float(dpi or figure.dpi)
    extents = {}  # id(text) -> its box in figure pixels; G7 and G5 reuse these instead of measuring again
    measured = []
    for text in itertools.islice(drawn.values(), PROBE_MEASURE_LIMIT):
        try:
            extents[id(text)] = _box(text.get_window_extent(renderer))
        except Exception:
            continue
        box = [value * scale for value in extents[id(text)]]
        if all(math.isfinite(value) for value in box):  # one text at an infinite coordinate never voids the probe
            measured.append({"kind": type(text).__name__, "box": box})
    # Only PROBE_LIMIT boxes are kept: the ones past a canvas edge go first, so a plot with
    # hundreds of labels (100 bars with value labels, a 100-entry legend) still shows G3
    # every clipped text among the measured ones, whatever order matplotlib drew them in.
    measured.sort(key=lambda item: not _beyond(item["box"], width_px, height_px))
    texts = measured[:PROBE_LIMIT]
    tick_overlaps = 0
    annotations_outside = 0
    points = 0
    line_points = 0
    annotation_budget = PROBE_MEASURE_LIMIT
    for axes in figure.get_axes():
        for axis in (axes.xaxis, axes.yaxis, getattr(axes, "zaxis", None)):  # zaxis: 3-D axes only
            if axis is None:
                continue
            boxes = [extents[id(label)] for label in axis.get_ticklabels() if id(label) in extents]
            tick_overlaps += sum(1 for left, right in zip(boxes, boxes[1:], strict=False) if _overlaps(left, right))
        axes_box = _box(axes.get_window_extent(renderer))
        for child in axes.texts:
            try:
                if not child.get_visible() or type(child).__name__ != "Annotation":
                    continue
                box = extents.get(id(child))
                if box is None:  # not drawn (its point is out of view) or past the measured texts
                    if annotation_budget <= 0:
                        continue
                    annotation_budget -= 1
                    box = _box(child.get_window_extent(renderer))
                if not _overlaps(box, axes_box):
                    annotations_outside += 1
            except Exception:
                continue
        for collection in axes.collections:
            if type(collection).__name__ != "PathCollection":  # scatter marks; fills and meshes are not rows
                continue
            try:
                points += len(collection.get_offsets())
            except Exception:
                continue
        for line in axes.get_lines():  # plot() lines and their markers: one vertex per plotted value
            try:
                if line.get_visible():
                    line_points += len(line.get_xydata())
            except Exception:
                continue
    overlaps, overlaps_total = text_overlaps(figure, extents, scale)
    return {
        "figsize": [float(width_in), float(height_in)],
        "dpi": float(dpi or figure.dpi),
        "canvas": [
            round(float(width_in) * float(dpi or figure.dpi)),
            round(float(height_in) * float(dpi or figure.dpi)),
        ],
        "texts": texts,
        "texts_total": len(drawn),
        "tick_overlaps": tick_overlaps,
        "text_overlaps": overlaps,
        "text_overlaps_total": overlaps_total,
        "annotations_outside": annotations_outside,
        "points": points,
        "line_points": line_points,
    }


def polar_report(figure):
    """Every polar axes of the figure (at most `POLAR_AXES_LIMIT`): where its radial tick labels sit and its data lies.

    All angles are in degrees in the axes' own theta coordinates, the ones
    `set_rlabel_position` takes, so the theta offset and direction need no
    conversion: `rlabel` is the radial labels' angle and `thetamin` and `thetamax`
    the visible span. Axes without drawn radial tick labels are left out. `bins`
    counts the plotted points (offsets of visible scatter collections and the
    vertices of visible lines) per `POLAR_BIN_DEG` bin of their angle modulo 360
    (the outer list) and per `POLAR_RINGS` bin of their radius as a share of the
    visible radius range, centre first (the inner lists); points outside that range
    are left out.
    """
    import numpy as np

    report = []
    for axes in figure.get_axes():
        if getattr(axes, "name", "") != "polar" or len(report) >= POLAR_AXES_LIMIT:
            continue
        try:
            # Only axes that show radial tick labels can have them on the data: none for a hidden
            # axes, a hidden radial axis, or ticks set empty (`set_yticks([])`, blank labels).
            labelled = (
                axes.get_visible()
                and axes.yaxis.get_visible()
                and any(label.get_visible() and label.get_text().strip() for label in axes.yaxis.get_ticklabels())
            )
        except Exception:
            labelled = False
        if not labelled:
            continue
        thetas, radii = [], []
        for collection in axes.collections:
            if type(collection).__name__ != "PathCollection" or not collection.get_visible():
                continue
            try:
                offsets = np.asarray(collection.get_offsets(), dtype=float).reshape(-1, 2)
            except Exception:
                continue
            thetas.append(offsets[:, 0])
            radii.append(offsets[:, 1])
        for line in axes.get_lines():
            try:
                if line.get_visible():
                    xy = np.asarray(line.get_xydata(), dtype=float).reshape(-1, 2)
                    thetas.append(xy[:, 0])
                    radii.append(xy[:, 1])
            except Exception:
                continue
        try:
            rmin, rmax = float(axes.get_rmin()), float(axes.get_rmax())
            entry = {
                "rlabel": float(axes.get_rlabel_position()),
                "thetamin": float(axes.get_thetamin()),
                "thetamax": float(axes.get_thetamax()),
            }
        except Exception:
            continue
        theta = np.concatenate(thetas) if thetas else np.empty(0)
        radius = np.concatenate(radii) if radii else np.empty(0)
        share = (radius - rmin) / (rmax - rmin) if rmax != rmin else np.full_like(radius, np.nan)
        keep = np.isfinite(theta) & np.isfinite(share) & (share >= 0) & (share <= 1)
        counts, _, _ = np.histogram2d(
            np.mod(np.degrees(theta[keep]), 360.0),
            share[keep],
            bins=[360 // POLAR_BIN_DEG, POLAR_RINGS],
            range=[[0.0, 360.0], [0.0, 1.0]],
        )
        entry["bins"] = [[int(count) for count in row] for row in counts]
        report.append(entry)
    return report


def install_probe(theme):
    try:
        from matplotlib.figure import Figure
    except ImportError:
        return
    original = Figure.savefig

    def savefig(self, *args, **kwargs):
        try:
            report = probe(self, kwargs.get("dpi"))
        except Exception as exc:  # the probe never breaks a render
            report = {"error": type(exc).__name__}
        result = original(self, *args, **kwargs)
        report["missing_glyphs"] = glyph_report()  # independent of the geometric probe, so also next to {"error": ...}
        try:
            polar = polar_report(self)
        except Exception:  # the polar report never breaks a render either
            polar = []
        if polar:
            report["polar"] = polar
        try:
            text = json.dumps(report, allow_nan=False)  # NaN or Infinity (a text at an infinite coordinate)
        except (TypeError, ValueError) as exc:
            text = json.dumps({"error": type(exc).__name__})
        try:
            with open(f"probe-{theme}.json", "w", encoding="utf-8") as handle:
                handle.write(text)
        except OSError:
            pass
        return result

    Figure.savefig = savefig


def frame_csv(frame, measure=None):
    """The CSV text of a snippet's `df`, or the `DATA_EXIT` key of why there is none.

    For a cap it broke, `measure` (a dict) gets the measured value and the cap: rows,
    columns or CSV bytes, which the host turns into a message the model can act on.
    """
    import pandas as pd

    measure = measure if measure is not None else {}
    if not isinstance(frame, pd.DataFrame):
        return None, "no_frame"
    if isinstance(frame.columns, pd.MultiIndex):
        return None, "frame_shape"
    index = frame.index
    default_index = isinstance(index, pd.RangeIndex) and index.start == 0 and index.step == 1 and index.name is None
    if not default_index:
        try:
            frame = frame.reset_index()
        except (ValueError, TypeError):  # an index name that is also a column, a MultiIndex level clash
            return None, "frame_shape"
    frame = frame.copy()
    frame.columns = [str(column) for column in frame.columns]
    if len(frame.index) > DATA_MAX_ROWS:
        measure.update(measured=len(frame.index), limit=DATA_MAX_ROWS)
        return None, "too_many_rows"
    if len(frame.columns) > DATA_MAX_COLUMNS:
        measure.update(measured=len(frame.columns), limit=DATA_MAX_COLUMNS)
        return None, "too_many_columns"
    buffer = io.StringIO()
    frame.to_csv(buffer, index=False)
    text = buffer.getvalue()
    size = len(text.encode("utf-8", errors="surrogatepass"))
    if size > DATA_MAX_CSV_BYTES:
        measure.update(measured=size, limit=DATA_MAX_CSV_BYTES)
        return None, "too_large"
    return text, None


def write_status(handle, code, measure):
    """`status.json`: the run's `DATA_EXIT` code and, for a broken cap, the measured value and the cap.

    The host reads it whatever the launcher's exit code says: Cloud Run's `sandbox do`
    reports every non-zero exit of the sandboxed process as its own death by SIGPIPE
    (-13), so the exit code alone cannot carry `too_large` from the sandbox. The handle
    was opened before the guard; the snippet cannot reach it, and a write to an open
    file raises no audit event.
    """
    if handle is None:
        return
    reason = next((name for name, value in DATA_EXIT.items() if value == code), None)
    report = {"exit": code, "reason": reason}
    for key in ("measured", "limit"):
        if isinstance(measure.get(key), int):
            report[key] = measure[key]
    try:
        handle.write(json.dumps(report))
        handle.close()
    except Exception:
        pass  # the host then falls back on the launcher's exit code


def main_data(path, guard=None):
    """Data mode (module docstring): run the snippet under `DataGuard`, write its `df` to `out.csv` and the
    outcome to `status.json`."""
    _report("start")
    set_limits()
    sys.dont_write_bytecode = True  # no .pyc write, which the guard would refuse
    try:
        status = open(DATA_STATUS_FILE, "w", encoding="utf-8")  # before the guard, which refuses every open
    except OSError:
        status = None
    measure = {}
    code = DATA_EXIT["error"]
    try:
        code = run_data_snippet(path, guard, measure)
    finally:
        write_status(status, code, measure)
    return code


def run_data_snippet(path, guard, measure):
    """`main_data` after the limits: preload, compile, arm the guard, run the snippet and write `out.csv`."""
    import builtins
    import ctypes  # noqa: F401  (pandas loads it anyway; its load opens a library, so before the guard)

    zones = preload_data_modules()  # every import and file read happens here, before the guard
    guard = guard if guard is not None else DataGuard()
    # The snippet is read and compiled before the guard too: it refuses every `open`, `io.open_code` included.
    try:
        with open(path, encoding="utf-8") as handle:
            code = compile(handle.read(), os.path.basename(path), "exec", dont_inherit=True)
    except (OSError, SyntaxError, ValueError):
        traceback.print_exc()
        return DATA_EXIT["error"]
    namespace = {"__name__": "__main__", "__builtins__": builtins}
    with open(DATA_OUT_FILE, "w", encoding="utf-8", newline="") as out:
        guard.arm(code)
        try:
            exec(code, namespace)
        except BaseException as exc:  # SystemExit included: the snippet never chooses the exit code
            print_snippet_error(guard, exc)
            return DATA_EXIT["blocked"] if guard.blocked else DATA_EXIT["error"]
        finally:
            try:
                _report("end", **_usage())
            except Exception:
                pass
        if guard.blocked:
            return DATA_EXIT["blocked"]
        try:
            text, refusal = frame_csv(namespace.get("df"), measure)
        except Exception as exc:
            print_snippet_error(guard, exc)
            return DATA_EXIT["blocked"] if guard.blocked else DATA_EXIT["error"]
        if guard.blocked:  # a pandas method the snippet replaced reached the guard
            return DATA_EXIT["blocked"]
        if refusal is not None:
            return DATA_EXIT[refusal]
        out.write(text)
    del zones
    return DATA_EXIT["ok"]


def warm_scikit_learn(source):
    """Run scikit-learn's two process lookups before the plot guard is armed, when the plot names sklearn (~45 ms).

    `KMeans`, `TSNE` and their kin ask threadpoolctl for the BLAS libraries, which first looks
    up libc with `ctypes.util.find_library("c")`: that runs `ldconfig` and then `gcc` through
    a temporary file, both of which the guard refuses, and the render fails. joblib's loky
    counts the physical cores with `lscpu`; refused, it falls back to the logical cores, and
    the oversubscribed threads of `TSNE` spent ten times the CPU seconds of an unguarded run
    (220 s against 23 s on a 16-core machine), past `RLIMIT_CPU`. Both cache their answer
    (`ThreadpoolController._system_libraries`, loky's `physical_cores_cache`), so one lookup
    here serves the render. A missing package or a renamed private name is skipped; the
    render test with `KMeans` under the guard catches the rename.
    """
    if b"sklearn" not in source:
        return
    try:
        import threadpoolctl

        threadpoolctl.ThreadpoolController._get_libc()
    except Exception:
        pass
    try:
        from joblib.externals.loky.backend import context

        context._count_physical_cores()
    except Exception:
        pass


def run_plot(path, guard):
    """Run the plot file as `__main__` under `guard`, the way `runpy.run_path` would.

    The file is read and compiled before the guard is armed, and the guard lets exactly
    that code object run once: every other `exec` the plot reaches is refused. `ctypes` is
    loaded first, because its import opens a library (`ctypes.dlopen`) and numpy, pandas and
    matplotlib reach it lazily; `warm_scikit_learn` runs the process lookups scikit-learn
    would otherwise make under the guard. No bytecode is written: the guard refuses the writes.
    The plot's frames carry the path as given, as under `runpy`, so a traceback still names
    `plot.py`.
    """
    import builtins
    import ctypes  # noqa: F401  (see the docstring)

    sys.dont_write_bytecode = True
    with open(path, "rb") as handle:
        source = handle.read()
    code = compile(source, path, "exec", dont_inherit=True)
    warm_scikit_learn(source)
    namespace = {
        "__name__": "__main__",
        "__file__": path,
        "__builtins__": builtins,
        "__doc__": None,
        "__package__": None,
        "__spec__": None,
        "__loader__": None,
        "__cached__": None,
    }
    guard.arm(code)
    exec(code, namespace)


def main(argv):
    if len(argv) == 3 and argv[1] == DATA_FLAG:
        return main_data(argv[2])
    _report("start")
    if len(argv) != 2:
        print("usage: harness.py <plot file>", file=sys.stderr)
        return 2
    theme = os.environ.get(THEME_ENV, "light")
    if theme not in ("light", "dark"):
        print(f"{THEME_ENV} must be light or dark", file=sys.stderr)
        return 2
    set_limits()
    seed_mplconfig()
    install_fallback_fonts()
    install_glyph_capture()
    install_probe(theme)
    try:
        run_plot(argv[1], PlotGuard((f"plot-{theme}.png", f"probe-{theme}.json")))
    finally:
        try:
            _report("end", **_usage())
        except Exception:
            pass  # a closed stdout must not hide the plot's own exception
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
