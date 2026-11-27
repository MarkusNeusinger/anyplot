"""anyplot.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import math
import os
import sys


# Prevent this file (pygal.py) from shadowing the pygal package on sys.path
_this_dir = os.path.abspath(os.path.dirname(__file__))
sys.path[:] = [p for p in sys.path if os.path.realpath(p or ".") != _this_dir]

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per sector in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
RINGS = ["Adopt", "Trial", "Assess", "Hold"]  # time horizons, innermost first
ARC_SPAN = 270  # degrees covered by the sectors; the rest stays open for the ring names
OPENING_CENTER = -90  # direction of the open part (straight down)
HOLE = 0.5  # radius of the empty center
PLOT_ASPECT = 1.18  # plot-area width / height, so that circles stay circles
PPU = 158  # pixels per radius unit on the 2400 px canvas
LABEL_PX = 44  # font size of every label

# Columns: set these to your table's column names
NAME = "Innovation"  # role: name
RING = "Time horizon"  # role: ring
SECTOR = "Sector"  # role: sector

# Data: replace this block with your own table, for example df = pd.read_csv("radar.csv")
df = pd.DataFrame(
    [
        ("dbt Core", "Data Engineering", "Adopt"),
        ("Apache Iceberg", "Data Engineering", "Adopt"),
        ("Kafka Streams", "Data Engineering", "Trial"),
        ("Delta Lake", "Data Engineering", "Trial"),
        ("Vector Databases", "Data Engineering", "Assess"),
        ("Arrow Flight RPC", "Data Engineering", "Hold"),
        ("Service Mesh", "Cloud Platforms", "Adopt"),
        ("eBPF Monitoring", "Cloud Platforms", "Trial"),
        ("Green Cloud APIs", "Cloud Platforms", "Trial"),
        ("Multi-Cloud Orchestration", "Cloud Platforms", "Assess"),
        ("Serverless Edge", "Cloud Platforms", "Assess"),
        ("Quantum Cloud", "Cloud Platforms", "Hold"),
        ("Zero Trust Network", "Security", "Adopt"),
        ("AI-Native SOC", "Security", "Trial"),
        ("Supply Chain Security", "Security", "Trial"),
        ("Post-Quantum Crypto", "Security", "Assess"),
        ("Confidential Compute", "Security", "Assess"),
        ("Homomorphic Encryption", "Security", "Hold"),
        ("Platform Engineering", "DevOps", "Adopt"),
        ("AI Code Assistants", "DevOps", "Adopt"),
        ("FinOps Automation", "DevOps", "Trial"),
        ("Chaos Engineering", "DevOps", "Trial"),
        ("Internal Dev Portal", "DevOps", "Assess"),
        ("GitOps at Scale", "DevOps", "Hold"),
    ],
    columns=[NAME, SECTOR, RING],
)

# Plot: reads only df and the constants above
sectors = list(df[SECTOR].unique())
span = ARC_SPAN / len(sectors)
start = OPENING_CENTER + 180 - ARC_SPAN / 2 + ARC_SPAN  # first sector begins here and runs clockwise
outer = HOLE + len(RINGS)
y_lo, y_hi = -(outer + 0.8), outer + 2.2
half_x = (y_hi - y_lo) / 2 * PLOT_ASPECT


def polar(radius, angle_deg):
    """Cartesian point for a radius and an angle in degrees."""
    return (radius * math.cos(math.radians(angle_deg)), radius * math.sin(math.radians(angle_deg)))


def arc(radius, a0, a1, steps=90):
    """Points along a circle arc from angle a0 to a1."""
    return [polar(radius, a0 + (a1 - a0) * i / steps) for i in range(steps + 1)]


# Sector s covers angles [start - (s + 1) * span, start - s * span]
sector_angles = {s: (start - (i + 1) * span, start - i * span) for i, s in enumerate(sectors)}
ring_index = {r: i for i, r in enumerate(RINGS)}

colors = []
chart_series = []  # (title, points, line width, dash pattern, dot size); width 0 draws no line, dots None none

# Ring boundaries and sector dividers, drawn as thin guide lines
GUIDE = (2.5, "10,10")  # ring boundaries inside the plot
EDGE = (4, "none")  # outer edges and sector dividers
a_lo, a_hi = start - len(sectors) * span, start
for j in range(len(RINGS) + 1):
    radius = HOLE + j
    width, dash = EDGE if j in (0, len(RINGS)) else GUIDE
    chart_series.append((None, arc(radius, a_lo, a_lo + 360, 180), width, dash, None))
    colors.append(INK_MUTED)
for k in range(len(sectors) + 1):
    angle = a_hi - k * span
    chart_series.append((None, [polar(HOLE, angle), polar(outer, angle)], *EDGE, None))
    colors.append(INK_MUTED)

CHAR_W = 0.602 * LABEL_PX  # monospace advance of the label font
MARKER_R = 18  # marker radius in pixels


def text_box(left, center_y, text):
    """Pixel box (x0, y0, x1, y1) of a label whose text starts at left and is centered on center_y."""
    return (left, center_y - 0.6 * LABEL_PX, left + CHAR_W * len(text), center_y + 0.6 * LABEL_PX)


def clash(box, others, pad=14):
    """True when box comes within pad pixels of any box in others."""
    return any(
        box[0] < o[2] + pad and o[0] < box[2] + pad and box[1] < o[3] + pad and o[1] < box[3] + pad for o in others
    )


# Every box already taken on the canvas, in pixels around the center: ring names in the open part
# of the circle, sector headers along the outer edge, the center hole.
taken = [(-HOLE * PPU, -HOLE * PPU, HOLE * PPU, HOLE * PPU)]
texts = []  # (left, center_y, text) in pixels
for i, ring in enumerate(RINGS):
    cx, cy = (v * PPU for v in polar(HOLE + i + 0.5, OPENING_CENTER))
    left = cx - CHAR_W * len(ring) / 2
    texts.append((left, cy, ring))
    taken.append(text_box(left, cy, ring))
for sector in sectors:
    mid = sum(sector_angles[sector]) / 2
    radius = outer + 0.2
    while True:  # move out until the whole header box lies beyond the outer ring
        cx, cy = (v * PPU for v in polar(radius, mid))
        left = cx - CHAR_W * len(sector) / 2
        box = text_box(left, cy, sector)
        if min(math.hypot(x, y) for x in (box[0], box[2]) for y in (box[1], box[3])) > outer * PPU + 12:
            break
        radius += 0.02
    texts.append((left, cy, sector.upper()))
    taken.append(text_box(left, cy, sector.upper()))

# Items: a marker goes anywhere inside its own sector and ring band (layout, not data). Candidates
# near the sector's evenly spread slot come first; the first one whose label clears everything wins.
limit = half_x * PPU - 20
marks = {}
for sector in sectors:
    items = df[df[SECTOR] == sector].copy()
    items["band"] = items[RING].map(ring_index)
    items = items.sort_values("band", kind="stable")
    a0, a1 = sector_angles[sector]
    points = []
    for slot, (_, row) in enumerate(items.iterrows()):
        ideal = a1 - (slot + 0.5) * span / len(items)
        candidates = [
            (abs(a - ideal) / span + 0.5 * abs(dr), a, HOLE + row["band"] + 0.5 + dr, right)
            for a in (a0 + 4 + k * (span - 8) / 15 for k in range(16))
            for dr in (-0.3, -0.15, 0.0, 0.15, 0.3)
            for right in (True, False)
        ]
        width = CHAR_W * len(row[NAME])
        options = []
        for cost, angle, radius, right in candidates:
            mx, my = (v * PPU for v in polar(radius, angle))
            marker = (mx - MARKER_R, my - MARKER_R, mx + MARKER_R, my + MARKER_R)
            left = mx + MARKER_R + 8 if right else mx - MARKER_R - 8 - width
            box = text_box(left, my, row[NAME])
            # a label should stay inside its sector and the plot and clear of everything placed so far
            inside = all(
                (math.degrees(math.atan2(y, x)) - a0 - 1) % 360 <= span - 2
                for x, y in ((box[0], box[1]), (box[0], box[3]), (box[2], box[1]), (box[2], box[3]))
            )
            fits = abs(box[0]) < limit and abs(box[2]) < limit
            reach = [math.hypot(x, y) / PPU for x in (box[0], box[2]) for y in (box[1], (box[1] + box[3]) / 2, box[3])]
            crosses = any(min(reach) < HOLE + j + 0.03 and max(reach) > HOLE + j - 0.03 for j in range(1, len(RINGS)))
            blocked = clash(box, taken) or clash(marker, taken, 2)
            options.append((blocked or not fits, not inside, crosses, cost, mx, my, left, box, marker))
        *_, mx, my, left, box, marker = min(options, key=lambda o: o[0:4])
        taken += [box, marker]
        texts.append((left, my, row[NAME]))
        points.append((mx / PPU, my / PPU))
    marks[sector] = points

# Labels are drawn by pygal at (x + value_font_size, y + value_font_size) from an invisible point,
# so each text gets a point shifted back by that offset
label_points = [{"value": ((left - LABEL_PX) / PPU, (cy + LABEL_PX) / PPU), "label": text} for left, cy, text in texts]
chart_series.append((None, label_points, 0, "none", 0))
colors.append(INK)
for i, sector in enumerate(sectors):
    chart_series.append((sector, marks[sector], 0, "none", MARKER_R))
    colors.append(IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)])

title_str = "radar-innovation-timeline · python · pygal · anyplot.ai"
title_font_size = max(round(66 * 67 / len(title_str)) if len(title_str) > 67 else 66, 44)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(colors),
    title_font_size=title_font_size,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=48,
    value_font_size=LABEL_PX,
    value_label_font_size=LABEL_PX,
    value_colors=tuple(INK for _ in colors),
    stroke_width=2.5,
    opacity=1,
    opacity_hover=1,
)

chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title=title_str,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(sectors),
    legend_box_size=36,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    xrange=(-half_x, half_x),
    range=(y_lo, y_hi),
    print_labels=True,
    margin=40,
)

for title, points, width, dash, dots in chart_series:
    chart.add(
        title,
        points,
        stroke=width > 0,
        stroke_style={"width": width, "dasharray": dash},
        show_dots=dots is not None,
        dots_size=dots or 0,
    )

chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
