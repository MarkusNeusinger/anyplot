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
   as the faster variant);
4. wraps `matplotlib.figure.Figure.savefig` so that every save also writes
   `probe-<theme>.json` next to the plot: the figure size and dpi, the bounding
   boxes in display pixels of every text the probe's own draw rendered, overlaps
   between rendered tick labels per axis, annotations outside their axes, and the
   number of drawn point marks. Only rendered text counts: matplotlib keeps tick
   labels for locator positions outside the view interval and for hidden axes
   (`axis("off")`, a twin's), which report themselves visible but are never drawn,
   and an edge label one tick step past the view sat beyond the canvas in every
   line plot of spike X (a false G3);
5. runs the plot file with `runpy.run_path` as `__main__`;
6. prints `HARNESS {"event": "end", "max_rss_mb": ..., "cpu_s": ...}` when the plot
   file returns or raises; an exception still propagates, so its traceback reaches
   stderr and the exit code stays non-zero.

The probe feeds the advisory gates G3 (clipped text), G5 (annotation outside its
axes), G7 (tick-label overlap) and G8 (more point marks than data rows). It is
advisory because the code under test could tamper with it; the host never fails a
render on it. The same holds for the `HARNESS` lines: the code under test shares
stdout, so the host reads them as hints (a retry decision, a memory figure), never
as a verdict.
"""

import functools
import json
import math
import os
import resource
import runpy
import shutil
import sys


PROBE_LIMIT = 400  # text boxes recorded per figure
THEME_ENV = "ANYPLOT_THEME"
MARKER = "HARNESS"


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


def _report(event, **fields):
    print(f"{MARKER} {json.dumps({'event': event, **fields})}", flush=True)


def _usage():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {"max_rss_mb": round(usage.ru_maxrss / 1024, 1), "cpu_s": round(usage.ru_utime + usage.ru_stime, 3)}


def _box(extent):
    return [round(extent.x0, 1), round(extent.y0, 1), round(extent.x1, 1), round(extent.y1, 1)]


def _overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


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
    texts = []
    for text in drawn.values():
        if len(texts) >= PROBE_LIMIT:
            break
        try:
            box = [value * scale for value in _box(text.get_window_extent(renderer))]
        except Exception:
            continue
        if all(math.isfinite(value) for value in box):  # one text at an infinite coordinate never voids the probe
            texts.append({"kind": type(text).__name__, "box": box})
    tick_overlaps = 0
    annotations_outside = 0
    points = 0
    for axes in figure.get_axes():
        for axis in (axes.xaxis, axes.yaxis):
            boxes = []
            for label in axis.get_ticklabels():
                try:
                    if id(label) in drawn:
                        boxes.append(_box(label.get_window_extent(renderer)))
                except Exception:
                    continue
            tick_overlaps += sum(1 for left, right in zip(boxes, boxes[1:], strict=False) if _overlaps(left, right))
        axes_box = _box(axes.get_window_extent(renderer))
        for child in axes.texts:
            try:
                if child.get_visible() and type(child).__name__ == "Annotation":
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
    return {
        "figsize": [float(width_in), float(height_in)],
        "dpi": float(dpi or figure.dpi),
        "canvas": [
            round(float(width_in) * float(dpi or figure.dpi)),
            round(float(height_in) * float(dpi or figure.dpi)),
        ],
        "texts": texts,
        "tick_overlaps": tick_overlaps,
        "annotations_outside": annotations_outside,
        "points": points,
    }


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


def main(argv):
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
