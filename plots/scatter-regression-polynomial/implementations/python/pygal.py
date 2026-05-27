""" anyplot.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: pygal 3.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-07
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette
BRAND = "#009E73"  # First series
ACCENT = "#C475FD"  # Second series

# Data
np.random.seed(42)
n_points = 80
x = np.linspace(2, 14, n_points)
y_true = -2.5 * x**2 + 45 * x - 80
y = y_true + np.random.randn(n_points) * 12

# Fit polynomial (degree 2)
coeffs = np.polyfit(x, y, 2)
poly = np.poly1d(coeffs)

# Calculate R²
y_pred = poly(x)
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Generate curve
x_curve = np.linspace(x.min(), x.max(), 200)
y_curve = poly(x_curve)

# Polynomial equation
a, b, c = coeffs
equation = f"y = {a:.2f}x² + {b:.2f}x + {c:.2f}"

# Custom style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND, ACCENT),
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Create chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-regression-polynomial · pygal · anyplot.ai",
    x_title="Sunlight Exposure (hours)",
    y_title="Plant Growth (cm)",
    show_legend=True,
    legend_at_bottom=False,
    dots_size=8,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    stroke_style={"width": 3},
)

# Prepare data as (x, y) tuples
scatter_data = [(float(x[i]), float(y[i])) for i in range(len(x))]
curve_data = [(float(x_curve[i]), float(y_curve[i])) for i in range(len(x_curve))]

# Add series
chart.add("Data Points", scatter_data, stroke=False, dots_size=8, opacity=0.7)
chart.add(f"Polynomial Fit (R²={r_squared:.3f})", curve_data, stroke=True, show_dots=False, dots_size=0)

# Add equation annotation as a legend subtitle
chart.add(f"Equation: {equation}", [], stroke=False, dots_size=0, show_legend=False)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
