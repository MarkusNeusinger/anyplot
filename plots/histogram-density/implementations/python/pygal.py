"""anyplot.ai
histogram-density: Density Histogram
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-11
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

# Columns: set these to your table's column names
SCORE = "Test score (points)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
group_a = np.random.normal(loc=65, scale=10, size=150)
group_b = np.random.normal(loc=82, scale=8, size=100)
df = pd.DataFrame({SCORE: np.clip(np.concatenate([group_a, group_b]), 0, 100)})

# Plot: reads only df and the constants above
values = df[SCORE].dropna().to_numpy()
n_bins = max(5, round(1.6 * len(values) ** 0.5))
density, edges = np.histogram(values, bins=n_bins, density=True)

style = Style(
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
    stroke_width=2.5,
)

chart = pygal.Histogram(
    width=3200,
    height=1800,
    style=style,
    title="histogram-density · python · pygal · anyplot.ai",
    x_title=SCORE,
    y_title="Density (probability per point)",
    show_legend=False,
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=0,
    margin=60,
    print_values=False,
)

# Contiguous bars: (density, bin start, bin end) so bar areas sum to 1
bars = [(float(d), float(lo), float(hi)) for d, lo, hi in zip(density, edges[:-1], edges[1:], strict=True)]
chart.add("Density", bars)

# Save outputs with theme-suffixed filenames
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
