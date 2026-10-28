"""Render harness: runs one plot file inside the sandbox with resource limits and a savefig probe.

Usage, from the run directory (the CI render command with the harness in front):

    python -I -X disable-remote-debug /opt/anyplot/harness.py plot.py

It is a standalone script with no anyplot import, because it runs inside the
sandbox with the isolated interpreter (`-I`: no user site, no current directory on
`sys.path`, no `PYTHON*` environment) and without Python 3.14's remote debugging
(`INTERPRETER_FLAGS`). The renderer service
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
   visible `plot()` lines (`line_points`), and the content of the drawn texts by role
   (`labels`, `drawn_labels`: what the root's closing reply is grounded in). Only rendered text counts: matplotlib keeps tick
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
   and `CODE_BUILDERS` (`namedtuple`, dataclasses, scipy's distributions, plotnine's
   expression strings, and cssselect2's selector compiler, which pygal's PNG export runs for
   every CSS rule of the chart), a code object or
   function built by hand or a `__code__` assignment, every `open` that writes anything but
   `plot-<theme>.png`, `probe-<theme>.json` and `plot-<theme>.html` (altair's second
   file, which stays in the sandbox), `subprocess.*`, `os.system`, `os.exec*`,
   `os.posix_spawn`, `os.spawn*`, `os.fork*`, `socket.*`, `ctypes.*` (but threadpoolctl's,
   `NATIVE_CALLERS`, and the `ctypes.cast` scipy makes while it is imported, `IMPORT_CTYPES_HELPERS`),
   `sys.remote_exec`, filesystem changes and `os.chdir`, and every frame (`gi_frame`,
   `cr_frame`, `ag_frame`, `tb_frame`, `sys._getframe`) while plot code is on the stack, but
   to `FRAME_READERS` and import bodies (Fable review of #12177; `hide_frames` makes
   `logging.currentframe` answer None and `inspect.currentframe` answer a frame to one of
   `FRAME_READERS` only, `frame_for_readers`). Imports, reads and `compile` stay
   allowed, because the plot imports its libraries lazily and matplotlib reads fonts and
   style sheets and compiles colour strings while it draws; a refusal raises
   `PermissionError`. The validator review of 2026-10-14 found `np.testing.measure`, which
   compiles and runs any string, past the validator: this is the layer behind it. A sweep
   of the 650 catalogue matplotlib and seaborn files rendered all 474 the validator passes
   under the guard (the seven it newly failed are ones the validator refuses: a fetch, a
   `chdir`, `load_dataset`). With the frame refusals, a sweep of the 572 files the
   readiness scan admits rendered the same 565 as before, with no refusal logged;
   the seven failures are the plots' own (each divides by the length of a title the
   normaliser emptied). Arming first installs a seccomp filter (`install_exec_deny`, since
   2026-10-28) under which the kernel refuses every `execve` and `execveat` of the process,
   its threads and its children, so native code the hook cannot see (lets-plot's
   ImageMagick delegates) starts no program either; with `ANYPLOT_DENY_EXEC=required`
   (lets-plot's command row) a filter that is not in place stops the run before the plot
   starts, with exit code `EXEC_DENY_EXIT` and a stderr line that names it (Cloud Run's
   launcher reports every non-zero exit as -13), and without it the run goes on;
6. prints `HARNESS {"event": "end", "max_rss_mb": ..., "cpu_s": ..., "exec_deny": ...}`
   when the plot file returns or raises (`exec_deny`: `on`, `unavailable`, `unsupported`,
   or `off` when the guard was never armed); an exception still propagates, so its
   traceback reaches stderr and the exit code stays non-zero.

**Data mode** (`python -I -X disable-remote-debug /opt/anyplot/harness.py --data snippet.py`, the renderer's
`POST /run-data`): the harness runs a data-generating snippet (`run_data_code`,
`agents/anyplot/tools/session.py`) instead of a plot. It prints the start line, sets the
same limits, imports everything the validator's DATA profile allows (`DATA_PRELOAD`, every
module of `pandas.core`, `pandas.tseries` and `pandas.api`, which pandas would otherwise
load lazily, and every time zone), reads and compiles the snippet, opens `out.csv` for
writing, and only then arms `DataGuard`, the kernel filter of step 5 first, with `sys.addaudithook`: from there on the
interpreter refuses every `open` (reading too) and every `import`, `ctypes.*`,
`sys.remote_exec`, `os.system`, `os.exec*`, `os.posix_spawn`, `os.spawn*`, `os.fork*`, `subprocess.*`,
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
(characters without a glyph in any font of the text); the `density` field each save adds after the
probe (`density_report`: per axes, the bars and points and the value labels and decorations on them)
feeds G11, and `tick_axes` (what each axis's tick labels write: numbers, dates, categories) tells G12
which tick labels are numbers. It is
advisory because the code under test could tamper with it; the host never fails a
render on it. The same holds for the `HARNESS` lines: the code under test shares
stdout, so the host reads them as hints (a retry decision, a memory figure), never
as a verdict.
"""

import errno
import functools
import io
import itertools
import json
import logging
import math
import os
import re
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
LABEL_LIMIT = 400
"""Drawn texts whose content the probe reports (`labels`): every title, axis label and legend text of a
plot and the tick labels of 100 categories per axis, so a requested category is found, not guessed at."""
LABEL_CHARS = 200
"""One reported text at most: longer than any text the user can ask for (`schemas.MAX_EXPECTED_TEXT_CHARS`, 120)."""
LABEL_TOTAL_CHARS = 20_000
"""The reported texts together: JSON escapes a character outside ASCII as up to 12 bytes, so 20,000 of them
stay under 240 KiB, within the wire's 256 KiB probe cap; past it the rest is left out (`labels_truncated`)."""
TICK_LABELS_PER_AXIS = 100  # tick labels of one axis of one axes that `labels` keeps, in draw order
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
DENSITY_AXES_LIMIT = 8  # axes the probe's `density` field describes per figure
DENSITY_LABEL_LIMIT = 500  # data-anchored texts per axes matched against the marks
DENSITY_MARK_LIMIT = 2_000  # bar ends and points per axes a text is matched against
DENSITY_BAR_SLACK = 0.12  # a label's anchor sits within this share of the axes' value extent past its bar's end
DENSITY_POINT_SLACK = (0.02, 0.08)  # ... and within these shares of the axes' width and height of its point
GLYPH_SAMPLE_LIMIT = 16  # code points the probe lists; the host shows a few of them
MISSING_GLYPHS: set[int] = set()  # code points reported by matplotlib's text layout, this process
MISSING_MATH_GLYPHS: set[int] = set()  # code points reported by mathtext (no fallback inside `$…$`)

