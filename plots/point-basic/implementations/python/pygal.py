"""anyplot.ai
point-basic: Point Estimate Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NULL_VALUE = 0  # reference line: no calibration error
CAP_HALF_HEIGHT = 0.15  # half height of the interval caps, in rows

# Columns: set these to your table's column names
SENSOR = "Sensor"  # role: category
ESTIMATE = "Calibration error (μV)"  # role: estimate
LOWER = "Lower 95% bound (μV)"  # role: lower_bound
UPPER = "Upper 95% bound (μV)"  # role: upper_bound

# Data: replace this block with your own table, for example df = pd.read_csv("sensors.csv")
df = pd.DataFrame(
    {
        SENSOR: ["Sensor A", "Sensor B", "Sensor C", "Sensor D", "Sensor E"],
        ESTIMATE: [0.3, 0.8, -0.2, 1.1, 0.5],
        LOWER: [-0.4, 0.1, -0.9, 0.3, -0.1],
        UPPER: [1.0, 1.5, 0.5, 1.9, 1.1],
    }
)

# Plot: reads only df and the constants above
n = len(df)
rows = list(range(n, 0, -1))  # first category at the top
pad = 0.15 * (df[UPPER].max() - df[LOWER].min())
x_min = min(df[LOWER].min(), NULL_VALUE) - pad
x_max = max(df[UPPER].max(), NULL_VALUE) + pad

# Series order: reference, one interval per category, estimates -> colors follow this order
series_colors = (IMPRINT_PALETTE[0],) + (IMPRINT_PALETTE[2],) * n + (IMPRINT_PALETTE[1],)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=series_colors,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
    guide_stroke_color=GRID,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="point-basic · python · pygal · anyplot.ai",
    x_title=ESTIMATE,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_y_guides=False,
    show_x_guides=True,
    dots_size=18,
    stroke=False,
    margin_left=80,
    margin_right=80,
    margin_top=100,
    margin_bottom=120,
    xrange=(x_min, x_max),
    range=(0, n + 1),
)

chart.add(
    "Reference (zero error)", [(NULL_VALUE, 0.3), (NULL_VALUE, n + 0.7)], stroke=True, show_dots=False, stroke_width=3
)

# One series per interval: line with a cap at each end
for i, (low, high, y) in enumerate(zip(df[LOWER], df[UPPER], rows, strict=True)):
    segments = [
        (low, y - CAP_HALF_HEIGHT),
        (low, y + CAP_HALF_HEIGHT),
        (low, y),
        (high, y),
        (high, y - CAP_HALF_HEIGHT),
        (high, y + CAP_HALF_HEIGHT),
    ]
    chart.add("95% CI" if i == 0 else None, segments, stroke=True, show_dots=False, stroke_width=5)

# Point estimates on top of the interval lines
chart.add("Point Estimate", list(zip(df[ESTIMATE], rows, strict=True)), dots_size=20, stroke=False)

# Category names at their rows
chart.y_labels = [{"value": y, "label": name} for y, name in zip(rows, df[SENSOR], strict=True)]

# Save as PNG and HTML with theme suffix
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
