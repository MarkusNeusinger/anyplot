""" pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-09
"""

import numpy as np
import pygal
from pygal.style import Style
from scipy import stats


# Data: Calibration standards for copper sulfate at 810 nm
np.random.seed(42)
concentration = np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0])
true_absorbance = 0.045 * concentration + 0.003
noise = np.random.normal(0, 0.004, len(concentration))
absorbance = true_absorbance + noise
absorbance[0] = 0.002

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(concentration, absorbance)
r_squared = r_value**2

# Regression line points
conc_fit = np.linspace(-0.5, 13.5, 100)
abs_fit = slope * conc_fit + intercept

# Prediction interval
n = len(concentration)
conc_mean = np.mean(concentration)
se_fit = std_err * np.sqrt(1 + 1 / n + (conc_fit - conc_mean) ** 2 / np.sum((concentration - conc_mean) ** 2))
t_crit = stats.t.ppf(0.975, n - 2)
upper_band = abs_fit + t_crit * se_fit
lower_band = abs_fit - t_crit * se_fit

# Unknown sample
unknown_absorbance = 0.350
unknown_concentration = (unknown_absorbance - intercept) / slope

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#CCCCCC",
    colors=("#306998", "#306998", "#A8C4D8", "#A8C4D8", "#C0392B", "#C0392B"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=5,
    opacity=0.9,
    opacity_hover=1.0,
)

# Chart
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="Beer-Lambert Calibration · calibration-beer-lambert · pygal · pyplots.ai",
    x_title="Concentration (mg/L)",
    y_title="Absorbance",
    show_dots=True,
    dots_size=16,
    show_x_guides=False,
    show_y_guides=True,
    xrange=(-0.5, 14.0),
    range=(-0.02, 0.65),
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=28,
    truncate_legend=-1,
    margin=50,
    margin_top=80,
    margin_bottom=200,
    x_value_formatter=lambda x: f"{x:.1f}",
    y_value_formatter=lambda y: f"{y:.3f}",
)

# Calibration standards
std_points = [
    {"value": (c, a), "label": f"{c:.1f} mg/L → A = {a:.4f}"} for c, a in zip(concentration, absorbance, strict=False)
]
chart.add("Calibration Standards", std_points, stroke=False, dots_size=16)

# Regression fit line
fit_points = [(float(x), float(y)) for x, y in zip(conc_fit, abs_fit, strict=False)]
chart.add(
    f"Fit: A = {slope:.4f}·C + {intercept:.4f} (R² = {r_squared:.4f})",
    fit_points,
    show_dots=False,
    stroke_style={"width": 5},
)

# Prediction interval upper
upper_points = [(float(x), float(y)) for x, y in zip(conc_fit, upper_band, strict=False)]
chart.add("95% Prediction Interval", upper_points, show_dots=False, stroke_style={"width": 2}, stroke_dasharray="8,4")

# Prediction interval lower
lower_points = [(float(x), float(y)) for x, y in zip(conc_fit, lower_band, strict=False)]
chart.add("", lower_points, show_dots=False, stroke_style={"width": 2}, stroke_dasharray="8,4")

# Unknown sample - horizontal dashed line from y-axis to point
unknown_h_points = [
    {"value": (0.0, unknown_absorbance), "label": f"Unknown A = {unknown_absorbance:.3f}"},
    {"value": (unknown_concentration, unknown_absorbance), "label": f"→ C = {unknown_concentration:.2f} mg/L"},
]
chart.add(
    f"Unknown → {unknown_concentration:.2f} mg/L",
    unknown_h_points,
    stroke_dasharray="12,6",
    dots_size=12,
    stroke_style={"width": 3},
)

# Unknown sample - vertical dashed line from point down to x-axis
unknown_v_points = [
    {"value": (unknown_concentration, unknown_absorbance), "label": f"C = {unknown_concentration:.2f} mg/L"},
    {"value": (unknown_concentration, 0.0), "label": f"Determined concentration: {unknown_concentration:.2f} mg/L"},
]
chart.add("", unknown_v_points, stroke_dasharray="12,6", dots_size=0, stroke_style={"width": 3})

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
