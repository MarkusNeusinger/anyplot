"""anyplot.ai
line-basic: Basic Line Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-04-29
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

# Columns: set these to your table's column names
DAY = "Date"  # role: x
VISITORS = "Daily visitors (thousands)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
rng = np.random.default_rng(7)
dates = pd.date_range("2025-03-03", periods=70, freq="D")
weekly = np.where(dates.day_of_week >= 5, -3.5, 0.0)
growth = np.linspace(0, 9, len(dates))
df = pd.DataFrame({DAY: dates, VISITORS: (24 + growth + weekly + rng.normal(0, 1.6, len(dates))).round(1)})

# Plot
labels = df[DAY].dt.strftime("%b %d").tolist()
major_labels = labels[::7]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=36,
    stroke_width=4,
)

chart = pygal.Line(
    width=3200,
    height=1800,
    title="line-basic · python · pygal · anyplot.ai",
    x_title=DAY,
    y_title=VISITORS,
    style=custom_style,
    show_legend=False,
    show_dots=True,
    dots_size=5,
    stroke_style={"width": 4},
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=0,
    show_minor_x_labels=False,
    truncate_label=-1,
    x_labels_major=major_labels,
    range=(float(np.floor(df[VISITORS].min() - 2)), float(np.ceil(df[VISITORS].max() + 2))),
)

chart.x_labels = labels
chart.add(VISITORS, df[VISITORS].tolist())

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
