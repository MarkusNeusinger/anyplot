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
5. runs the plot file with `runpy.run_path` as `__main__`;
6. prints `HARNESS {"event": "end", "max_rss_mb": ..., "cpu_s": ...}` when the plot
   file returns or raises; an exception still propagates, so its traceback reaches
   stderr and the exit code stays non-zero.

**Data mode** (`python -I /opt/anyplot/harness.py --data snippet.py`, the renderer's
`POST /run-data`): the harness runs a data-generating snippet (`run_data_code`,
`agents/anyplot/tools/session.py`) instead of a plot. It prints the start line, sets the
same limits, imports numpy and pandas (pandas loads `ctypes` at import time), opens
`out.csv` for writing, and only then arms `DataGuard` with `sys.addaudithook`: from
there on the interpreter refuses `ctypes.*`, `os.system`, `os.exec*`, `os.posix_spawn`,
`os.spawn*`, `os.fork*`, `subprocess.*`, `socket.*`, every filesystem change
(`os.remove`, `os.rename`, `os.mkdir`, `os.chmod`, ...) and every `open` for writing.
An audit hook cannot be removed, and the snippet cannot reach it. It runs the snippet
with `runpy.run_path`, catches everything it raises (its traceback goes to stderr, the
exit code is `DATA_EXIT["error"]`, so the snippet cannot choose an exit code), and
takes `df` from the returned globals: a pandas DataFrame whose columns are no
MultiIndex, with a non-default index turned into columns (`reset_index`), its column
names as text, at most `DATA_MAX_ROWS` rows and `DATA_MAX_COLUMNS` columns and at most
`DATA_MAX_CSV_BYTES` of CSV (the parser's caps: `agents/anyplot/schemas.py` and
`data/parse.py`; a test pins them equal). It writes the CSV through the handle it opened
before the guard; a run the guard refused at any point writes nothing, even when the
snippet caught the error. Each refusal has its own exit code (`DATA_EXIT`); the host
maps a code to a fixed message and trusts nothing the snippet printed. The plot mode
does not arm the guard: savefig and the probe write files, and a render sweep of the
catalogue under the guard has not been run (it needs the renderer image).

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
import runpy
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
DATA_MAX_ROWS = 20_000  # agents/anyplot/schemas.py MAX_ROWS
DATA_MAX_COLUMNS = 50  # agents/anyplot/schemas.py MAX_COLUMNS
DATA_MAX_CSV_BYTES = 200 * 1024  # agents/anyplot/data/parse.py MAX_INPUT_BYTES
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
)
"""Audit events `DataGuard` refuses once it is armed (https://docs.python.org/3/library/audit_events.html)."""
_WRITE_MODES = frozenset("wax+")
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND


class DataGuard:
    """The audit hook of data mode: refuses native code, processes, sockets and writes once armed.

    `blocked` keeps the first refused event's family, so a run whose snippet caught the
    error is refused all the same.
    """

    def __init__(self):
        self.armed = False
        self.blocked = None

    def refuses(self, event, args):
        """Whether `event` with `args` is one the armed guard refuses."""
        if event == "open":
            mode = args[1] if len(args) > 1 else None
            flags = args[2] if len(args) > 2 else 0
            if isinstance(mode, str):
                return bool(_WRITE_MODES & set(mode))
            return isinstance(flags, int) and bool(flags & _WRITE_FLAGS)
        return event.startswith(DATA_BLOCKED_PREFIXES)

    def __call__(self, event, args):
        if not self.armed or not self.refuses(event, args):
            return
        if self.blocked is None:
            self.blocked = event.split(".", 1)[0]
        raise RuntimeError("blocked by the data sandbox")

    def arm(self):
        sys.addaudithook(self)
        self.armed = True


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


def frame_csv(frame):
    """The CSV text of a snippet's `df`, or the `DATA_EXIT` key of why there is none."""
    import pandas as pd

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
        return None, "too_many_rows"
    if len(frame.columns) > DATA_MAX_COLUMNS:
        return None, "too_many_columns"
    buffer = io.StringIO()
    frame.to_csv(buffer, index=False)
    text = buffer.getvalue()
    if len(text.encode("utf-8", errors="surrogatepass")) > DATA_MAX_CSV_BYTES:
        return None, "too_large"
    return text, None


def main_data(path, guard=None):
    """Data mode (module docstring): run the snippet under `DataGuard` and write its `df` to `out.csv`."""
    _report("start")
    set_limits()
    sys.dont_write_bytecode = True  # no .pyc write, which the guard would refuse
    import ctypes  # noqa: F401  (pandas loads it anyway; its load opens a library, so before the guard)

    import numpy  # noqa: F401
    import pandas  # noqa: F401

    guard = guard if guard is not None else DataGuard()
    with open(DATA_OUT_FILE, "w", encoding="utf-8", newline="") as out:
        guard.arm()
        try:
            namespace = runpy.run_path(path, run_name="__main__")
        except BaseException:  # SystemExit included: the snippet never chooses the exit code
            traceback.print_exc()
            return DATA_EXIT["blocked"] if guard.blocked else DATA_EXIT["error"]
        finally:
            try:
                _report("end", **_usage())
            except Exception:
                pass
        if guard.blocked:
            return DATA_EXIT["blocked"]
        try:
            text, refusal = frame_csv(namespace.get("df"))
        except Exception:
            traceback.print_exc()
            return DATA_EXIT["blocked"] if guard.blocked else DATA_EXIT["error"]
        if guard.blocked:  # a pandas method the snippet replaced reached the guard
            return DATA_EXIT["blocked"]
        if refusal is not None:
            return DATA_EXIT[refusal]
        out.write(text)
    return DATA_EXIT["ok"]


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
        runpy.run_path(argv[1], run_name="__main__")
    finally:
        try:
            _report("end", **_usage())
        except Exception:
            pass  # a closed stdout must not hide the plot's own exception
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