INTERPRETER_FLAGS = ("-I", "-X", "disable-remote-debug")
"""The flags every sandbox interpreter runs the harness with (the renderer's `executor.INTERPRETER_FLAGS`, the local
backend's `PythonRuntime` commands): `-I` isolates it, and `-X disable-remote-debug` turns off PEP 768's remote
debugging, new in Python 3.14, through which `sys.remote_exec` makes another Python process, or this one, run a
script file. `-I` ignores `PYTHON_DISABLE_REMOTE_DEBUG`, so only the option works here. The guards refuse
`sys.remote_exec` and `cpython.remote_debugger_script` as well, for a harness started without the flag."""
EXEC_FLAG = "--exec"
"""Exec mode (`agents/renderer/commands.py`): `harness.py --exec -- <command...>` prints the start line, sets the
limits and runs the language's own command (`Rscript plot.R`, `node render.mjs plot.js`, `julia plot.jl`) as a
child with the limits inherited, then prints the end line from the child's rusage and exits with its code. The
launcher retry, the host watchdog and the kill path then work for every language as for a Python plot; the
plot guard and the probe are Python's and do not apply."""
DATA_FLAG = "--data"
DATA_OUT_FILE = "out.csv"
DATA_STATUS_FILE = "status.json"
"""The data run's outcome for the host (`write_status`): `{"exit", "reason", "measured"?, "limit"?, "damage"?}`."""
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
CONVERT_FLAG = "--convert"
CONVERT_MODULE_FILE = "convert.py"
"""The converter (`agents/anyplot/render/convert.py`), next to the harness in the image and in the checkout."""
CONVERT_REQUEST_FILE = "request.json"
"""`{"sheet": <name or null>}`: the sheet (or `.npz` array) the page chose; missing means the first one."""
CONVERT_META_FILE = "meta.json"
"""What the conversion found (`convert.Conversion.meta`): the kind, the sheet and the others, the warning counts."""
CONVERT_MAX_INPUT_BYTES = 5 * 1024 * 1024  # convert.MAX_INPUT_BYTES
CONVERT_MAX_REQUEST_BYTES = 4096
CONVERT_REFUSALS = (
    "unsupported",
    "encrypted",
    "pickle",
    "hdf5",
    "corrupt",
    "archive_limits",
    "too_many_rows",
    "too_many_columns",
    "too_large",
    "empty",
    "sheet_not_found",
    "array_shape",
    "object_array",
    "formulas_only",
    "too_complex",
)
"""`convert.REFUSALS`, in its order (pinned by a test): the harness exits with 10 plus the index."""
CONVERT_DAMAGES = ("zip", "workbook", "sheet", "parquet", "arrow", "npy_header", "npy_data")
"""`convert.DAMAGES` (pinned by a test): the broken part of a `corrupt` file, written to `status.json` as `damage`
only when it is one of these names, so no text of the reader's ever leaves the sandbox."""
CONVERT_EXIT = {
    "ok": 0,
    "error": 1,
    "usage": 2,
    "blocked": 8,
    **{reason: 10 + index for index, reason in enumerate(CONVERT_REFUSALS)},
}
"""Exit codes of convert mode: `error` an exception in the reader (its class on stderr), `blocked` an operation the
guard refused (a reader that tried to import, open or run code), the rest a refused file."""
CONVERT_AST_READERS = (
    ("ast.py", "parse"),
    ("ast.py", "literal_eval"),
    ("numpy/lib/_format_impl.py", "_read_array_header"),
)
"""The one `compile` convert mode lets through: NumPy's `.npy` header reader parsing its dict literal to a tree."""
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
    "gc.get_",
    "sys.settrace",
    "sys.setprofile",
    "sys.monitoring.",
    "sys.remote_exec",
    "cpython.remote_debugger_script",
)
"""Audit events `DataGuard` refuses once it is armed (https://docs.python.org/3/library/audit_events.html), next to
every `open` and every `import`. CPython 3.14 raises no event for `os.stat` and its family (`os.path.exists`,
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
        ("plotnine/mapping/_env.py", "eval"),
        ("cssselect2/compiler.py", "__init__"),
    }
)
"""The `(file suffix, function)` pairs whose `exec` and `compile` both guards let through when they call them: each
builds methods from a fixed template and names it checked as identifiers. `namedtuple` runs inside
`DataFrame.itertuples()`, `add_fns_to_class` whenever a dataclass is created (`make_dataclass`), and scipy's
`_attach_argparser_methods` whenever a distribution is created (`stats.rv_histogram`, `rv_discrete(values=...)`). The
caller is the frame that called `exec`, which the code under test cannot forge without running code it compiled.
plotnine's `Environment.eval` is the one entry that evaluates text the plot wrote: an aesthetic or facet string that
is not a column name (`aes(fill="factor(g)")`, 7 of 273 eligible catalogue files, and the adapter's habit). The
validator admits those strings only as literals it walked as code with every rule of the profile
(`validate.EXPRESSION_CALLS`), and whatever the evaluated code reaches (writes, processes, sockets, frames) stays
refused here; patsy's `exec` behind `formula=` has no entry, the keyword is a validator finding. cssselect2's
`CompiledSelector.__init__` turns every CSS selector of an SVG `<style>` block into one `eval("lambda el: ...")`
(87 per pygal chart: cairosvg's `css.parse_stylesheets`, which `render_to_png` and `svg2png` run on the chart's
own stylesheet and on anything the plot adds through `Style`, `css=["inline:..."]` or `defs=`). The source is built
from the parsed selector tree: every string the CSS text controls (type, class, id, attribute name and value,
namespace, `:lang()` argument) is interpolated with `repr`, the only other values are the two integers of an `An+B`
argument (`tinycss2.nth.parse_nth`), and every other token raises `SelectorError`. The spike of 2026-10-26 fed 339
selectors with quotes, backslashes, CSS escapes, newlines, `{`/`}` and Python text to the compiler, and the same
payloads through every pygal channel, and read the generated source back with `ast`: it compares `el`'s name,
classes, id, attributes and `lang`, nothing else. Only Python objects handed to `compile_selector_list` in place of
tokens (a forged `dimension` token whose `int_value` is a string) reach an unquoted slot; the validator admits neither
`cssselect2` nor `tinycss2` nor `cairosvg.css`/`cairosvg.parser`, and a lambda the compiler built runs under the same
guard as the plot (no write, process, socket or frame)."""
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
thread setters. Every other `ctypes.*` event is refused (but `IMPORT_CTYPES_HELPERS`), so a NumPy array's `.ctypes`
cannot reach `CDLL`."""
IMPORT_CTYPES_HELPERS = ("_cast_addr",)
"""The `_ctypes` attributes holding the addresses of ctypes' own C helpers the plot guard lets an import call: only
`ctypes.cast`'s. Python 3.14 raises `ctypes.call_function` (its first argument the function's address) for every call
through a ctypes function pointer, `cast`, `memmove` and `memset` included, where 3.13 raised no event for those three.
scipy's `_lib._ccallback_c` calls `ctypes.cast` while it is imported, so every plot that imports scipy, statsmodels,
scikit-learn or seaborn after the guard is armed failed. `PlotGuard` lets that call through when the nearest origin
of its caller is an import (`calls_import_ctypes_helper`), the rule `exec` and frames follow; the same call from plot
code, `memmove` and `memset` (an in-process write that no allowed library needs), `string_at`, `wstring_at`,
`memoryview_at` and every other foreign function stay refused (Fable review of the 3.14 bump: the first draft let all
three helpers through from anywhere, which gave plot code back a write primitive 3.14's event had closed). The data
and convert guards need none of it: data mode imports scipy before it arms, and neither mode imports after."""
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
    "gc.get_",
    "sys.settrace",
    "sys.setprofile",
    "sys.monitoring.",
    "sys.remote_exec",
    "cpython.remote_debugger_script",
)
"""Audit events `PlotGuard` refuses once it is armed (`ctypes.*` but `NATIVE_CALLERS`), next to `exec` and
`CODE_OBJECT_EVENTS` and every `open` that writes anywhere but the plot's PNG and its probe. Unlike data mode it lets
imports, file reads and environment writes through: the plot imports its libraries lazily, matplotlib and seaborn read
fonts, style sheets and their own data files while drawing, and scikit-learn's import sets `KMP_DUPLICATE_LIB_OK`
(`os.putenv`), which matters to no process the guard lets start. A refusal raises `PermissionError`, an `OSError`, so
library code that already tolerates a read-only filesystem or a missing tool (matplotlib's cache writes,
`os.makedirs(..., exist_ok=True)`, `ctypes.util.find_library`, loky's `lscpu` call) carries on. Both guards refuse
`gc.get_objects`, `gc.get_referrers` and `gc.get_referents` (`gc.get_`), which would hand out the guard object itself
the way a frame's locals would (#12181 review), and every way to install a callback the interpreter hands frames or
code positions to (Fable review of #12181): `sys.settrace` and `sys.setprofile` (also what `threading.settrace`,
`setprofile` and their `_all_threads` forms raise, per thread) and `sys.monitoring.register_callback`, the one PEP 669
call that raises an event (`use_tool_id` and `set_events` do nothing without a callback). A trace function gets the
real frame and walks `f_back`, which no event sees, to `run_plot`'s locals. The signal handler, which gets a frame
too, has no event and is replaced instead (`UNAUDITED_CALLS`).

The guard's state (`armed`, `paused_depth`) stays a plain attribute, settable by anyone holding the guard: CPython
gives in-process code no state that a reference cannot reach (a closure cell is writable through `cell_contents`, a
class attribute through the class), so the defence is that no reference reaches the code under test. Every route to
one is refused: frames (`FRAME_EVENTS`, `FRAME_ATTRIBUTES`), the collector (`gc.get_`), trace, profile and monitoring
callbacks, and signal handlers."""
FRAME_ATTRIBUTES = frozenset({"gi_frame", "cr_frame", "ag_frame", "tb_frame"})
"""Attributes that hand out a frame, whose `f_builtins` and `f_globals` reach `open` and `__import__`
(`(i for i in []).gi_frame.f_builtins`). CPython raises `object.__getattr__` for each; every other route to a frame
needs `sys._getframe` (refused) or `inspect` (a banned import, and `inspect.currentframe` is replaced)."""
FRAME_EVENTS = ("sys._getframe", "sys._current_frames", "sys._current_exceptions")
"""Audit events that hand out a frame. `sys._getframemodulename` shares the first one's prefix but returns a module
name only, and both guards let it through: `namedtuple` and `enum` ask for it."""
FRAME_READERS = (
    (("pandas/core/common.py", "is_local_in_caller_frame"),),
    (("statsmodels/graphics/utils.py", "_import_mpl"),),
    (("traceback.py", "extract_stack"),),
    (("traceback.py", "_walk_tb_with_full_positions"), ("traceback.py", "_extract_from_extended_frame_gen")),
    (("plotnine/mapping/_env.py", "capture"),),
)
"""The callers the plot guard hands a frame (`FRAME_EVENTS`, `FRAME_ATTRIBUTES`) while plot code is on the stack,
each a chain of `(file suffix, function)` pairs that the caller's frame and the frames above it must match: each reads
a name or compares a value in the frame and returns no frame and no namespace. pandas' chained-assignment check runs
when an inplace method or a `__setitem__` meets a temporary (`df["a"].fillna(0, inplace=True)`), and statsmodels
names the caller of every graphic (`qqplot`, `plot_acf`). `traceback.extract_stack` and `extract_tb` return file
names and line numbers (`_walk_tb_with_full_positions` is a generator that yields frames, so it passes only while
`extract_tb`'s summary builder consumes it): pyparsing calls both while matplotlib builds and runs its mathtext
parser, on the first `$...$` a plot draws (30 of 572 eligible catalogue files). plotnine's `Environment.capture`
walks from `inspect.currentframe()` to the plot's own frame and keeps its `f_locals` and `f_globals`, the namespace
the plot has anyway, to look column names up in `aes("x")`; every plotnine file fails without it (the spike of
2026-10-24: `call-stack is not that deep!`), and the validator parses every aes string that is not a column name as
code. Library code that reads frames while an import runs (scipy's bunch types name their module) needs no entry: an
import body gets its frame like its `exec`. The helpers that return the frame they read are replaced before the guard
is armed (`hide_frames`): `logging.currentframe` answers None, `inspect.currentframe` answers its caller's frame to
one of these readers and None to everyone else (`frame_for_readers`)."""
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


