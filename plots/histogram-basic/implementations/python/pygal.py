"""anyplot.ai
histogram-basic: Basic Histogram
Library: pygal 3.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-28
"""

import sys


# This file is named pygal.py which shadows the installed pygal package.
# Move the script directory to the end so site-packages takes precedence.
_script_dir = sys.path.pop(0) if sys.path else None

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


if _script_dir is not None:
    sys.path.append(_script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 20  # enough bins to show the skew and the tails of 500 observations

# Columns: set these to your table's column names
SCORE = "Exam score (points)"  # role: values
COUNT = "Number of students"  # axis title for the frequency, derived from the values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame({SCORE: rng.beta(a=5, b=2, size=500) * 60 + 35})

# Plot: reads only df and the constants above
counts, bin_edges = np.histogram(df[SCORE].dropna(), bins=N_BINS)
hist_data = [(int(count), float(lo), float(hi)) for count, lo, hi in zip(counts, bin_edges[:-1], bin_edges[1:])]

# Style: thin bin edges in the page color keep neighboring bars distinguishable without gaps
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)
custom_style.opacity = "1"
custom_style.opacity_hover = "0.85"

chart = pygal.Histogram(
    css=["file://style.css", "file://graph.css", f"inline:.rect {{ stroke: {PAGE_BG}; stroke-width: 3; }}"],
    width=3200,
    height=1800,
    style=custom_style,
    title="histogram-basic · python · pygal · anyplot.ai",
    x_title=SCORE,
    y_title=COUNT,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    tooltip_fancy_mode=True,
    print_values=False,
    margin_bottom=100,
    margin_left=80,
    margin_right=60,
    margin_top=80,
)
chart.add(COUNT, hist_data)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
