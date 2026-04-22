""" pyplots.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-30
"""

import numpy as np
import pygal
from pygal.style import Style
from statsmodels.nonparametric.smoothers_lowess import lowess


# Data - Drug dose-response relationship with non-linear effect
# Simulates enzyme activity response to varying drug concentrations
np.random.seed(42)
n_points = 150

# Drug concentration in mg/L (log-spaced for pharmacological realism)
concentration = np.linspace(0.1, 50, n_points)

# Enzyme activity response: sigmoidal with saturation and hormesis effect
# Low doses show slight stimulation, mid-range shows increase, high doses plateau
base_response = 25 + 55 * (1 - np.exp(-concentration / 8)) - 10 * np.exp(-concentration / 3)
noise = np.random.normal(0, 4, n_points)
activity = base_response + noise

# Calculate LOWESS smoothed curve
lowess_result = lowess(activity, concentration, frac=0.35, return_sorted=True)
conc_smooth = lowess_result[:, 0]
activity_smooth = lowess_result[:, 1]

# Custom style for large canvas with increased font sizes
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#E74C3C"),
    title_font_size=56,
    label_font_size=42,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=28,
    stroke_width=5,
    opacity=0.6,
    opacity_hover=0.9,
)

# Create XY chart for scatter plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-regression-lowess · pygal · pyplots.ai",
    x_title="Drug Concentration (mg/L)",
    y_title="Enzyme Activity (%)",
    show_dots=True,
    dots_size=8,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
)

# Add scatter points (as XY data with no stroke)
scatter_data = list(zip(concentration, activity, strict=True))
chart.add("Observed Response", scatter_data, stroke=False, dots_size=10)

# Add LOWESS curve (as line with no dots)
lowess_data = list(zip(conc_smooth, activity_smooth, strict=True))
chart.add("LOWESS Fit (frac=0.35)", lowess_data, stroke=True, show_dots=False, stroke_style={"width": 6})

# Save as PNG and SVG/HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
