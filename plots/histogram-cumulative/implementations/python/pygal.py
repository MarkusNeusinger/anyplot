"""anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
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
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BIN_COUNT = 20  # number of equal-width bins the values are cut into

# Columns: set these to your table's column names
RATING = "Customer Satisfaction Rating"  # role: numeric

# Data: replace this block with your own table, for example df = pd.read_csv("ratings.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame({RATING: np.clip(rng.normal(loc=3.7, scale=0.8, size=1000), 1, 5)})

# Plot: reads only df and the constants above
counts, bin_edges = np.histogram(df[RATING].dropna(), bins=BIN_COUNT)
cumulative = (np.cumsum(counts) / counts.sum()).tolist()
bin_labels = [f"{lo:.1f}-{hi:.1f}" for lo, hi in zip(bin_edges[:-1], bin_edges[1:], strict=True)]

# Style: pygal font sizes are source pixels on the 3200x1800 canvas
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
)

chart = pygal.Bar(
    width=3200,
    height=1800,
    style=custom_style,
    title="histogram-cumulative · python · pygal · anyplot.ai",
    x_title=RATING,
    y_title="Cumulative Proportion",
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=45,
    range=(0, 1.05),
    margin=40,
    spacing=20,
    print_values=False,
)
chart.x_labels = bin_labels
chart.add("Cumulative", cumulative)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
