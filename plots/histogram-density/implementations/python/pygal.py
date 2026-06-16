""" anyplot.ai
histogram-density: Density Histogram
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-11
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme configuration
THEME = os.getenv("ANYPLOT_THEME", "light")

# Color palette - Okabe-Ito + theme-adaptive chrome
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Generate sample data - test scores with realistic distribution
np.random.seed(42)
scores_group1 = np.random.normal(loc=65, scale=10, size=150)
scores_group2 = np.random.normal(loc=82, scale=8, size=100)
scores = np.concatenate([scores_group1, scores_group2])
scores = np.clip(scores, 0, 100)

# Calculate density histogram
n_bins = 25
counts, bin_edges = np.histogram(scores, bins=n_bins, density=True)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Create custom style matching default-style-guide.md
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
    stroke_width=3,
)

# Create histogram chart
chart = pygal.Bar(
    width=4800,
    height=2700,
    style=custom_style,
    title="histogram-density · pygal · anyplot.ai",
    x_title="Test Score",
    y_title="Density (Probability per Unit)",
    show_legend=False,
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=0,
    margin=120,
    spacing=1,
    print_values=False,
)

# Format x-axis labels (show every 5th bin for clarity)
chart.x_labels = [f"{int(bc)}" if i % 5 == 0 else "" for i, bc in enumerate(bin_centers)]

# Add density histogram data
chart.add("", [float(c) for c in counts])

# Save outputs with theme-suffixed filenames
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