def is_one_of(frame, functions):
    """Whether `frame` runs one of `functions`, `(file suffix, function name)` pairs."""
    if frame is None:
        return False
    code = frame.f_code
    file_name = code.co_filename.replace("\\", "/")
    return any(file_name.endswith("/" + suffix) and code.co_name == name for suffix, name in functions)


def builds_code(frame):
    """Whether `frame`, the caller of an `exec` or `compile`, is one of `CODE_BUILDERS`."""
    return is_one_of(frame, CODE_BUILDERS)


def reads_frames(frame):
    """Whether `frame`, the caller of a frame event, and the frames above it match one of the `FRAME_READERS` chains."""
    for chain in FRAME_READERS:
        current = frame
        for function in chain:
            if not is_one_of(current, (function,)):
                break
            current = current.f_back
        else:
            return True
    return False


UNAUDITED_CALLS = (
    ("os", "mkfifo"),
    ("os", "mknod"),
    ("posix", "mkfifo"),
    ("posix", "mknod"),
    ("_posixsubprocess", "fork_exec"),
    ("subprocess", "_fork_exec"),
    ("signal", "signal"),
    ("_signal", "signal"),
    ("_interpreters", "create"),
    ("_interpreters", "exec"),
    ("_interpreters", "run_string"),
    ("_interpreters", "run_func"),
    ("_interpreters", "call"),
)
"""Callables that create a directory entry, start a process or install a frame callback with no audit event in
CPython 3.13 (#12177 review: `os.mkfifo` and `os.mknod`; `_posixsubprocess.fork_exec` is what `subprocess.Popen` runs
after its own event; Fable review of #12181: `signal.signal`, whose handler is called with the interrupted frame).
CPython 3.14 still raises none for `os.mkfifo`, `os.mknod` and `signal.signal`; `_posixsubprocess.fork_exec` raises
an event of its own from 3.14 on, and stays replaced all the same. The `_interpreters` entries are PEP 734's
subinterpreters, public from 3.14 as `concurrent.interpreters` and `InterpreterPoolExecutor` (Fable review of the
3.14 bump): a hook added with `sys.addaudithook` belongs to one interpreter, and creating, entering or running code in
another raises no event the guard sees, so code run there would write files the guard refuses here. Both public
modules reach the five calls through the `_interpreters` module object, never a name of their own.
The guards replace them with `refused_call` before arming, in `os`, `posix`, `signal`, `_interpreters` and the module
that holds each by name, so code past the validator cannot reach them there."""


def refused_call(*args, **kwargs):
    raise PermissionError("blocked by the sandbox: a call the audit hook cannot see")


def disable_unaudited_calls():
    """Replace `UNAUDITED_CALLS` in the modules that are loaded or load without side effects."""
    import importlib

    for module_name, name in UNAUDITED_CALLS:
        module = sys.modules.get(module_name)
        if module is None and module_name.startswith(("posix", "_posix", "signal", "_signal", "_interpreters")):
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                continue
        if module is not None and hasattr(module, name):
            setattr(module, name, refused_call)


def sets_code(event, args):
    """A `function.__code__` assignment, which would run a compiled code object without an `exec` event."""
    return event == "object.__setattr__" and len(args) > 1 and args[1] == "__code__"


def ctypes_helper_addresses():
    """The addresses of `IMPORT_CTYPES_HELPERS`, read when the plot guard is built, before it is armed (importing
    `_ctypes` opens its shared library); empty where `_ctypes` is missing."""
    try:
        import _ctypes
    except ImportError:
        return frozenset()
    return frozenset(getattr(_ctypes, name) for name in IMPORT_CTYPES_HELPERS if hasattr(_ctypes, name))


EXEC_DENY_ENV = "ANYPLOT_DENY_EXEC"
"""`required` (lets-plot's row of `agents/renderer/commands.py`) makes arming the plot guard fail when the kernel
filter is not in place (`ExecDenyUnavailable`); unset, and in data and convert mode, which never get a row's
environment, a guard installs it where it can and reports where it cannot."""
EXEC_DENY_EXIT = 3
"""Plot mode's exit code when `ANYPLOT_DENY_EXEC=required` and the filter is not in place: the plot never ran."""
EXEC_PROBE_PATH = "/nonexistent/anyplot-exec-probe"
"""The program `install_exec_deny` tries to start once the filter is installed: with the filter the kernel refuses the
call with EPERM before it looks the path up, without it the path does not exist (ENOENT), so no probe starts a program."""
PR_SET_NO_NEW_PRIVS = 38
SECCOMP_SET_MODE_FILTER = 1
SECCOMP_FILTER_FLAG_TSYNC = 1
SECCOMP_RET_ALLOW = 0x7FFF0000
SECCOMP_RET_ERRNO = 0x00050000
SECCOMP_DATA_NR = 0  # offsetof(struct seccomp_data, nr)
SECCOMP_DATA_ARCH = 4  # offsetof(struct seccomp_data, arch)
BPF_LD_W_ABS = 0x20
BPF_JEQ_K = 0x15
BPF_JGE_K = 0x35
BPF_RET_K = 0x06
X32_SYSCALL_BIT = 0x40000000
EXEC_DENY_MACHINES = {
    # machine: (AUDIT_ARCH_*, the seccomp syscall, execve and execveat, whether the x32 ABI exists)
    "x86_64": (0xC000003E, 317, (59, 322), True),
    "aarch64": (0xC00000B7, 277, (221, 281), False),
}
"""The syscall numbers of the two machines the renderer image is built for (linux/audit.h, the kernel's syscall
tables); another machine gets no filter (`unsupported`)."""


