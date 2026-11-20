"""anyplot.ai
polar-scatter: Polar Scatter Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-11-20
"""

import os
import re

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
GRID = "#C9C7BC" if THEME == "light" else "#4A4A44"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SPOKE_STEP = 45  # degrees between angular gridlines
COMPASS = {0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW"}

# Columns: set these to your table's column names
DIRECTION = "Wind direction (degrees)"  # role: theta
SPEED = "Wind speed (m/s)"  # role: radius
PERIOD = "Time of day"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
rng = np.random.default_rng(42)
periods = {"Morning": (315, 30, 6, 15, 35), "Afternoon": (45, 35, 8, 18, 40), "Evening": (180, 25, 5, 12, 35)}
parts = []
for name, (mean_dir, spread, lo, hi, n) in periods.items():
    parts.append(
        pd.DataFrame({DIRECTION: rng.normal(mean_dir, spread, n) % 360, SPEED: rng.uniform(lo, hi, n), PERIOD: name})
    )
df = pd.concat(parts, ignore_index=True)

# Plot: compass convention, 0° at the top and degrees running clockwise
raw_step = df[SPEED].max() / 4
magnitude = 10 ** np.floor(np.log10(raw_step))
RING_STEP = magnitude * min(m for m in (1, 2, 5, 10) if m * magnitude >= raw_step)  # about four rings, round values
rim = (np.floor(df[SPEED].max() / RING_STEP) + 1) * RING_STEP
groups = list(dict.fromkeys(df[PERIOD]))


def to_xy(theta_deg, radius):
    theta = np.radians(theta_deg)
    return float(radius * np.sin(theta)), float(radius * np.cos(theta))


# One grid series: rings and spokes joined by None breaks; ring and compass labels ride on single points
sweep = np.linspace(0, 360, 181)
grid = []
for ring in np.arange(RING_STEP, rim + 1e-9, RING_STEP):
    grid += [to_xy(t, ring) for t in sweep] + [None]
for spoke in range(0, 360, SPOKE_STEP):
    grid += [to_xy(spoke, 0), to_xy(spoke, rim), None]
labels = []
for spoke in range(0, 360, SPOKE_STEP):
    x_l, y_l = to_xy(spoke, rim * 1.12)
    labels.append({"value": (x_l, y_l), "label": f"{COMPASS.get(spoke, '')} {spoke}°"})
for ring in np.arange(RING_STEP, rim + 1e-9, RING_STEP):
    x_l, y_l = to_xy(247.5, ring)
    labels.append({"value": (x_l, y_l), "label": f"{ring:g}"})

MARGIN_X = 135
limit = rim * 1.22
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE[: len(groups)]) + (GRID, INK_MUTED),
    opacity=0.65,
    opacity_hover=0.95,
    title_font_size=66,
    label_font_size=34,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=40,
    value_colors=(INK_MUTED,) * (len(groups) + 2),
    stroke_width=3,
)

chart = pygal.XY(
    style=custom_style,
    width=2400,
    height=2400,
    title="polar-scatter · python · pygal · anyplot.ai",
    x_title=f"Radius: {SPEED} · angle: degrees clockwise from north",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(groups) + 2,
    dots_size=14,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    range=(-limit, limit),
    xrange=(-limit, limit),
    stroke=False,
    margin_left=MARGIN_X,
    margin_right=MARGIN_X,
    print_labels=False,
    truncate_legend=-1,
)

for group in groups:
    sub = df[df[PERIOD] == group]
    chart.add(str(group), [to_xy(t, r) for t, r in zip(sub[DIRECTION], sub[SPEED], strict=True)])
chart.add("Gridlines", grid, stroke=True, show_dots=False, print_labels=False)
chart.add("Scale labels", [item["value"] for item in labels], stroke=False, dots_size=1)

# pygal draws XY value text only as tooltips, so the labels are written into the SVG at the dots' positions
svg = chart.render().decode()
series_groups = [
    part.split('<g class="series serie-')[0] for part in svg.split('class="series serie-%d ' % (len(groups) + 1))[1:]
]
centers = max((re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)"', part) for part in series_groups), key=len)
shift_x, shift_y = map(float, re.search(r'translate\(([\d.]+), ([\d.]+)\)" class="plot"', svg).groups())
texts = "".join(
    f'<text x="{float(cx) + shift_x}" y="{float(cy) + shift_y + 14}" text-anchor="middle" font-size="40" '
    f'font-family="Consolas,Liberation Mono,Menlo,monospace" fill="{INK_MUTED}">{item["label"]}</text>'
    for (cx, cy), item in zip(centers, labels, strict=True)
)
svg = svg.replace("</svg>", texts + "</svg>")

# Save
cairosvg.svg2png(bytestring=svg.encode(), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg)
