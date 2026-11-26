"""anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: pygal 3.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-20
"""

import sys


sys.path.pop(0)  # Prevent self-import: pygal.py shadows the installed pygal package

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
TAIL_SIGMAS = 2  # tails start this many standard deviations from the mean
N_BINS = 30
N_CURVE = 300  # thin adjacent bins that approximate a smooth curve in the Histogram API

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RETURNS = "Daily return (%)"  # role: returns

# Data: replace this block with your own table, for example df = pd.read_csv("returns.csv")
# 252 daily returns of an equity ETF: fat-tailed Student-t (4 degrees of freedom), about 1.3 % volatility
rng = np.random.default_rng(7)
t_draws = rng.standard_t(df=4, size=252) / np.sqrt(2.0)  # unit variance
df = pd.DataFrame({DATE: pd.bdate_range("2024-01-02", periods=252), RETURNS: 0.06 + 1.3 * t_draws})

# Plot: reads only df and the constants above
returns = df[RETURNS].dropna()
mean_return = returns.mean()
std_return = returns.std()
skewness = returns.skew()
kurtosis = returns.kurt()  # excess kurtosis

counts, bin_edges = np.histogram(returns, bins=N_BINS, density=True)
lower_tail = mean_return - TAIL_SIGMAS * std_return
upper_tail = mean_return + TAIL_SIGMAS * std_return

# Histogram bars: pygal.Histogram native format (height, xmin, xmax)
normal_bars = []
tail_bars = []
for height, left, right in zip(counts, bin_edges[:-1], bin_edges[1:], strict=True):
    bar = (float(height), float(left), float(right))
    center = (left + right) / 2
    (tail_bars if center < lower_tail or center > upper_tail else normal_bars).append(bar)

# Fitted normal curve: dense adjacent thin bins
x_curve = np.linspace(bin_edges[0], bin_edges[-1], N_CURVE)
normal_pdf = np.exp(-0.5 * ((x_curve - mean_return) / std_return) ** 2) / (std_return * np.sqrt(2 * np.pi))
curve_data = [
    (float(h), float(a), float(b)) for h, a, b in zip(normal_pdf[:-1], x_curve[:-1], x_curve[1:], strict=True)
]

# Style
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
    stroke_width=2.5,
    opacity=0.85,
    opacity_hover=1.0,
)

stats_text = (
    f"Mean: {mean_return:.3f}% | Std: {std_return:.3f}% | Skew: {skewness:.2f} | Excess kurtosis: {kurtosis:.2f}"
)

# The curve is the third series: translucent fill keeps the bars underneath readable
chart = pygal.Histogram(
    width=3200,
    height=1800,
    explicit_size=True,
    style=custom_style,
    title=f"histogram-returns-distribution · python · pygal · anyplot.ai\n{stats_text}",
    x_title=RETURNS,
    y_title="Probability density",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=32,
    show_y_guides=True,
    show_x_guides=False,
    margin_bottom=200,
    margin_left=120,
    margin_right=80,
    print_values=False,
    css=[
        "file://style.css",
        "file://graph.css",
        "inline:.color-2 .rect {fill-opacity: 0.3 !important; stroke-opacity: 0.3 !important}",
    ],
)

chart.add(f"Returns (within {TAIL_SIGMAS}σ)", normal_bars)
chart.add(f"Tails (beyond ±{TAIL_SIGMAS}σ)", tail_bars)
chart.add("Fitted normal distribution", curve_data)

# Save
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
chart.render_to_png(f"plot-{THEME}.png")