class ExecDenyUnavailable(Exception):
    """`ANYPLOT_DENY_EXEC=required`, and the filter could not be installed: the code must not run."""


def exec_deny_program(arch, denied, x32):
    """The classic BPF program of the filter as `(code, jt, jf, k)` instructions: `execve` and `execveat` fail with
    EPERM, as does every syscall of another architecture (a 32-bit `int 0x80` on x86_64) and every x32 syscall, which
    carry other numbers for the same calls; every other syscall is allowed."""
    checks = ([(BPF_JGE_K, X32_SYSCALL_BIT)] if x32 else []) + [(BPF_JEQ_K, number) for number in denied]
    program = [
        (BPF_LD_W_ABS, 0, 0, SECCOMP_DATA_ARCH),
        (BPF_JEQ_K, 0, len(checks) + 2, arch),  # another architecture: past the checks and the allow, to the refusal
        (BPF_LD_W_ABS, 0, 0, SECCOMP_DATA_NR),
    ]
    # A matching check jumps past the checks after it and the allow, to the refusal.
    program += [(code, len(checks) - index, 0, value) for index, (code, value) in enumerate(checks)]
    program += [(BPF_RET_K, 0, 0, SECCOMP_RET_ALLOW), (BPF_RET_K, 0, 0, SECCOMP_RET_ERRNO | errno.EPERM)]
    return program


