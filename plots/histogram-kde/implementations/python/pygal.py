""" pyplots.ai
histogram-kde: Histogram with KDE Overlay
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Simulated stock returns showing realistic distribution with tails
np.random.seed(42)
returns = np.concatenate(
    [
        np.random.normal(0.05, 1.5, 400),  # Main distribution of daily returns
        np.random.normal(-3, 0.5, 30),  # Left tail (market drops)
        np.random.normal(4, 0.8, 20),  # Right tail (market rallies)
    ]
)

# Compute histogram bins
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

# Custom style for 4800x2700 px canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#306998", "#D62839"),  # Blue for histogram, vivid red for KDE
    title_font_size=60,
    label_font_size=42,
    major_label_font_size=38,
    legend_font_size=42,
    value_font_size=32,
    opacity=0.55,
    opacity_hover=0.75,
)

# Create XY chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="histogram-kde \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Daily Return (%)",
    y_title="Probability Density",
    show_dots=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    show_y_guides=True,
    show_x_guides=True,
)

# Add histogram as filled step area
chart.add("Histogram", hist_xy, fill=True, stroke_style={"width": 2})

# Add KDE curve with prominent stroke for visibility
kde_data = [(float(x), float(y)) for x, y in zip(x_range, kde, strict=True)]
chart.add("KDE Curve", kde_data, fill=False, stroke_style={"width": 10})

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
