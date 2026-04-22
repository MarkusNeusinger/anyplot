""" pyplots.ai
density-basic: Basic Density Plot
Library: pygal 3.1.0 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-23
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
x_range = np.linspace(scores.min() - 8, scores.max() + 8, 400)
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
    legend_font_size=36,
    value_font_size=28,
    stroke_width=5,
    opacity=0.60,
    opacity_hover=0.85,
    font_family="'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
)

# Chart with refined axes — spines removed for clean floating-axis look
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
    legend_box_size=28,
    show_y_guides=True,
    show_x_guides=False,
    stroke_style={"width": 5, "linecap": "round"},
    truncate_label=-1,
    margin_top=40,
    margin_right=40,
    margin_bottom=30,
    margin_left=20,
    x_value_formatter=lambda x: f"{x:.0f}",
    y_value_formatter=lambda y: f"{y:.3f}",
    css=[
        "file://style.css",
        "inline:.plot .background {fill: white !important; stroke: none !important; stroke-width: 0 !important;}",
        "inline:.graph > .background {fill: white !important; stroke: none !important;}",
        "inline:.axis .guides .line {stroke: #e0e0e0 !important; stroke-width: 0.8px;}",
        "inline:.axis.x > path.line {stroke: none !important; stroke-width: 0 !important;}",
        "inline:.axis.y > path.line {stroke: none !important; stroke-width: 0 !important;}",
        "inline:.axis .guides text {fill: #666666 !important;}",
        "inline:text.title {font-weight: 600 !important; fill: #222222 !important;}",
        "inline:.axis text {font-weight: 400 !important;}",
        "inline:.legends text {font-weight: 400 !important; fill: #444444 !important;}",
    ],
    js=[],
)

# Main density curve (combined) — prominent filled area
xy_combined = [(float(x), float(y)) for x, y in zip(x_range, density, strict=True)]
chart.add("Test score distribution", xy_combined)

# Secondary component — warm accent highlighting bimodal structure
xy_sec = [(float(x), float(y)) for x, y in zip(x_range, density_sec, strict=True)]
chart.add("Lower-scoring group", xy_sec, stroke_style={"width": 3.5, "linecap": "round"}, fill=True)

# Rug plot — individual observation marks with increased prominence
rug_height = max(density) * 0.10
rug_data = []
for xi in sorted(scores):
    rug_data.append((float(xi), 0.0))
    rug_data.append((float(xi), float(rug_height)))
    rug_data.append((float(xi), 0.0))

chart.add("Individual scores", rug_data, stroke_style={"width": 4.5, "linecap": "round"}, show_dots=False, fill=False)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
