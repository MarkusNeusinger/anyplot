""" pyplots.ai
scatter-categorical: Categorical Scatter Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Iris-like flower measurements by species
np.random.seed(42)

# Three species with different characteristic measurements
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

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#2ca02c"),  # Python Blue, Python Yellow, Green
    title_font_size=56,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=36,
    value_font_size=28,
    opacity=0.7,
    opacity_hover=0.9,
    stroke_width=0,
    dots_size=12,
)

# Create XY scatter chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-categorical · pygal · pyplots.ai",
    x_title="Petal Length (cm)",
    y_title="Petal Width (cm)",
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=False,
    legend_box_size=24,
    truncate_legend=-1,
    dots_size=12,
)

# Add data for each species as (x, y) tuples
chart.add("Setosa", list(zip(setosa_x, setosa_y, strict=True)))
chart.add("Versicolor", list(zip(versicolor_x, versicolor_y, strict=True)))
chart.add("Virginica", list(zip(virginica_x, virginica_y, strict=True)))

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
