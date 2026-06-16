""" anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-12
"""

import os
import sys


# Prevent importing local pygal.py file
sys.path = [p for p in sys.path if not p.endswith("/implementations/python")]

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series = #009E73)
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - Iris-like flower measurements by species
np.random.seed(42)

species = ["Setosa", "Versicolor", "Virginica"]
n_per_species = 40

# Setosa: small petals (low x, low y)
setosa_x = np.random.normal(1.5, 0.25, n_per_species)
setosa_y = np.random.normal(0.3, 0.1, n_per_species)

# Versicolor: medium petals (medium x, medium y)
versicolor_x = np.random.normal(4.2, 0.6, n_per_species)
versicolor_y = np.random.normal(1.3, 0.25, n_per_species)

# Virginica: large petals (high x, high y)
virginica_x = np.random.normal(5.5, 0.6, n_per_species)
virginica_y = np.random.normal(2.0, 0.3, n_per_species)

# Custom style for large canvas with theme support
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    opacity=0.75,
    opacity_hover=0.9,
    stroke_width=2,
    dots_size=8,
)

# Create XY scatter chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-categorical · pygal · anyplot.ai",
    x_title="Petal Length (cm)",
    y_title="Petal Width (cm)",
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_box_size=16,
    truncate_legend=-1,
)

# Add data for each species as (x, y) tuples
chart.add("Setosa", list(zip(setosa_x, setosa_y, strict=True)))
chart.add("Versicolor", list(zip(versicolor_x, versicolor_y, strict=True)))
chart.add("Virginica", list(zip(virginica_x, virginica_y, strict=True)))

# Save as PNG and HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