def install_exec_deny():
    """Install a seccomp filter that refuses every `execve` and `execveat` of this process for good, its threads and
    every child included, and return `on`; or `unsupported` (not Linux on a machine of `EXEC_DENY_MACHINES`) or
    `unavailable` (the kernel or the sandbox refused the filter, or it did not take).

    The audit hook sees a process start from Python only; native code calls the kernel directly: lets-plot's
    Kotlin/Native bridge links an ImageMagick whose delegates start programs through `/bin/sh` and reads no policy
    file. With the filter the kernel refuses every such start with EPERM, whatever is on `PATH`. `fork` and threads
    stay allowed. `PR_SET_NO_NEW_PRIVS` lets an unprivileged process install it and keeps a later `execve` from
    gaining privileges; `SECCOMP_FILTER_FLAG_TSYNC` puts it on every thread already running (BLAS, Arrow and the
    bridge start some at import). A filter cannot be removed, and one the code adds later can only refuse more. It
    runs before the audit hook is added, which refuses its `ctypes` calls and the probe's `execv`.
    """
    import ctypes
    import platform

    machine = EXEC_DENY_MACHINES.get(platform.machine())
    if machine is None or not sys.platform.startswith("linux"):
        return "unsupported"
    arch, seccomp_number, denied, x32 = machine
    program = exec_deny_program(arch, denied, x32)

    class SockFilter(ctypes.Structure):
        _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte), ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint)]

    class SockFprog(ctypes.Structure):
        _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(SockFilter))]

    instructions = (SockFilter * len(program))(*(SockFilter(*instruction) for instruction in program))
    fprog = SockFprog(len(program), ctypes.cast(instructions, ctypes.POINTER(SockFilter)))
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        libc.prctl.restype = ctypes.c_int
        libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
        libc.syscall.restype = ctypes.c_long
        libc.syscall.argtypes = [ctypes.c_long, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
    except OSError, AttributeError:
        return "unavailable"
    if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        return "unavailable"
    # TSYNC answers a positive thread id when a thread cannot take the filter; only 0 installed it everywhere.
    if libc.syscall(seccomp_number, SECCOMP_SET_MODE_FILTER, SECCOMP_FILTER_FLAG_TSYNC, ctypes.byref(fprog)) != 0:
        return "unavailable"
    try:
        os.execv(EXEC_PROBE_PATH, [EXEC_PROBE_PATH])
    except OSError as exc:
        # Only the filter's EPERM proves it: ENOENT (or an EACCES on the path) means the call reached the lookup.
        return "on" if exc.errno == errno.EPERM else "unavailable"
    return "unavailable"


class DataGuard:
    """The audit hook of data mode: once armed, refuses every `open` and every `import`, native code, processes,
    sockets, filesystem changes and listings, every route to a frame, and every `exec` and `compile` but the
    snippet's own run and `CODE_BUILDERS`.

    `blocked` keeps the first refused event's family, so a run whose snippet caught the
    error is refused all the same. `paused()` lets the harness itself read frames while it
    prints a traceback, when no snippet code runs. `exec_deny` is the kernel filter's state
    for the end line (`install_exec_deny`): `off` until `arm` installs it; `exec_deny_required`
    makes `arm` refuse to run without it (the plot guard's, from `ANYPLOT_DENY_EXEC`).
    """

    def __init__(self):
        self.armed = False
        self.blocked = None
        self.paused_depth = 0
        self.entry = None  # the code object `arm` lets run once
        self.exec_deny = "off"
        self.exec_deny_required = False

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

        The kernel filter that refuses every program start goes in first (`install_exec_deny`; where
        `exec_deny_required` is set, a filter that is not in place raises `ExecDenyUnavailable`, and
        nothing runs), then the calls that change the filesystem or start a process without raising an
        audit event are replaced (`disable_unaudited_calls`), because the hook cannot see them.
        """
        self.entry = entry
        self.exec_deny = install_exec_deny()
        if self.exec_deny != "on" and self.exec_deny_required:
            raise ExecDenyUnavailable(self.exec_deny)
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
    filesystem changes), every `open` that writes anywhere but `outputs`, a `__code__` assignment, every `exec`
    but the plot's own run, `CODE_BUILDERS` and the module bodies of an import, and every frame (`FRAME_EVENTS`,
    `FRAME_ATTRIBUTES`) handed out while plot code is on the stack, but to `FRAME_READERS` and import bodies.

    Imports, reads and `compile` stay allowed (`PLOT_BLOCKED_PREFIXES`, `CODE_EVENTS`). A refusal raises
    `PermissionError`; `blocked` keeps the first refused event's family for a caller that wants it.
    """

    def __init__(self, outputs):
        super().__init__()
        self.outputs = frozenset(os.path.realpath(path) for path in outputs)
        self.plot_file = None
        self.import_ctypes_helpers = ctypes_helper_addresses()
        self.exec_deny_required = os.environ.get(EXEC_DENY_ENV) == "required"

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
        if self.calls_import_ctypes_helper(event, args):
            return False
        if event.startswith("ctypes."):
            return not self.native_caller()
        if event == "object.__getattr__":
            return len(args) > 1 and args[1] in FRAME_ATTRIBUTES and not self.lets_frame_out()
        if event == "sys._getframemodulename":
            return False  # a module name, no frame: `namedtuple` and `enum` ask for it
        if event.startswith(FRAME_EVENTS):
            return not self.lets_frame_out()
        return event.startswith(PLOT_BLOCKED_PREFIXES)

    def calls_import_ctypes_helper(self, event, args):
        """A `ctypes.call_function` of `IMPORT_CTYPES_HELPERS` (`ctypes.cast`) whose caller's nearest origin is an
        import, as scipy's `_lib._ccallback_c` makes while it is imported: Python 3.13 ran it with no event at all."""
        if event != "ctypes.call_function" or not args or args[0] not in self.import_ctypes_helpers:
            return False
        return self.nearest_origin(self.caller()) == "import"

    def lets_code_run(self, event, args):
        """The plot's code object once, `CODE_BUILDERS`, and code an import runs: walking up from the caller, an
        import frame (`IMPORT_FRAME_FILES`) comes before any frame of the plot file, so no plot code (a callback the
        plot handed to a library) sits between the import and the `exec`."""
        if self.is_entry(event, args):
            return True
        frame = self.caller()
        if builds_code(frame):
            return True
        return self.nearest_origin(frame) == "import"

    def lets_frame_out(self):
        """Whether a frame may be handed out (`FRAME_EVENTS`, `FRAME_ATTRIBUTES`): only to `FRAME_READERS` and to the
        module body of an import (an import frame before any plot frame, as for `exec`). Everything else is refused,
        plot code and library code the plot called (a callback or a `getattr` it hands to a library has the plot's
        frame above it, Fable review of #12177) as much as a stack with no plot frame at all: a worker thread runs a
        callable the plot submitted (`ThreadPoolExecutor.submit(sys._current_frames)`) with neither frame above it,
        and the frames it returned would reach `run_plot`'s locals and the guard itself (#12181 review). The
        interpreter's traceback of a failed plot needs no exception: it reads its frames through `traceback`'s
        summary builder, one of `FRAME_READERS`."""
        frame = self.caller()
        if reads_frames(frame):
            return True
        return self.nearest_origin(frame) == "import"

    def nearest_origin(self, frame):
        """Walking up from `frame`: `"plot"` when a frame of the plot file comes first, `"import"` when an import
        frame (`IMPORT_FRAME_FILES`) does, None when neither is on the stack."""
        while frame is not None:
            file_name = frame.f_code.co_filename
            if file_name == self.plot_file:
                return "plot"
            if file_name in IMPORT_FRAME_FILES:
                return "import"
            frame = frame.f_back
        return None

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
            except OSError, ValueError, TypeError:
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
    except ValueError, OSError:
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


def drawn_labels(figure, drawn, extents=None, canvas=None):
    """The content of the drawn texts, by role: what the plot shows, for the host's grounding (`grounding.py`).

    At most `LABEL_LIMIT` entries of `{"kind", "text"}`, each text cut to
    `LABEL_CHARS`: titles, axis labels, legend texts and annotations first, then tick
    labels (named by their axis, `x tick label`), then any other drawn text, a tick or
    axis label with the index of its axes in `figure.get_axes()` (`axes`), so a unit on
    one axis is checked against that axis's ticks only; and whether any drawn text was
    left out or cut (`labels_truncated`). Only
    texts the probe's draw rendered count, so a tick label outside the view is never
    listed, and neither is a text whose measured box (`extents`) lies wholly outside
    the `canvas`. A colorbar's tick labels and label are `colorbar tick label` and
    `colorbar label`, never one of the axes'. At most `TICK_LABELS_PER_AXIS` tick labels
    are kept per axis of each axes, so a second subplot keeps its share. The host reads
    it as untrusted data: the code under test can write any text.
    """
    kinds, _, _ = _text_kinds(figure)
    axes_of = {}  # id(text) -> the index of its axes in figure.get_axes(), for tick labels and axis labels
    for index, axes in enumerate(figure.get_axes()):
        colorbar = getattr(axes, "_colorbar", None) is not None
        for name in ("x", "y", "z"):
            axis = getattr(axes, f"{name}axis", None)
            if axis is None:
                continue
            for label in axis.get_ticklabels():
                kinds[id(label)] = "colorbar tick label" if colorbar else f"{name} tick label"
                axes_of[id(label)] = index
            if colorbar:
                kinds[id(axis.label)] = "colorbar label"
            axes_of[id(axis.label)] = index
    entries = []
    per_axis = {}
    truncated = False
    for key, text in drawn.items():
        box = (extents or {}).get(key)
        if box is not None and canvas is not None and _outside(box, *canvas):
            continue  # drawn, but off the canvas: not in the image
        kind = kinds.get(key, "text")
        if kind.endswith("tick label"):
            slot = (axes_of.get(key), kind)
            per_axis[slot] = per_axis.get(slot, 0) + 1
            if per_axis[slot] > TICK_LABELS_PER_AXIS:
                truncated = True  # the other axes keep their share of LABEL_LIMIT
                continue
        rank = 1 if kind.endswith("tick label") else 2 if kind == "text" else 0
        entries.append((rank, kind, key, text))
    entries.sort(key=lambda entry: entry[0])
    labels = []
    budget = LABEL_TOTAL_CHARS
    for _, kind, key, text in entries[:LABEL_LIMIT]:
        try:
            content = str(text.get_text())
        except Exception:
            truncated = True
            continue
        if min(len(content), LABEL_CHARS) > budget:
            truncated = True
            break
        budget -= min(len(content), LABEL_CHARS)
        truncated = truncated or len(content) > LABEL_CHARS
        label = {"kind": kind, "text": content[:LABEL_CHARS]}
        if key in axes_of:
            label["axes"] = axes_of[key]
        labels.append(label)
    # Any drawn text left out: the host then never claims that a requested text is missing.
    return labels, truncated or len(entries) > LABEL_LIMIT


def _outside(box, width, height):
    """Whether a text box lies wholly outside the `width` x `height` canvas."""
    return box[2] <= 0 or box[3] <= 0 or box[0] >= width or box[1] >= height


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


def _renderer(figure):
    """The figure's Agg renderer. plotnine saves a figure it built with `Figure()`, whose canvas is the base class
    and has no renderer; `savefig` to PNG switches it to Agg anyway, so the probe does the same first."""
    if not hasattr(figure.canvas, "get_renderer"):
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        FigureCanvasAgg(figure)
    return figure.canvas.get_renderer()


def probe(figure, dpi):
    """What the figure will look like on the canvas, measured before it is saved."""
    renderer = _renderer(figure)  # before the recording draw: the base canvas's `draw` draws nothing (plotnine)
    drawn = _draw_recording_texts(figure)
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
    try:
        # Without the key the host checks no requested text; an empty list would read as "nothing drawn".
        figure_canvas = (float(width_in) * figure.dpi, float(height_in) * figure.dpi)  # the extents' pixels
        labels, truncated = drawn_labels(figure, drawn, extents, figure_canvas)
        texts_part = {"labels": labels, "labels_truncated": truncated}
    except Exception:  # the texts are for the reply's grounding; they never break the probe
        texts_part = {}
    return {
        **texts_part,
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


def _in_view(x, y, box, slack=1.0):
    """Whether a display point lies within the axes box (a mark or anchor outside it is clipped, never drawn)."""
    return box.x0 - slack <= x <= box.x1 + slack and box.y0 - slack <= y <= box.y1 + slack


def _bar_ends(axes, box):
    """Every visible bar of the axes inside its view as `(centre, end, width, base)` in display pixels along its
    orientation, plus a flag whether it draws a path effect (a shadow), and the orientation of the first bar container.

    For a vertical bar the centre is its x centre, the end the y of the side away from the
    baseline, the base the y of the baseline side and the width its pixel width; a
    horizontal bar swaps the axes. End and base come from the bar's data coordinates, so an
    inverted or logarithmic value axis puts the end where the bar ends on the canvas. A bar
    with a missing value (NaN geometry) or a rectangle outside the axes box (a zoomed view)
    is left out: it draws nothing, and a NaN would void the probe's JSON. A bar whose
    rectangle meets the view counts, even when its centre lies past a value-axis limit.
    """
    bars = []
    orientation = None
    for container in axes.containers:
        if type(container).__name__ != "BarContainer":
            continue
        horizontal = getattr(container, "orientation", "vertical") == "horizontal"
        orientation = orientation or ("horizontal" if horizontal else "vertical")
        for patch in container.patches:
            if not patch.get_visible():
                continue
            extent = patch.get_window_extent()
            x, y, w, h = patch.get_x(), patch.get_y(), patch.get_width(), patch.get_height()
            if horizontal:
                (end, _), (base, _) = axes.transData.transform([(x + w, y), (x, y)])
                bar = ((extent.y0 + extent.y1) / 2, end, extent.y1 - extent.y0, base)
            else:
                (_, end), (_, base) = axes.transData.transform([(x, y + h), (x, y)])
                bar = ((extent.x0 + extent.x1) / 2, end, extent.x1 - extent.x0, base)
            # Drawn when its rectangle meets the view: a bar zoomed past on its value axis still shows its end.
            meets = extent.x0 <= box.x1 and extent.x1 >= box.x0 and extent.y0 <= box.y1 and extent.y1 >= box.y0
            if not all(math.isfinite(float(value)) for value in bar) or not meets:
                continue
            bars.append((*(float(value) for value in bar), bool(patch.get_path_effects())))
    return bars, orientation


def _point_marks(axes, box):
    """The display positions of the axes' visible point marks (scatter marks, and the markers of a `plot` call that
    draws no line, `ax.plot(x, y, "o")`) and of the vertices of its lines of three or more, finite and inside the
    axes box only."""
    import numpy as np

    scatter, vertices = [], []
    for collection in axes.collections:
        if type(collection).__name__ != "PathCollection" or not collection.get_visible():
            continue
        offsets = np.asarray(collection.get_offsets(), dtype=float).reshape(-1, 2)
        scatter.append(collection.get_offset_transform().transform(offsets))
    for line in axes.get_lines():
        if not line.get_visible():
            continue
        xy = np.asarray(line.get_xydata(), dtype=float).reshape(-1, 2)
        markers_only = line.get_linestyle() in ("None", "none", "", " ") and line.get_marker() not in (None, "None", "")
        if markers_only:
            scatter.append(line.get_transform().transform(xy))
        elif len(xy) >= 3:  # two-vertex lines are rules, brackets and reference lines
            vertices.append(line.get_transform().transform(xy))
    empty = np.empty((0, 2))

    def kept(parts):
        points = np.concatenate(parts) if parts else empty
        inside = (
            np.isfinite(points).all(axis=1)
            & (points[:, 0] >= box.x0 - 1)
            & (points[:, 0] <= box.x1 + 1)
            & (points[:, 1] >= box.y0 - 1)
            & (points[:, 1] <= box.y1 + 1)
        )
        return points[inside]

    return kept(scatter), kept(vertices)


def _label_anchors(axes, box, renderer):
    """The visible texts of the axes placed at a data coordinate, with their anchors in display pixels.

    An annotation counts when its `xycoords` is "data" (`ax.annotate`, `ax.bar_label`), any
    other text when it uses the data transform (`ax.text` at a data position). A callout in
    axes coordinates is no value label. Like matplotlib's own draw, an annotation whose point
    lies outside the axes is skipped unless it is set to draw there (`annotation_clip=False`),
    and so is a plain text clipped to the axes (`clip_on=True`) outside them; a text at an
    infinite position is skipped too.
    """
    found = []
    for text in axes.texts:
        if not text.get_visible() or not text.get_text().strip():
            continue
        if type(text).__name__ == "Annotation":
            if callable(text.xycoords):
                # `bar_label(label_type="center")` anchors at a share of its bar's box: a callable returning it.
                try:
                    frame = text.xycoords(renderer)
                    anchor = (frame.x0 + text.xy[0] * frame.width, frame.y0 + text.xy[1] * frame.height)
                except Exception:
                    continue
            elif text.xycoords == "data":
                anchor = axes.transData.transform(text.xy)
            else:
                continue
            clipped = text.get_annotation_clip() is not False
        elif text.get_transform() == axes.transData:
            anchor = axes.transData.transform(text.get_position())
            clipped = bool(text.get_clip_on())
        else:
            continue
        x, y = float(anchor[0]), float(anchor[1])
        if not (math.isfinite(x) and math.isfinite(y)) or (clipped and not _in_view(x, y, box)):
            continue
        found.append((text, x, y))
        if len(found) >= DENSITY_LABEL_LIMIT:
            break
    return found


def _on_bar_ends(scatter, bar_array, horizontal, value_extent):
    """Which scatter marks sit on a bar's end, matched in chunks of `DENSITY_MARK_LIMIT` marks so the pairwise
    arrays stay at most `DENSITY_MARK_LIMIT` squared, however many marks the plot draws."""
    import numpy as np

    on_bar = np.zeros(len(scatter), dtype=bool)
    if not len(bar_array) or not len(scatter):
        return on_bar
    for start in range(0, len(scatter), DENSITY_MARK_LIMIT):
        chunk = scatter[start : start + DENSITY_MARK_LIMIT]
        along, across = (chunk[:, 1], chunk[:, 0]) if horizontal else (chunk[:, 0], chunk[:, 1])
        near_centre = np.abs(along[:, None] - bar_array[None, :, 0]) <= bar_array[None, :, 2] / 2 + 1
        near_end = np.abs(across[:, None] - bar_array[None, :, 1]) <= 0.03 * value_extent
        on_bar[start : start + len(chunk)] = (near_centre & near_end).any(axis=1)
    return on_bar


def density_report(figure, dpi):
    """Per axes (at most `DENSITY_AXES_LIMIT`, only those with bars or point marks): how many marks it draws and how
    many of them carry a value label or a decoration, with the space a label has.

    `bars` counts the visible bars, `marks` bars plus scatter marks plus line vertices
    (point marks on a bar's end count as decorations instead), `labelled` the texts at a
    data coordinate whose anchor sits on a mark (at or past a bar's end, inside a bar's
    segment, or on a point; `_label_anchors`), `numeric_labels` those of them that are one
    number (`_is_number_text`: a named point, `Firm 3`, is not), `labelled_bars` the bar
    positions that carry a label (a stacked bar's segments share one), `decorated` the point marks
    on a bar's end plus the bars that draw a path effect such as a shadow, `slot_px` the
    space one bar label has along the category axis (`_label_slot`, from the labelled bars
    only) and `label_px` the median extent of the bar labels along that axis. Pixels are the
    saved image's. The host turns this into G11.
    """
    import numpy as np

    scale = (dpi or figure.dpi) / figure.dpi
    renderer = _renderer(figure)
    report = []
    for axes in figure.get_axes():
        if len(report) >= DENSITY_AXES_LIMIT:
            break
        try:
            box = axes.get_window_extent(renderer)
            bars, orientation = _bar_ends(axes, box)
            scatter, vertices = _point_marks(axes, box)
        except Exception:
            continue
        if not bars and not len(scatter) and not len(vertices):
            continue
        horizontal = orientation == "horizontal"
        width, height = float(box.width), float(box.height)
        value_extent = width if horizontal else height
        bar_array = np.asarray([bar[:3] for bar in bars[:DENSITY_MARK_LIMIT]], dtype=float).reshape(-1, 3)
        # A scatter mark on a bar's end is a decoration (the catalogue's dots on its bar tops), not a data mark.
        on_bar = _on_bar_ends(scatter, bar_array, horizontal, value_extent)
        points = np.concatenate([scatter[~on_bar], vertices])[:DENSITY_MARK_LIMIT]
        segments = np.asarray([bar[3] for bar in bars[:DENSITY_MARK_LIMIT]], dtype=float)
        slack = DENSITY_BAR_SLACK * value_extent
        labelled, numeric, label_sizes, labelled_bars = 0, 0, [], []
        for text, x, y in _label_anchors(axes, box, renderer):
            along, across = (y, x) if horizontal else (x, y)
            hit = None
            if len(bar_array):
                # On a bar: past its end by at most `slack`, or inside its segment (`label_type="center"`).
                low = np.minimum(bar_array[:, 1], segments) - slack
                high = np.maximum(bar_array[:, 1], segments) + slack
                matches = (
                    (np.abs(along - bar_array[:, 0]) <= bar_array[:, 2] / 2 + 1) & (across >= low) & (across <= high)
                )
                if matches.any():
                    hit = int(np.argmax(matches))
            on_a_point = len(points) and bool(
                (
                    (np.abs(x - points[:, 0]) <= DENSITY_POINT_SLACK[0] * width + 2)
                    & (np.abs(y - points[:, 1]) <= DENSITY_POINT_SLACK[1] * height + 2)
                ).any()
            )
            if hit is None and not on_a_point:
                continue
            labelled += 1
            numeric += _is_number_text(text.get_text())
            if hit is not None:
                labelled_bars.append((float(bar_array[hit, 0]), float(bar_array[hit, 2])))
                try:
                    extent = text.get_window_extent(renderer)
                except Exception:
                    continue
                size = float(extent.height if horizontal else extent.width)
                if math.isfinite(size):
                    label_sizes.append(size)
        slot = _label_slot(labelled_bars)
        report.append(
            {
                "bars": len(bars),
                "marks": len(bars) + int((~on_bar).sum()) + len(vertices),
                "labelled": labelled,
                "numeric_labels": numeric,
                "labelled_bars": len({round(centre, 1) for centre, _ in labelled_bars}),
                "decorated": int(on_bar.sum()) + sum(1 for bar in bars if bar[4]),
                "slot_px": None if slot is None else round(slot * scale, 1),
                "label_px": round(float(np.median(label_sizes)) * scale, 1) if label_sizes else None,
            }
        )
    return report


_NUMBER_TEXT = re.compile(
    r"[$€£¥]?\s?[+\-−]?\s?[$€£¥]?\s?\d[\d.,'    ]*"
    r"(?:\s?(?:%|‰|[$€£¥]|[^\W\d_]{1,5}\.?(?:\s[^\W\d_]{1,5}\.?)?))?"
)
_MATH_MARKUP = re.compile(r"\\mathdefault|\\mathrm|\\,|[{}$]")


def _is_number_text(text):
    """Whether a label is one number (`5.30`, `6,5 Mio.`, `12 %`, `5,30 €`), mathtext read as drawn; a name is not."""
    stripped = text.strip()
    if len(stripped) > 2 and stripped.startswith("$") and stripped.endswith("$") and stripped.count("$") == 2:
        stripped = _MATH_MARKUP.sub("", stripped).strip()
    return _NUMBER_TEXT.fullmatch(stripped) is not None


def _label_slot(labelled_bars):
    """The space one bar label has along the category axis: the median distance from each labelled bar's centre to
    the nearest other labelled bar's centre, in display pixels, or None for fewer than two.

    Only labelled bars count, so unlabelled bars between them (an offset shadow series, a
    chart that labels only its extremes) leave the space as wide as it looks. Distances
    below half a bar width are one bar labelled twice (a stacked bar's segments) and are skipped.
    """
    import numpy as np

    if len(labelled_bars) < 2:
        return None
    centres = np.asarray([centre for centre, _ in labelled_bars], dtype=float)
    widths = np.asarray([bar_width for _, bar_width in labelled_bars], dtype=float)
    distances = np.abs(centres[:, None] - centres[None, :])
    distances[distances < np.median(widths) / 2] = np.inf
    nearest = distances.min(axis=1)
    nearest = nearest[np.isfinite(nearest)]
    return float(np.median(nearest)) if len(nearest) else None


def _tick_kind(axis):
    """What an axis's tick labels write: `number` (a numeric scale and formatter), `date`, `category`, `fixed`
    (labels the code set itself, `set_xticks(positions, labels)`: often the data's own categories), `none` (no labels)
    or `other`."""
    major = axis.get_major_formatter()
    formatter = type(major).__name__
    if formatter == "NullFormatter":
        return "none"
    # `set_ticklabels` (and `set_xticks(positions, labels)`) installs a FuncFormatter over a dict of the labels.
    labels_dict = getattr(getattr(major, "func", None), "func", None)
    if formatter == "FixedFormatter" or getattr(labels_dict, "__name__", "") == "_format_with_dict":
        return "fixed"
    # A date formatter over coordinates converted beforehand (`mdates.date2num`) leaves the converter unset.
    if "Date" in formatter or "dates" in type(major).__module__:
        return "date"
    get_converter = getattr(axis, "get_converter", None)
    converter = get_converter() if get_converter is not None else getattr(axis, "converter", None)
    if converter is None:
        return "number"
    module = type(converter).__module__
    if "dates" in module:
        return "date"
    if "category" in module:
        return "category"
    return "other"


def tick_axes(figure):
    """Per axes of `figure.get_axes()`, in that order (the `axes` index of `drawn_labels`), what each of its axes'
    tick labels write (`_tick_kind`), so the host checks the decimal mark (G12) of numeric ticks only, never of a
    date (`14.10`) or a category the data names (`3.11`)."""
    report = []
    for axes in figure.get_axes():
        entry = {}
        for name in ("x", "y", "z"):
            axis = getattr(axes, f"{name}axis", None)
            if axis is None:
                continue
            try:
                entry[name] = _tick_kind(axis)
            except Exception:
                entry[name] = "other"
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
            density = density_report(self, kwargs.get("dpi"))
        except Exception:  # nor does the density report
            density = []
        if density:
            report["density"] = density
        try:
            report["tick_axes"] = tick_axes(self)
        except Exception:  # nor does the tick-axes report
            pass
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
        except ValueError, TypeError:  # an index name that is also a column, a MultiIndex level clash
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


def write_status(handle, code, measure, exits=DATA_EXIT):
    """`status.json`: the run's `DATA_EXIT` code and, for a broken cap, the measured value and the cap.

    The host reads it whatever the launcher's exit code says: Cloud Run's `sandbox do`
    reports every non-zero exit of the sandboxed process as its own death by SIGPIPE
    (-13), so the exit code alone cannot carry `too_large` from the sandbox. The handle
    was opened before the guard; the snippet cannot reach it, and a write to an open
    file raises no audit event.
    """
    if handle is None:
        return
    reason = next((name for name, value in exits.items() if value == code), None)
    report = {"exit": code, "reason": reason}
    for key in ("measured", "limit"):
        if isinstance(measure.get(key), int):
            report[key] = measure[key]
    if measure.get("damage") in CONVERT_DAMAGES:
        report["damage"] = measure["damage"]
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
    except OSError, SyntaxError, ValueError:
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
                _report("end", **_usage(), exec_deny=guard.exec_deny)
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


def warm_cairo(source):
    """Import cairosvg before the plot guard is armed, when the plot names pygal or cairosvg.

    pygal's `render_to_png` imports cairosvg lazily, and cairosvg's import loads libcairo through
    cairocffi, which first asks `ctypes.util.find_library` for three library names: each runs
    `ldconfig -p`, then `gcc` through a temporary file and `ld` where they are installed. On the
    spike's developer machine (Python 3.14.6) `ctypes.util`'s own module body also opens libc
    (`ctypes.dlopen`), which the guard refuses, so every pygal render failed there (2026-10-24).
    In the renderer image (Python 3.14.9, no compiler) the import raises no `ctypes.dlopen`,
    `find_library` swallows the refused `ldconfig` as an `OSError`, and cairocffi then opens
    `libcairo.so.2` by name; the import here keeps a render from depending on refused process
    starts, at no cost the measurement could tell from noise (five renders each way, 2026-10-26).
    cffi's `dlopen` and its calls into libcairo raise no audit event, so the one import serves the
    render. A missing package (a developer machine without the `lib-pygal` extra, or without
    libcairo) is skipped, and the plot's own `import cairosvg` reports it under the guard.
    """
    if b"pygal" not in source and b"cairosvg" not in source:
        return
    import importlib

    try:
        importlib.import_module("cairosvg")
    except Exception:
        pass


def hide_frames():
    """Replace the two stdlib helpers that hand out their caller's frame, before the plot guard is armed.

    The guard refuses a frame to plot code and to library code the plot called (`lets_frame_out`), so
    `inspect.currentframe()` and `logging.currentframe()` would raise where libraries expect a frame or None:
    pandas' `find_stack_level` walks frames before every warning, and every logging call looks up its caller.
    Both read None as "no frame support": pandas reports its warning at level 0, a log record names
    "(unknown file)". `inspect.currentframe` answers its caller's frame to one of `FRAME_READERS` (plotnine's
    `Environment.capture`, which needs the plot's namespace) and None to everyone else (`frame_for_readers`). The
    plot reaches neither module past the validator (both are banned imports).
    """
    import inspect

    inspect.currentframe = frame_for_readers
    logging.currentframe = no_frame


def no_frame():
    """What `logging.currentframe` answers in plot mode: no frame (`hide_frames`)."""
    return None


def frame_for_readers():
    """What `inspect.currentframe` answers in plot mode: the caller's frame to one of `FRAME_READERS`, else None.

    `sys._getframe` raises the audit event the plot guard decides on; the guard skips this helper's own frame
    (`caller` walks past the harness file) and judges the chain above it, as it does for every other reader. A
    refusal is swallowed here, because the callers of `inspect.currentframe` expect a frame or None, never an error
    (pandas' `find_stack_level` before every warning).
    """
    try:
        return sys._getframe(1)
    except PermissionError:
        return None


def run_plot(path, guard):
    """Run the plot file as `__main__` under `guard`, the way `runpy.run_path` would.

    The file is read and compiled before the guard is armed, and the guard lets exactly
    that code object run once: every other `exec` the plot reaches is refused. `ctypes` is
    loaded first, because its import opens a library (`ctypes.dlopen`) and numpy, pandas and
    matplotlib reach it lazily; `warm_scikit_learn` runs the process lookups scikit-learn
    would otherwise make under the guard, and `warm_cairo` imports cairosvg (libcairo through
    cairocffi, with the same `ldconfig` lookups) when the plot names pygal or cairosvg. No
    bytecode is written: the guard refuses the writes.
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
    warm_cairo(source)
    hide_frames()
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


def chain_matches(frame, chain):
    """Whether `frame` and the frames above it run the `(file suffix, function)` pairs of `chain`, in order."""
    for function in chain:
        if not is_one_of(frame, (function,)):
            return False
        frame = frame.f_back
    return True


class ConvertGuard(DataGuard):
    """The audit hook of convert mode: `DataGuard`, with no code to run at all, but for one `compile`.

    NumPy reads an `.npy` header, a dict literal, with `ast.literal_eval`, which compiles the
    text to a syntax tree (`compile` with `PyCF_ONLY_AST`, no code object): `CONVERT_AST_READERS`.
    Every `exec` is refused, as are every `open` and every `import` after the preload.
    """

    def lets_code_run(self, event, args):
        """Only NumPy's header compile: none of data mode's `CODE_BUILDERS` (`namedtuple`, dataclasses), which a
        reader of data files never needs (Copilot review of #12194), and no entry code object to run."""
        return event == "compile" and chain_matches(self.caller(), CONVERT_AST_READERS)


def load_converter():
    """`convert.py` next to this file (the image's `/opt/anyplot/convert.py`), loaded by path: `-I` puts no script
    directory on `sys.path`. Registered in `sys.modules` like an import."""
    import importlib.util

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONVERT_MODULE_FILE)
    spec = importlib.util.spec_from_file_location("anyplot_convert", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main_convert(path, guard=None):
    """Convert mode (module docstring): read the file, preload, arm `ConvertGuard`, write `out.csv`, `meta.json`
    and `status.json`."""
    _report("start")
    set_limits()
    sys.dont_write_bytecode = True
    try:
        status = open(DATA_STATUS_FILE, "w", encoding="utf-8")  # before the guard, which refuses every open
    except OSError:
        status = None
    measure = {}
    code = CONVERT_EXIT["error"]
    try:
        code = run_conversion(path, guard, measure)
    finally:
        write_status(status, code, measure, CONVERT_EXIT)
    return code


def run_conversion(path, guard, measure):
    """`main_convert` after the limits. Only the exception's class reaches stderr: its message may quote the file."""
    try:
        with open(path, "rb") as handle:
            data = handle.read(CONVERT_MAX_INPUT_BYTES + 1)
        request = {}
        if os.path.exists(CONVERT_REQUEST_FILE):
            with open(CONVERT_REQUEST_FILE, encoding="utf-8") as handle:
                request = json.loads(handle.read(CONVERT_MAX_REQUEST_BYTES))
    except OSError, ValueError:
        return CONVERT_EXIT["usage"]
    sheet = request.get("sheet") if isinstance(request, dict) else None
    if sheet is not None and not isinstance(sheet, str):
        return CONVERT_EXIT["usage"]
    if len(data) > CONVERT_MAX_INPUT_BYTES:
        measure.update(measured=len(data), limit=CONVERT_MAX_INPUT_BYTES)
        return CONVERT_EXIT["too_large"]
    converter = load_converter()
    converter.preload()
    guard = guard if guard is not None else ConvertGuard()
    with (
        open(DATA_OUT_FILE, "w", encoding="utf-8", newline="") as out,
        open(CONVERT_META_FILE, "w", encoding="utf-8") as meta,
    ):
        guard.arm()
        try:
            result = converter.convert(data, sheet)
            text = result.csv_text
            # Not ASCII-escaped: ten 255-character CJK sheet names would pass the host's 16 KiB cap as escapes.
            report = json.dumps(result.meta(), ensure_ascii=False)
        except converter.Refused as exc:
            if guard.blocked:
                return CONVERT_EXIT["blocked"]
            for key in ("measured", "limit"):
                value = getattr(exc, key, None)
                if isinstance(value, int) and not isinstance(value, bool):
                    measure[key] = value
            damage = getattr(exc, "damage", None)
            if isinstance(damage, str) and damage in CONVERT_DAMAGES:
                measure["damage"] = damage
            return CONVERT_EXIT.get(exc.reason, CONVERT_EXIT["error"])
        except BaseException as exc:  # MemoryError and SystemExit too: the code is the harness's own
            try:
                print(f"conversion failed: {type(exc).__name__}", file=sys.stderr, flush=True)
            except Exception:
                pass
            return CONVERT_EXIT["blocked"] if guard.blocked else CONVERT_EXIT["error"]
        finally:
            try:
                _report("end", **_usage(), exec_deny=guard.exec_deny)
            except Exception:
                pass
        if guard.blocked:
            return CONVERT_EXIT["blocked"]
        out.write(text)
        meta.write(report)
    return CONVERT_EXIT["ok"]


def main_exec(command):
    """Exec mode: run `command` (a language's own render command) as a child under the harness's limits.

    The start line goes out before the child starts, so the renderer tells a launcher that
    never ran the harness from a command that failed. The limits are set in this process
    and inherited; `RLIMIT_AS` and `RLIMIT_NPROC` arrive only when the renderer's command
    table applies them to the language. The child gets the sandbox's environment as it is
    and the working directory, where the code file and `data.csv` lie. Its exit code is the
    harness's; a signal death becomes 128 plus the signal, as a shell reports it.
    """
    import subprocess

    if command and command[0] == "--":
        command = command[1:]
    _report("start")
    if not command:
        print(f"usage: harness.py {EXEC_FLAG} -- <command> [args...]", file=sys.stderr)
        return 2
    set_limits()
    try:
        # The command is a row of the renderer's own table (`agents/renderer/commands.py`), never the request's.
        completed = subprocess.run(command, check=False)
        code = completed.returncode
    except OSError as exc:
        print(f"{EXEC_FLAG}: cannot run {command[0]}: {type(exc).__name__}", file=sys.stderr)
        code = 127
    finally:
        try:
            _report("end", **_child_usage())
        except Exception:
            pass  # a closed stdout must not hide the command's own exit code
    return code if code >= 0 else 128 - code


def _child_usage():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"max_rss_mb": round(usage.ru_maxrss / 1024, 1), "cpu_s": round(usage.ru_utime + usage.ru_stime, 3)}


def main(argv):
    if len(argv) >= 2 and argv[1] == EXEC_FLAG:
        return main_exec(argv[2:])
    if len(argv) == 3 and argv[1] == DATA_FLAG:
        return main_data(argv[2])
    if len(argv) == 3 and argv[1] == CONVERT_FLAG:
        return main_convert(argv[2])
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
    # The HTML is altair's second file (314 of 325 catalogue files); it stays in the sandbox, nothing collects it.
    guard = PlotGuard((f"plot-{theme}.png", f"probe-{theme}.json", f"plot-{theme}.html"))
    try:
        run_plot(argv[1], guard)
    except ExecDenyUnavailable as exc:
        print(f"the sandbox could not refuse process starts ({exc}), which this library requires", file=sys.stderr)
        return EXEC_DENY_EXIT
    finally:
        try:
            _report("end", **_usage(), exec_deny=guard.exec_deny)
        except Exception:
            pass  # a closed stdout must not hide the plot's own exception
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
