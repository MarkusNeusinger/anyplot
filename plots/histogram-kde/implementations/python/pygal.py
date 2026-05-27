""" anyplot.ai
histogram-kde: Histogram with KDE Overlay
Library: pygal 3.1.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-06
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = (
    "#009E73",  # brand green
    "#C475FD",  # vermillion
    "#4467A3",  # blue
    "#BD8233",  # reddish purple
    "#AE3030",  # orange
    "#2ABCCD",  # sky blue
    "#954477",  # yellow
)

# Data - Simulated stock returns showing realistic distribution with tails
np.random.seed(42)
returns = np.concatenate(
    [
        np.random.normal(0.05, 1.5, 400),  # Main distribution of daily returns
        np.random.normal(-3, 0.5, 30),  # Left tail (market drops)
        np.random.normal(4, 0.8, 20),  # Right tail (market rallies)
    ]
)

# Compute histogram bins with density normalization
n_bins = 25
counts, bin_edges = np.histogram(returns, bins=n_bins, density=True)

# Compute KDE using Gaussian kernel (Scott's rule for bandwidth)
x_range = np.linspace(returns.min() - 1, returns.max() + 1, 200)
n = len(returns)
bandwidth = n ** (-1 / 5) * np.std(returns)
kde = np.zeros_like(x_range)
for xi in returns:
    kde += np.exp(-0.5 * ((x_range - xi) / bandwidth) ** 2)
kde /= n * bandwidth * np.sqrt(2 * np.pi)

# Create histogram bar data as step-like XY path
hist_xy = [(float(bin_edges[0]), 0.0)]
for i, count in enumerate(counts):
    left = float(bin_edges[i])
    right = float(bin_edges[i + 1])
    height = float(count)
    hist_xy.append((left, height))
    hist_xy.append((right, height))
hist_xy.append((float(bin_edges[-1]), 0.0))

# Custom style for 4800x2700 px canvas with theme-adaptive colors
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    opacity=0.55,
    opacity_hover=0.75,
)

# Create XY chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="histogram-kde · pygal · anyplot.ai",
    x_title="Daily Return (%)",
    y_title="Probability Density",
    show_dots=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    show_y_guides=False,
    show_x_guides=False,
)

# Add histogram as filled step area (first series uses #009E73)
chart.add("Histogram", hist_xy, fill=True, stroke_style={"width": 2})

# Add KDE curve with prominent stroke for visibility (second series uses #C475FD)
kde_data = [(float(x), float(y)) for x, y in zip(x_range, kde, strict=True)]
chart.add("KDE Curve", kde_data, fill=False, stroke_style={"width": 4})

# Save outputs
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
