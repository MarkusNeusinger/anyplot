""" pyplots.ai
density-basic: Basic Density Plot
Library: pygal 3.1.0 | Python 3.14.3
Quality: 85/100 | Updated: 2026-02-23
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - simulated test scores showing slightly left-skewed distribution
np.random.seed(42)
scores = np.concatenate(
    [
        np.random.normal(75, 8, 200),  # Main cluster around 75
        np.random.normal(58, 5, 50),  # Smaller cluster showing left skew
    ]
)

# Compute KDE using Gaussian kernel with Scott's rule bandwidth
x_range = np.linspace(scores.min() - 10, scores.max() + 10, 300)
n = len(scores)
bandwidth = n ** (-1 / 5) * np.std(scores)
density = np.zeros_like(x_range)
for xi in scores:
    density += np.exp(-0.5 * ((x_range - xi) / bandwidth) ** 2)
density /= n * bandwidth * np.sqrt(2 * np.pi)

# Custom style — clean white, refined typography for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#e0e0e0",
    colors=("#306998", "#1a4971"),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=32,
    stroke_width=5,
    opacity=0.70,
    opacity_hover=0.85,
)

# Create XY chart for continuous density curve
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="density-basic · pygal · pyplots.ai",
    x_title="Test Score (points)",
    y_title="Density",
    show_dots=False,
    fill=True,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    stroke_style={"width": 5, "linecap": "round"},
    truncate_label=-1,
    css=[
        "file://style.css",
        "inline:.plot .background {fill: white; stroke: none !important;}",
        "inline:.axis .guides .line {stroke: #e8e8e8 !important; stroke-width: 1px;}",
        "inline:.axis .line {stroke: #cccccc !important; stroke-width: 1.5px;}",
    ],
    js=[],
)

# Add density curve as XY points
xy_data = [(float(x), float(y)) for x, y in zip(x_range, density, strict=True)]
chart.add("Density", xy_data)

# Add rug plot as individual vertical marks along x-axis
rug_height = max(density) * 0.06
rug_sample = scores[::3]  # Sample every 3rd point for good coverage
rug_data = []
for xi in sorted(rug_sample):
    rug_data.append((float(xi), 0.0))
    rug_data.append((float(xi), float(rug_height)))
    rug_data.append((float(xi), 0.0))

chart.add("Observations", rug_data, stroke_style={"width": 2.5, "linecap": "round"}, show_dots=False, fill=False)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
