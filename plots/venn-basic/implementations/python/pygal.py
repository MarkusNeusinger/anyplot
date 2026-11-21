""" anyplot.ai
venn-basic: Venn Diagram
Library: pygal 3.1.3 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os
import re
from itertools import combinations

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per set in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
JOIN = " & "  # separates set names in a combination
MIN_SETS = 2  # a third circle is placed only when the table has more sets than this
CANVAS = 2400  # square canvas, in pixels

# Columns: set these to your table's column names
COMBINATION = "Subscribed to"  # role: set_labels
RESPONDENTS = "Respondents (inclusive)"  # role: set_sizes
SETS_COMBINED = "Lists combined"  # role: intersections

# Data: replace this block with your own table, for example df = pd.read_csv("overlaps.csv")
# One row per combination of sets; the count is inclusive (a pair also counts the triple overlap).
df = pd.DataFrame(
    {
        COMBINATION: [
            "Weekly Digest",
            "Product Updates",
            "Community Forum",
            "Weekly Digest & Product Updates",
            "Weekly Digest & Community Forum",
            "Product Updates & Community Forum",
            "Weekly Digest & Product Updates & Community Forum",
        ],
        RESPONDENTS: [240, 180, 130, 70, 45, 40, 18],
        SETS_COMBINED: [1, 1, 1, 2, 2, 2, 3],
    }
)

# Plot: reads only df and the constants above
inclusive = {frozenset(name.split(JOIN)): size for name, size in zip(df[COMBINATION], df[RESPONDENTS], strict=True)}
set_names = list(dict.fromkeys(df.loc[df[SETS_COMBINED] == df[SETS_COMBINED].min(), COMBINATION]))
n_sets = len(set_names)

# Exclusive count of every region by inclusion-exclusion over the inclusive sizes
regions = {}
for k in range(1, n_sets + 1):
    for members in combinations(range(n_sets), k):
        inside = frozenset(set_names[i] for i in members)
        count = 0
        for j in range(k, n_sets + 1):
            for superset in combinations(range(n_sets), j):
                names = frozenset(set_names[i] for i in superset)
                if inside <= names:
                    count += (-1) ** (j - k) * inclusive.get(names, 0)
        regions[members] = count

# Circle radii: area proportional to set size
radii = np.array([np.sqrt(inclusive[frozenset([name])] / np.pi) for name in set_names])


def lens_area(d, r1, r2):
    """Area where two circles at distance d overlap."""
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return np.pi * min(r1, r2) ** 2
    a1 = r1**2 * np.arccos((d**2 + r1**2 - r2**2) / (2 * d * r1))
    a2 = r2**2 * np.arccos((d**2 + r2**2 - r1**2) / (2 * d * r2))
    tri = 0.5 * np.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))
    return a1 + a2 - tri


def center_distance(r1, r2, overlap):
    """Distance at which two circles overlap by the given area (bisection)."""
    lo, hi = abs(r1 - r2), r1 + r2
    for _ in range(80):
        mid = (lo + hi) / 2
        if lens_area(mid, r1, r2) > overlap:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# Circle centers: first two on a horizontal line, third found from its two distances
dist = {
    (i, j): center_distance(radii[i], radii[j], inclusive.get(frozenset([set_names[i], set_names[j]]), 0))
    for i, j in combinations(range(n_sets), 2)
}
centers = np.zeros((n_sets, 2))
centers[1] = (dist[(0, 1)], 0.0)
if n_sets > MIN_SETS:
    d01, d02, d12 = dist[(0, 1)], dist[(0, 2)], dist[(1, 2)]
    cx = (d01**2 + d02**2 - d12**2) / (2 * d01)
    centers[2] = (cx, -np.sqrt(max(d02**2 - cx**2, 0.0)))

# Label anchor of each region: the grid point deepest inside it
pad = radii.max() * 0.4
x_lo, x_hi = (centers[:, 0] - radii).min() - pad, (centers[:, 0] + radii).max() + pad
y_lo, y_hi = (centers[:, 1] - radii).min() - pad, (centers[:, 1] + radii).max() + pad
gx, gy = np.meshgrid(np.linspace(x_lo, x_hi, 500), np.linspace(y_lo, y_hi, 500))
gap = np.stack([np.hypot(gx - c[0], gy - c[1]) - r for c, r in zip(centers, radii, strict=True)])
anchors = {}
for members in regions:
    others = [i for i in range(n_sets) if i not in members]
    depth = np.min([-gap[i] for i in members], axis=0)
    if others:
        depth = np.minimum(depth, np.min([gap[i] for i in others], axis=0))
    iy, ix = np.unravel_index(np.argmax(depth), depth.shape)
    anchors[members] = (gx[iy, ix], gy[iy, ix])

# Set names sit just outside their circle, above it or below it
middle = centers.mean(axis=0)
name_pos = []
for c, r in zip(centers, radii, strict=True):
    # above the circle, or below it for the circle under the middle
    above = c[1] >= middle[1]
    name_pos.append(c + np.array([0.0, (r + pad * 0.45) * (1 if above else -1)]))

# Style
style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE[:n_sets] * 2),
    value_colors=(INK,) * 16,
    value_label_font_size=56,
    opacity=0.45,
    opacity_hover=0.6,
    title_font_size=66,
    value_font_size=60,
    stroke_width=5,
)

title = "venn-basic · python · pygal · anyplot.ai"


# pygal prints a label 60 px right of and 60 px below its point; nudge (in data units) cancels that
nudge = (0.0, 0.0)


def circle_points(c, r, baseline):
    """Closed ring that starts on the fill baseline, so pygal's fill adds no stray edge."""
    t0 = np.arcsin(np.clip((baseline - c[1]) / r, -1, 1))
    return [(c[0] + r * np.cos(t), c[1] + r * np.sin(t)) for t in t0 + np.linspace(0, 2 * np.pi, 361)]


