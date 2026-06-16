""" anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: pygal 3.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-17
"""

import os
import sys

import numpy as np


# Remove current directory from path to avoid shadowing pygal module
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != current_dir]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ("#009E73", "#C475FD", "#4467A3")

# Data - Three groups of measurements (plant heights by soil type)
np.random.seed(42)

# Generate three distributions with different characteristics
group_a = np.random.normal(loc=45, scale=8, size=200)  # Sandy soil - lower mean
group_b = np.random.normal(loc=55, scale=10, size=200)  # Loamy soil - medium mean, wider spread
group_c = np.random.normal(loc=60, scale=6, size=200)  # Clay soil - higher mean, narrow spread

# Define bins for frequency calculation
bins = np.linspace(20, 85, 15)
bin_midpoints = (bins[:-1] + bins[1:]) / 2

# Calculate frequencies for each group
freq_a, _ = np.histogram(group_a, bins=bins)
freq_b, _ = np.histogram(group_b, bins=bins)
freq_c, _ = np.histogram(group_c, bins=bins)

# Extend lines to zero at both ends to close the polygon shape
midpoints_extended = [float(bins[0])] + [float(m) for m in bin_midpoints] + [float(bins[-1])]
freq_a_extended = [0] + [int(f) for f in freq_a] + [0]
freq_b_extended = [0] + [int(f) for f in freq_b] + [0]
freq_c_extended = [0] + [int(f) for f in freq_c] + [0]

# Custom style for large canvas (4800x2700) with theme-adaptive colors
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
    opacity=0.8,
    opacity_hover=1.0,
)

# Create XY chart for frequency polygon with fill
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="frequency-polygon-basic · pygal · anyplot.ai",
    x_title="Plant Height (cm)",
    y_title="Frequency",
    show_x_guides=True,
    show_y_guides=True,
    dots_size=10,
    stroke_style={"width": 4},
    legend_at_bottom=True,
    show_dots=True,
    fill=True,
    x_label_rotation=0,
    range=(0, int(max(max(freq_a), max(freq_b), max(freq_c))) + 5),
    xrange=(15, 90),
)

# Add data series - each point is (x, y) tuple
chart.add("Sandy Soil", list(zip(midpoints_extended, freq_a_extended, strict=True)))
chart.add("Loamy Soil", list(zip(midpoints_extended, freq_b_extended, strict=True)))
chart.add("Clay Soil", list(zip(midpoints_extended, freq_c_extended, strict=True)))

# Save as PNG and HTML with theme-suffixed filenames
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
