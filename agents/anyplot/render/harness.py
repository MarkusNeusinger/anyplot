"""Render harness: runs one plot file inside the sandbox with resource limits and a savefig probe.

Usage, from the run directory (the CI render command with the harness in front):

    python -I /opt/anyplot/harness.py plot.py

It is a standalone script with no anyplot import, because it runs inside the
sandbox with the isolated interpreter (`-I`: no user site, no current directory on
`sys.path`, no `PYTHON*` environment). In order it:

1. sets resource limits: CPU seconds (`ANYPLOT_RLIMIT_CPU_S`, default 60), the
   largest file it may write (`ANYPLOT_RLIMIT_FSIZE_MB`, default 32) and, when
   `ANYPLOT_RLIMIT_AS_MB` is set, the address space (tuned in the sandbox spike);
2. wraps `matplotlib.figure.Figure.savefig` so that every save also writes
   `probe-<theme>.json` next to the plot: the figure size and dpi, the bounding
   boxes of all visible text in display pixels, tick-label overlaps per axis,
   annotations outside their axes, and the number of drawn point marks;
3. runs the plot file with `runpy.run_path` as `__main__`.

The probe feeds the advisory gates G3 (clipped text), G5 (annotation outside its
axes), G7 (tick-label overlap) and G8 (more point marks than data rows). It is
advisory because the code under test could tamper with it; the host never fails a
render on it.
"""

import json
import os
import resource
import runpy
import sys


PROBE_LIMIT = 400  # text boxes recorded per figure
THEME_ENV = "ANYPLOT_THEME"


def _limit(kind: int, value: int) -> None:
    try:
        soft, hard = resource.getrlimit(kind)
        if hard != resource.RLIM_INFINITY:
            value = min(value, hard)
        resource.setrlimit(kind, (value, hard))
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


def _box(extent):
    return [round(extent.x0, 1), round(extent.y0, 1), round(extent.x1, 1), round(extent.y1, 1)]


def _overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def probe(figure, dpi):
    """What the figure will look like on the canvas, measured before it is saved."""
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    width_in, height_in = figure.get_size_inches()
    scale = (dpi or figure.dpi) / figure.dpi
    texts = []
    for text in figure.findobj(lambda artist: hasattr(artist, "get_window_extent") and hasattr(artist, "get_text")):
        if len(texts) >= PROBE_LIMIT:
            break
        try:
            if not text.get_visible() or not text.get_text().strip():
                continue
            extent = text.get_window_extent(renderer)
        except Exception:
            continue
        texts.append({"kind": type(text).__name__, "box": [value * scale for value in _box(extent)]})
    tick_overlaps = 0
    annotations_outside = 0
    points = 0
    for axes in figure.get_axes():
        for axis in (axes.xaxis, axes.yaxis):
            boxes = []
            for label in axis.get_ticklabels():
                try:
                    if label.get_visible() and label.get_text().strip():
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
            with open(f"probe-{theme}.json", "w", encoding="utf-8") as handle:
                json.dump(report, handle)
        except OSError:
            pass
        return result

    Figure.savefig = savefig


def main(argv):
    if len(argv) != 2:
        print("usage: harness.py <plot file>", file=sys.stderr)
        return 2
    theme = os.environ.get(THEME_ENV, "light")
    if theme not in ("light", "dark"):
        print(f"{THEME_ENV} must be light or dark", file=sys.stderr)
        return 2
    set_limits()
    install_probe(theme)
    runpy.run_path(argv[1], run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
