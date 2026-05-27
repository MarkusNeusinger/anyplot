""" anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pygal
from pygal.style import Style
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - Drug dose-response relationship with non-linear effect
np.random.seed(42)
n_points = 150

# Drug concentration in mg/L (log-spaced for pharmacological realism)
concentration = np.linspace(0.1, 50, n_points)

# Enzyme activity response: sigmoidal with saturation and hormesis effect
base_response = 25 + 55 * (1 - np.exp(-concentration / 8)) - 10 * np.exp(-concentration / 3)
noise = np.random.normal(0, 4, n_points)
activity = base_response + noise

# Calculate LOWESS smoothed curve
lowess_result = lowess(activity, concentration, frac=0.35, return_sorted=True)
conc_smooth = lowess_result[:, 0]
activity_smooth = lowess_result[:, 1]

# Custom style with theme-adaptive tokens
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
    opacity=0.6,
    opacity_hover=0.9,
)

# Create XY chart for scatter plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-regression-lowess · pygal · anyplot.ai",
    x_title="Drug Concentration (mg/L)",
    y_title="Enzyme Activity (%)",
    show_dots=True,
    dots_size=8,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
)

# Add scatter points (brand green - Okabe-Ito position 1)
scatter_data = list(zip(concentration, activity, strict=True))
chart.add("Observed Response", scatter_data, stroke=False, dots_size=10)

# Add LOWESS curve (vermillion - Okabe-Ito position 2)
lowess_data = list(zip(conc_smooth, activity_smooth, strict=True))
chart.add("LOWESS Fit (frac=0.35)", lowess_data, stroke=True, show_dots=False, stroke_style={"width": 6})

# Save as PNG and HTML with theme suffix
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
