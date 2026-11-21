"""anyplot.ai
line-confidence: Line Plot with Confidence Interval
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants
BAND_OPACITY = 0.28  # semi-transparent band so grid lines stay visible through it

# Columns: set these to your table's column names
WEEK = "Time (weeks)"  # role: x
USERS = "Predicted users"  # role: y
LOWER = "Lower bound (95%)"  # role: y_lower
UPPER = "Upper bound (95%)"  # role: y_upper

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
rng = np.random.default_rng(42)
weeks = np.linspace(0, 12, 50)
trend = 1000 + 500 * (1 - np.exp(-0.3 * weeks)) + rng.normal(0, 20, 50)
trend = np.convolve(trend, np.ones(5) / 5, mode="same")
trend[:2] = trend[2]
trend[-2:] = trend[-3]
half_width = 30 + 15 * weeks  # uncertainty widens with the forecast horizon
df = pd.DataFrame({WEEK: weeks, USERS: trend, LOWER: trend - half_width, UPPER: trend + half_width})

# Plot: reads only df and the constants above
table = df.dropna(subset=[WEEK, USERS, LOWER, UPPER]).sort_values(WEEK)
x_vals = table[WEEK].astype(float).tolist()
pad = 0.04 * float(table[UPPER].max() - table[LOWER].min())

style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(IMPRINT_PALETTE[0], IMPRINT_PALETTE[0]),
    opacity=BAND_OPACITY,
    opacity_hover=BAND_OPACITY,
    title_font_size=60,
    label_font_size=52,
    major_label_font_size=44,
    legend_font_size=44,
    stroke_width=2,
)

chart = pygal.XY(
    style=style,
    width=3200,
    height=1800,
    title="line-confidence · python · pygal · anyplot.ai",
    x_title=WEEK,
    y_title=USERS,
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    css=[
        "file://style.css",
        "file://graph.css",
        "inline:.serie-0 .line{stroke-width:2px !important} .serie-1 .line{stroke-width:10px !important}",
    ],
    range=(float(table[LOWER].min() - pad), float(table[UPPER].max() + pad)),
)

# Band: closed polygon running along the upper bound and back along the lower bound
band = list(zip(x_vals, table[UPPER].astype(float).tolist(), strict=True))
band += list(zip(reversed(x_vals), reversed(table[LOWER].astype(float).tolist()), strict=True))
line = list(zip(x_vals, table[USERS].astype(float).tolist(), strict=True))

chart.add("95% confidence interval", band, fill=True, stroke=True, show_dots=False, stroke_style={"width": 1})
chart.add("Predicted mean", line, fill=False, stroke=True, show_dots=False, stroke_style={"width": 12})

# Output
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
