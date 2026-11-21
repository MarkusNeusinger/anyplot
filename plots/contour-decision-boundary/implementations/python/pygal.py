"""anyplot.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-16
"""

import os
import re
import sys
from pathlib import Path


# Remove script directory from path to avoid name collision with the pygal package
_script_dir = str(Path(__file__).parent)
sys.path = [p for p in sys.path if p != _script_dir]

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402
from sklearn.datasets import make_moons  # noqa: E402
from sklearn.svm import SVC  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per class in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MESH_CELLS = 800  # mesh cells along the longer side; fine enough that the boundary shows no stair-steps
REGION_OPACITY = 0.26  # fill of the predicted regions, light enough that the points stay the strongest marks

MISCLASSIFIED_RING = "#AE3030"  # ring and legend swatch of the misclassified points

# Columns: set these to your table's column names
FEATURE_1 = "Feature 1"  # role: X1
FEATURE_2 = "Feature 2"  # role: X2
CLASS = "Class"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("points.csv")
X, y = make_moons(n_samples=150, noise=0.25, random_state=42)
df = pd.DataFrame({FEATURE_1: X[:, 0], FEATURE_2: X[:, 1], CLASS: y})

# Plot: reads only df and the constants above
df = df.dropna(subset=[FEATURE_1, FEATURE_2, CLASS]).reset_index(drop=True)
df[[FEATURE_1, FEATURE_2]] = df[[FEATURE_1, FEATURE_2]].astype(float)
features = df[[FEATURE_1, FEATURE_2]].to_numpy()
labels = df[CLASS].astype(str).to_numpy()
classes = sorted(set(labels))
class_index = np.searchsorted(classes, labels)

clf = SVC(kernel="rbf", C=1.0, gamma="scale").fit(features, labels)
wrong = clf.predict(features) != labels

# Plotted feature plane: the data range plus a margin
x_min, x_max = df[FEATURE_1].min() - 0.5, df[FEATURE_1].max() + 0.5
y_min, y_max = df[FEATURE_2].min() - 0.5, df[FEATURE_2].max() + 0.5

# Predictions on the mesh, one cell per prediction (cell centres)
step = max(x_max - x_min, y_max - y_min) / MESH_CELLS
x_edges = np.arange(x_min, x_max + step, step)
y_edges = np.arange(y_min, y_max + step, step)
x_centres = (x_edges[:-1] + x_edges[1:]) / 2
y_centres = (y_edges[:-1] + y_edges[1:]) / 2
xx, yy = np.meshgrid(x_centres, y_centres)
grid_class = np.searchsorted(classes, clf.predict(np.c_[xx.ravel(), yy.ravel()])).reshape(xx.shape)

# Style
imprint_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(*IMPRINT_PALETTE[:2], MISCLASSIFIED_RING),
    title_font_size=64,
    label_font_size=52,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
    opacity=1.0,
    opacity_hover=1.0,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=imprint_style,
    title="contour-decision-boundary · python · pygal · anyplot.ai",
    x_title=FEATURE_1,
    y_title=FEATURE_2,
    xrange=(x_min, x_max),
    range=(y_min, y_max),
    show_x_guides=True,
    show_y_guides=True,
    stroke=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(classes) + 1,
    legend_box_size=36,
    truncate_legend=-1,
    margin=40,
    print_values=False,
    css=[
        "file://style.css",
        "file://graph.css",
        f"inline:.guide.line, .axis.major.line {{ stroke: none !important; }} .dot {{ stroke: {INK}; stroke-width: 3; }} "
        f".serie-{len(classes)} .dot {{ stroke: {MISCLASSIFIED_RING} !important; stroke-width: 9 !important; }}",
    ],
)

# One series per class (correctly classified points), then the misclassified points
for i, label in enumerate(classes):
    keep = (class_index == i) & ~wrong
    chart.add(f"{CLASS} {label}", list(zip(df[FEATURE_1][keep], df[FEATURE_2][keep], strict=True)), dots_size=14)
chart.add(
    "Misclassified (large, red ring)",
    [
        {"value": (a, b), "color": IMPRINT_PALETTE[k % len(IMPRINT_PALETTE)]}
        for a, b, k in zip(df[FEATURE_1][wrong], df[FEATURE_2][wrong], class_index[wrong], strict=True)
    ],
    dots_size=22,
)

svg = chart.render(is_unicode=True)

# Data-to-pixel mapping, read off the tick guides pygal drew (value label -> guide position)
tick = r'<path d="M{pos}" class="[^"]*" /><text[^>]*>([^<]*)</text>'
x_ticks = [(float(lab), float(pos)) for pos, lab in re.findall(tick.format(pos=r"([\d.]+) [\d.]+ v[\d.]+"), svg)]
y_ticks = [(float(lab), float(pos)) for pos, lab in re.findall(tick.format(pos=r"[\d.]+ ([\d.]+) h[\d.]+"), svg)]
x_fit = np.polyfit(*zip(*x_ticks, strict=True), 1)
y_fit = np.polyfit(*zip(*y_ticks, strict=True), 1)

# Predicted regions: merge each mesh row into runs of one class, drawn as opaque rects
# inside one translucent group, so neighbouring cells never show seams
x_px = list(np.polyval(x_fit, x_edges))
y_px = list(np.polyval(y_fit, y_edges))
rects = []
for r in range(grid_class.shape[0]):
    row = grid_class[r]
    start = 0
    for c in range(1, len(row) + 1):
        if c == len(row) or row[c] != row[start]:
            top = min(y_px[r], y_px[r + 1]) - 0.4
            height = abs(y_px[r + 1] - y_px[r]) + 0.8
            left = x_px[start]
            width = x_px[c] - left
            rects.append(
                f'<rect x="{left:.2f}" y="{top:.2f}" width="{width:.2f}" height="{height:.2f}" '
                f'fill="{IMPRINT_PALETTE[row[start] % len(IMPRINT_PALETTE)]}"/>'
            )
            start = c
region_group = f'<g class="regions" opacity="{REGION_OPACITY}" clip-path="url(#plot-clip)">{"".join(rects)}</g>'

plot_open = svg.index('class="plot"')
bg_end = svg.index("/>", plot_open) + 2  # end of the plot background rect
clip = f'<clipPath id="plot-clip"><rect x="{x_px[0]:.2f}" y="{min(y_px):.2f}" width="{x_px[-1] - x_px[0]:.2f}" height="{abs(y_px[-1] - y_px[0]):.2f}"/></clipPath>'
# Frame the feature plane
frame = (
    f'<rect x="{x_px[0]:.2f}" y="{min(y_px):.2f}" width="{x_px[-1] - x_px[0]:.2f}" '
    f'height="{abs(y_px[-1] - y_px[0]):.2f}" fill="none" stroke="{INK_MUTED}" stroke-width="3"/>'
)
svg = svg[:bg_end] + clip + region_group + frame + svg[bg_end:]

cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>contour-decision-boundary - pygal</title>'
        f"<style>body{{margin:0;background:{PAGE_BG}}}svg{{max-width:100%;height:auto}}</style></head>"
        f"<body>{svg}</body></html>"
    )
