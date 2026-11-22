""" anyplot.ai
histogram-stepwise: Step Histogram
Library: pygal 3.1.3 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
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

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 25  # number of contiguous bins shared by every distribution

# Columns: set these to your table's column names
VALUES = ["Value (cm)"]  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("heights.csv")
np.random.seed(42)
df = pd.DataFrame({VALUES[0]: np.concatenate([np.random.normal(50, 10, 200), np.random.normal(80, 8, 150)])})

# Plot
counts, bin_edges = np.histogram(df[VALUES[0]].dropna(), bins=N_BINS)

# Step outline: one horizontal segment per bin at its count, joined by vertical
# segments at the bin edges, starting and ending on the baseline
step_data = [(bin_edges[0], 0)]
for left, right, count in zip(bin_edges[:-1], bin_edges[1:], counts, strict=True):
    step_data.append((left, int(count)))
    step_data.append((right, int(count)))
step_data.append((bin_edges[-1], 0))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=5,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="histogram-stepwise · python · pygal · anyplot.ai",
    x_title=VALUES[0],
    y_title="Frequency (count)",
    show_dots=False,
    fill=False,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=0,
    min_scale=1,
    range=(0, int(counts.max() * 1.08) + 1),
)

chart.add(VALUES[0], step_data)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