def build(xr, yr):
    chart = pygal.XY(
        width=CANVAS,
        height=CANVAS,
        style=style,
        fill=True,
        stroke=True,
        show_dots=False,
        show_legend=False,
        print_labels=True,
        print_values=False,
        show_x_guides=False,
        show_y_guides=False,
        show_x_labels=False,
        show_y_labels=False,
        title=title,
        margin=60,
        explicit_size=True,
        xrange=xr,
        range=yr,
        include_x_axis=False,
        zero=float(centers[:, 1].mean()),
        css=("file://style.css", "file://graph.css", "inline:.text-overlay text {text-anchor: middle}"),
    )
    baseline = float(centers[:, 1].mean())
    for name, c, r in zip(set_names, centers, radii, strict=True):
        ring = circle_points(c, r, baseline)
        chart.add(name, ring, stroke_style={"stroke-width": 0, "stroke-opacity": 0})
    # Outlines are separate unfilled series, so no fill baseline is stroked
    for name, c, r in zip(set_names, centers, radii, strict=True):
        ring = circle_points(c, r, baseline)
        chart.add(f"{name} outline", ring, fill=False, stroke=True)
    # Region counts and set names as native pygal value labels on invisible dots
    counts = [
        {"value": (anchors[m][0] - nudge[0], anchors[m][1] + nudge[1]), "label": str(count)}
        for m, count in regions.items()
    ]
    chart.add("Counts", counts, fill=False, stroke=False, show_dots=True, dots_size=0)
    names = [
        {"value": (p[0] - nudge[0], p[1] + nudge[1]), "label": f"{name} ({inclusive[frozenset([name])]})"}
        for name, p in zip(set_names, name_pos, strict=True)
    ]
    chart.add("Sets", names, fill=False, stroke=False, show_dots=True, dots_size=0)
    return chart


# First pass reads the plot area; second pass sets equal units on both axes so circles stay round
span_x, span_y = x_hi - x_lo, y_hi - y_lo
probe = build((x_lo, x_hi), (y_lo, y_hi))
plot_rect = re.search(r'class="plot">\s*<rect[^>]*>', probe.render().decode("utf-8")).group(0)
area_w, area_h = (float(re.search(f'{k}="([\\d.]+)"', plot_rect).group(1)) for k in ("width", "height"))
unit = max(span_x / area_w, span_y / area_h)
mid_x, mid_y = (x_lo + x_hi) / 2, (y_lo + y_hi) / 2
xr = (mid_x - unit * area_w / 2, mid_x + unit * area_w / 2)
yr = (mid_y - unit * area_h / 2, mid_y + unit * area_h / 2)
nudge = (60 * unit, 60 * unit)
chart = build(xr, yr)

# Output
svg_content = chart.render().decode("utf-8")
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=f"plot-{THEME}.png")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{ margin: 0; padding: 20px; background: {PAGE_BG}; display: flex; justify-content: center; }}
        svg {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    {svg_content}
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
