""" anyplot.ai
circos-basic: Circos Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
"""

import math
import os
import sys

import pandas as pd


# This file is named pygal.py: keep its own directory off sys.path so the real package imports
sys.path = [p for p in sys.path if p not in ("", ".")]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per segment in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GAP = 0.09  # radians of empty ring between two neighbouring segments
RING_PX = 755  # pixels per data unit of radius on the 2400 x 2400 canvas (measured)
RIBBON_FILL = 0.5
RIBBON_ALPHA = 0.6  # share of a segment's arc slot that a ribbon end occupies

LABEL_DX, LABEL_DY = 0.156, 0.066  # pygal's fixed label offset from its anchor point, in data units

# Columns: set these to your table's column names
SOURCE = "Source chromosome"  # role: source
TARGET = "Target chromosome"  # role: target
VALUE = "Connection strength"  # role: value
EXPRESSION = "Expression level at source"  # role: track_data

# Data: replace this block with your own table, for example df = pd.read_csv("links.csv")
df = pd.DataFrame(
    {
        SOURCE: ["Chr1", "Chr1", "Chr2", "Chr2", "Chr3", "Chr3", "Chr4", "Chr4", "Chr5", "Chr5"]
        + ["Chr6", "Chr6", "Chr7", "Chr7", "ChrX", "ChrX", "Chr1", "Chr4"],
        TARGET: ["Chr4", "ChrX", "Chr5", "Chr7", "Chr6", "Chr1", "Chr7", "Chr2", "ChrX", "Chr3"]
        + ["Chr1", "Chr2", "Chr5", "Chr6", "Chr3", "Chr4", "Chr6", "Chr6"],
        VALUE: [45, 70, 60, 48, 55, 30, 40, 35, 65, 28, 50, 32, 38, 26, 52, 24, 20, 22],
        EXPRESSION: [6.2, 6.2, 3.1, 3.1, 8.4, 8.4, 4.7, 4.7, 7.3, 7.3, 2.4, 2.4, 5.5, 5.5, 9.1, 9.1, 6.2, 4.7],
    }
)

# Plot: reads only df and the constants above
segments = list(dict.fromkeys(df[SOURCE].tolist() + df[TARGET].tolist()))
n = len(segments)
index = {name: i for i, name in enumerate(segments)}
flow = pd.concat([df.groupby(SOURCE, sort=False)[VALUE].sum(), df.groupby(TARGET, sort=False)[VALUE].sum()])
size = flow.groupby(level=0).sum().reindex(segments)  # arc length follows the total connection strength
rad_per_unit = (2 * math.pi - n * GAP) / size.sum()
start = {}
angle = GAP / 2
for name in segments:
    start[name] = angle
    angle += size[name] * rad_per_unit + GAP
track_level = df.groupby(SOURCE, sort=False)[EXPRESSION].mean().reindex(segments)

R_OUT, R_TRACK0, R_TRACK1, R_RIBBON = 1.0, 0.80, 0.93, 0.74
lo, hi = track_level.min(), track_level.max()

# Ribbon end slots: ends on one segment are ordered by where the partner sits, which limits crossings
ends = {name: [] for name in segments}
for row, (src, dst) in enumerate(zip(df[SOURCE], df[TARGET], strict=True)):
    ends[src].append((row, "s", (index[dst] - index[src]) % n))
    ends[dst].append((row, "t", (index[src] - index[dst]) % n))
slot = {}
for name in segments:
    cursor = start[name]
    for row, side, _ in sorted(ends[name], key=lambda e: -e[2]):
        width = df[VALUE].iloc[row] * rad_per_unit
        slot[(row, side)] = cursor + width / 2
        cursor += width


def polar(radius, theta):
    return (radius * math.cos(theta), radius * math.sin(theta))


def arc(radius, a0, a1, steps=40):
    return [polar(radius, a0 + (a1 - a0) * k / steps) for k in range(steps + 1)]


series = []  # (name, points, color, stroke width px, legend, dots)
for i, name in enumerate(segments):
    span = size[name] * rad_per_unit
    series.append(
        (name, arc(R_OUT, start[name], start[name] + span), IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)], 44, True, 0)
    )

track = []
for name in segments:
    span = size[name] * rad_per_unit
    level = R_TRACK0 + (R_TRACK1 - R_TRACK0) * (track_level[name] - lo) / (hi - lo)
    track += arc(level, start[name] + 0.01, start[name] + span - 0.01, 30) + [None]
series.append(("Inner ring: expression level", track[:-1], INK_SOFT, 10, True, 0))

labels = []
for name in segments:
    mid = start[name] + size[name] * rad_per_unit / 2
    x, y = polar(1.13, mid)
    x, y = x - LABEL_DX, y + LABEL_DY  # pygal draws a label right of and below its anchor point
    labels.append({"value": (x, y), "label": name})

for row in range(len(df)):
    p0, p2 = polar(R_RIBBON, slot[(row, "s")]), polar(R_RIBBON, slot[(row, "t")])
    pts = []
    for k in range(41):
        t = k / 40
        pts.append(((1 - t) ** 2 * p0[0] + t**2 * p2[0], (1 - t) ** 2 * p0[1] + t**2 * p2[1]))
    px = df[VALUE].iloc[row] * rad_per_unit * R_RIBBON * RING_PX * RIBBON_FILL
    series.append(("", pts, IMPRINT_PALETTE[index[df[SOURCE].iloc[row]] % len(IMPRINT_PALETTE)], px, False, 0))


def with_alpha(hex_color, alpha):
    r, g, b = (int(hex_color[k : k + 2], 16) for k in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"


# Ribbons are translucent so that crossings stay readable
colors = [s[2] if s[4] else with_alpha(s[2], RIBBON_ALPHA) for s in series] + [INK]
style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(colors),
    title_font_size=64,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=50,
    value_label_font_size=56,
    value_colors=tuple([INK] * len(colors)),
    stroke_width="inherit",
    stroke_width_hover="inherit",
    stroke_opacity="inherit",
    stroke_opacity_hover="inherit",
)

view = 1.22
xview = view * 1.3
chart = pygal.XY(
    style=style,
    width=2400,
    height=2400,
    title="circos-basic · python · pygal · anyplot.ai",
    x_title="Ribbon width: connection strength",
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    xrange=(-xview, xview),
    range=(-view, view),
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=28,
    truncate_legend=-1,
    print_labels=True,
    print_values=False,
    stroke=True,
    margin=30,
    include_x_axis=False,
)
for name, pts, _color, px, legend, _dots in series:
    chart.add(
        name if legend else None,
        pts,
        show_dots=False,
        allow_interruptions=True,
        stroke_style={"width": px, "linecap": "butt"},
    )
chart.add(None, labels, stroke=False, dots_size=1)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
