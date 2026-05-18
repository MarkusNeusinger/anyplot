""" anyplot.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: pygal 3.1.0 | Python 3.13.13
Quality: 40/100 | Created: 2026-05-18
"""

import os
import sys


# Remove the script's directory from sys.path to avoid shadowing installed packages
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)

import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402
from sklearn.datasets import load_iris  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data
iris = load_iris()
df = pd.DataFrame(iris.data, columns=["sepal_length", "sepal_width", "petal_length", "petal_width"])
df["species"] = iris.target_names[iris.target]

# Create scatter plot matrix visualization
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
)

chart = pygal.XY(
    width=4800,
    height=2700,
    title="scatter-matrix-interactive · python · pygal · anyplot.ai",
    x_title="Sepal Length (cm)",
    y_title="Petal Length (cm)",
    show_legend=True,
    show_dots=True,
    stroke=False,
    style=custom_style,
    tooltip_border_radius=4,
    range=(4, 8),
)

# Add data series for each species
species_names = iris.target_names
for species_name in species_names:
    species_data = df[df["species"] == species_name]
    points = [
        {"value": (float(x), float(y)), "label": f"{species_name}: ({x:.1f}, {y:.1f})"}
        for x, y in zip(species_data["sepal_length"], species_data["petal_length"], strict=False)
    ]
    chart.add(species_name.capitalize(), points)

# Render files
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
