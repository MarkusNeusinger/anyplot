"""anyplot.ai
box-basic: Basic Box Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os
import sys


# Remove this script's directory from sys.path so 'import pygal' finds the
# installed package rather than this file itself (same-name collision).
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _here]

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
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
ZONE = "City zone"  # role: category
PM25 = "PM2.5 (µg/m³)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("air_quality.csv")
rng = np.random.default_rng(42)
zones = {
    "Industrial": (46, 0.30),
    "Downtown": (34, 0.28),
    "Residential": (26, 0.25),
    "Suburban": (19, 0.24),
    "Park": (12, 0.22),
}
readings = {zone: rng.lognormal(np.log(median), spread, 120) for zone, (median, spread) in zones.items()}
# A few episodes: smog spikes next to the factories, a bonfire night in the park
readings["Industrial"] = np.append(readings["Industrial"], [118, 126, 133])
readings["Downtown"] = np.append(readings["Downtown"], [96, 104])
readings["Park"] = np.append(readings["Park"], [41, 47])
df = pd.DataFrame(
    {
        ZONE: np.repeat(list(readings), [len(v) for v in readings.values()]),
        PM25: np.concatenate(list(readings.values())).round(1),
    }
)

# Plot: reads only df and the constants above
table = {zone: group[PM25].tolist() for zone, group in df.groupby(ZONE, sort=False)}
pad = (df[PM25].max() - df[PM25].min()) * 0.05
y_min = max(0.0, float(np.floor((df[PM25].min() - pad) / 10) * 10))
y_max = float(np.ceil((df[PM25].max() + pad) / 10) * 10)

title = "box-basic · python · pygal · anyplot.ai"
title_font_size = round(66 * 67 / len(title)) if len(title) > 67 else 66

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_font_size,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    opacity=1.0,
    opacity_hover=1.0,
)

chart = pygal.Box(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=ZONE,
    y_title=PM25,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(table),
    legend_box_size=36,
    truncate_legend=-1,
    truncate_label=-1,
    show_y_guides=True,
    show_x_guides=False,
    margin=80,
    spacing=40,
    box_mode="tukey",
    range=(y_min, y_max),
)

for zone, values in table.items():
    chart.add(zone, values)

svg_string = chart.render().decode("utf-8")

# Increase box fill opacity (pygal hardcodes subtle-fill at 0.2) and add an ink border to each box
svg_string = svg_string.replace(
    ".subtle-fill{fill-opacity:.2}", f".subtle-fill{{fill-opacity:.7;stroke:{INK_SOFT};stroke-width:4}}"
)

# Draw whiskers, caps and the median in ink so they stand out from the box fill (an inline style beats the
# chart's id-scoped .reactive rule), and remove the chart border
svg_string = re.sub(
    r'<path stroke-width="[23]" (d="[^"]*" class="reactive tooltip-trigger")',
    rf'<path style="stroke:{INK};stroke-width:6;stroke-opacity:1" \1',
    svg_string,
)
svg_string = svg_string.replace("</style>", ".background{stroke:none}</style>", 1)

# Enlarge outlier dots (pygal hardcodes r=3 for box outliers)
svg_string = re.sub(r'(<circle[^>]*) r="3" (class="subtle-fill)', r'\1 r="20" \2', svg_string)

# Save
with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg_string)

cairosvg.svg2png(bytestring=svg_string.encode("utf-8"), write_to=f"plot-{THEME}.png")
