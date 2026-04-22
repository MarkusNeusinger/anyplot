""" pyplots.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: pygal 3.1.0 | Python 3.13.11
Quality: 86/100 | Created: 2026-01-15
"""

import numpy as np
import pygal
from pygal.style import Style


# Reference impedance
Z0 = 50  # ohms

# Grid parameters
r_values = [0, 0.2, 0.5, 1, 2, 5]  # Constant resistance circles
x_values = [0.2, 0.5, 1, 2, 5]  # Constant reactance arcs

# Custom style - Python Blue boundary, gray grid, prominent data
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#888888",
    colors=("#E74C3C", "#9B59B6", "#F39C12", "#2ECC71", "#306998", "#BBBBBB"),
    title_font_size=56,
    label_font_size=24,
    major_label_font_size=22,
    legend_font_size=28,
    value_font_size=20,
    stroke_width=2,
    opacity=1.0,
    opacity_hover=1.0,
)

# Create XY chart for Smith chart - square format better for circular chart
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="smith-chart-basic · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    show_x_guides=False,
    show_y_guides=False,
    x_title="Reflection Coefficient Real Part",
    y_title="Reflection Coefficient Imaginary Part",
    dots_size=6,
    range=(-1.15, 1.15),
    xrange=(-1.15, 1.15),
    margin=40,
)

# Generate unit circle boundary (|gamma| = 1) - Python Blue (structural, no legend)
theta = np.linspace(0, 2 * np.pi, 200)
unit_circle = [(np.cos(t), np.sin(t)) for t in theta]
chart.add("", unit_circle, show_dots=False, stroke="#306998", stroke_width=4)

# Generate constant resistance circles as a single combined grid element (no legend)
all_r_points = []
for r in r_values:
    x_range = np.concatenate([np.linspace(-50, -0.01, 100), np.linspace(0.01, 50, 100)])
    for x in x_range:
        z_norm = complex(r, x)
        gamma = (z_norm - 1) / (z_norm + 1)
        if abs(gamma) <= 1.001:
            all_r_points.append((gamma.real, gamma.imag))
    all_r_points.append((None, None))
chart.add("", all_r_points, show_dots=False, stroke="#BBBBBB", stroke_width=1.5, stroke_dasharray="8,4")

# Generate constant reactance arcs combined (no legend)
all_x_points = []
for x in x_values:
    # Positive reactance arc
    for r in np.linspace(0.001, 50, 100):
        z_norm = complex(r, x)
        gamma = (z_norm - 1) / (z_norm + 1)
        if abs(gamma) <= 1.001:
            all_x_points.append((gamma.real, gamma.imag))
    all_x_points.append((None, None))
    # Negative reactance arc
    for r in np.linspace(0.001, 50, 100):
        z_norm = complex(r, -x)
        gamma = (z_norm - 1) / (z_norm + 1)
        if abs(gamma) <= 1.001:
            all_x_points.append((gamma.real, gamma.imag))
    all_x_points.append((None, None))
chart.add("", all_x_points, show_dots=False, stroke="#BBBBBB", stroke_width=1.5, stroke_dasharray="8,4")

# Add horizontal axis (real axis, no legend)
chart.add("", [(-1, 0), (1, 0)], show_dots=False, stroke="#555555", stroke_width=3)

# Generate example impedance data - antenna impedance sweep 1-6 GHz
np.random.seed(42)
num_points = 50
frequencies = np.linspace(1e9, 6e9, num_points)  # 1-6 GHz

# Simulate antenna impedance that varies with frequency
base_r = 25 + 50 * np.exp(-frequencies / 3e9)
base_x = 30 * np.sin(2 * np.pi * frequencies / 2e9) + 20 * np.cos(frequencies / 1e9)
z_real = base_r + np.random.randn(num_points) * 3
z_imag = base_x + np.random.randn(num_points) * 5

# Normalize impedance and convert to reflection coefficient
z_complex = z_real + 1j * z_imag
z_normalized = z_complex / Z0
gamma = (z_normalized - 1) / (z_normalized + 1)

# Create impedance locus data points
impedance_locus = [(g.real, g.imag) for g in gamma]

# Add impedance locus curve - Red for visibility
chart.add("Antenna Z(f)", impedance_locus, show_dots=True, stroke_width=4, dots_size=5)

# Add labeled frequency markers at key points
# 1 GHz marker
chart.add("1 GHz", [(gamma[0].real, gamma[0].imag)], show_dots=True, dots_size=16, stroke=False)
# 3.5 GHz marker (midpoint)
chart.add(
    "3.5 GHz", [(gamma[num_points // 2].real, gamma[num_points // 2].imag)], show_dots=True, dots_size=16, stroke=False
)
# 6 GHz marker
chart.add("6 GHz", [(gamma[-1].real, gamma[-1].imag)], show_dots=True, dots_size=16, stroke=False)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
