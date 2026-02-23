"""pyplots.ai
density-basic: Basic Density Plot
Library: pygal 3.1.0 | Python 3.14.3
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - test scores with clear bimodal structure (two student groups)
np.random.seed(42)
main_scores = np.random.normal(76, 8, 200)  # Main group around 76
secondary_scores = np.random.normal(52, 5, 70)  # Distinct lower-scoring group
scores = np.concatenate([main_scores, secondary_scores])

# KDE with Gaussian kernel and Scott's rule bandwidth
x_range = np.linspace(scores.min() - 12, scores.max() + 12, 400)
n = len(scores)
bandwidth = n ** (-1 / 5) * np.std(scores)

# Combined density
density = np.zeros_like(x_range)
for xi in scores:
    density += np.exp(-0.5 * ((x_range - xi) / bandwidth) ** 2)
density /= n * bandwidth * np.sqrt(2 * np.pi)

# Secondary component density (weighted by proportion) for visual storytelling
density_sec = np.zeros_like(x_range)
for xi in secondary_scores:
    density_sec += np.exp(-0.5 * ((x_range - xi) / bandwidth) ** 2)
density_sec /= n * bandwidth * np.sqrt(2 * np.pi)

# Refined style with warm accent for secondary group
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#e0e0e0",
    colors=("#306998", "#c47a3a", "#1a3d5c"),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=32,
    value_font_size=28,
    stroke_width=5,
    opacity=0.60,
    opacity_hover=0.85,
)

# Chart with refined axes, compact bottom legend, explicit margins
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="density-basic · pygal · pyplots.ai",
    x_title="Test Score (points)",
    y_title="Density",
    show_dots=False,
    fill=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    show_y_guides=True,
    show_x_guides=False,
    stroke_style={"width": 5, "linecap": "round"},
    truncate_label=-1,
    margin_top=50,
    margin_right=60,
    x_value_formatter=lambda x: f"{x:.0f}",
    y_value_formatter=lambda y: f"{y:.3f}",
    css=[
        "file://style.css",
        "inline:.plot .background {fill: white !important; stroke: none !important; stroke-width: 0 !important;}",
        "inline:.graph > .background {fill: white !important; stroke: none !important;}",
        "inline:.axis .guides .line {stroke: #e8e8e8 !important; stroke-width: 1px;}",
        "inline:.axis.x .line {stroke: #999999 !important; stroke-width: 1.5px;}",
        "inline:.axis.y .line {stroke: #999999 !important; stroke-width: 1.5px;}",
    ],
    js=[],
)

# Main density curve (combined) — prominent filled area
xy_combined = [(float(x), float(y)) for x, y in zip(x_range, density, strict=True)]
chart.add("Test score distribution", xy_combined)

# Secondary component — warm accent line highlighting bimodal structure
xy_sec = [(float(x), float(y)) for x, y in zip(x_range, density_sec, strict=True)]
chart.add("Lower-scoring group", xy_sec, stroke_style={"width": 3, "linecap": "round"}, fill=False)

# Rug plot — prominent individual observation marks
rug_height = max(density) * 0.08
rug_sample = scores[::2]  # Every other point for good coverage
rug_data = []
for xi in sorted(rug_sample):
    rug_data.append((float(xi), 0.0))
    rug_data.append((float(xi), float(rug_height)))
    rug_data.append((float(xi), 0.0))

chart.add("Individual scores", rug_data, stroke_style={"width": 3.5, "linecap": "round"}, show_dots=False, fill=False)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
