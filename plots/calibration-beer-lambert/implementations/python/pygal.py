""" pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: pygal 3.1.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-09
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

# Regression line points (tightened to data range)
conc_fit = np.linspace(-0.3, 12.8, 100)
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

# Style with refined guide colors for subtle grid
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2c3e50",
    foreground_strong="#2c3e50",
    foreground_subtle="#e8e8e8",
    colors=("#306998", "#1a5276", "#5a9abf", "#c0392b"),
    guide_stroke_color="#e8e8e8",
    major_guide_stroke_color="#d5d5d5",
    guide_stroke_dasharray="2,2",
    major_guide_stroke_dasharray="",
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=5,
    opacity=0.95,
    opacity_hover=1.0,
)

# Chart with custom CSS to hide axis spines/frame lines
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="calibration-beer-lambert · pygal · pyplots.ai",
    x_title="Concentration (mg/L)",
    y_title="Absorbance",
    show_dots=True,
    dots_size=18,
    show_x_guides=False,
    show_y_guides=True,
    xrange=(-0.3, 13.0),
    range=(-0.02, 0.62),
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=30,
    truncate_legend=-1,
    margin=50,
    margin_top=80,
    margin_bottom=200,
    tooltip_fancy_mode=True,
    tooltip_border_radius=8,
    print_labels=False,
    x_value_formatter=lambda x: f"{x:.1f}",
    y_value_formatter=lambda y: f"{y:.3f}",
    css=["file://style.css", "file://graph.css", "inline:.axis > .line { stroke: transparent !important; }"],
)

# Calibration standards with rich value dicts for interactive tooltips
std_points = [
    {"value": (float(c), float(a)), "label": f"Standard {i + 1}: {c:.1f} mg/L, A = {a:.4f}", "color": "#306998"}
    for i, (c, a) in enumerate(zip(concentration, absorbance, strict=False))
]
chart.add("Calibration Standards", std_points, stroke=False, dots_size=18)

# Regression fit line
fit_points = [
    {"value": (float(x), float(y)), "label": f"Fit: A = {slope:.4f} × {x:.1f} + {intercept:.4f} = {y:.4f}"}
    for x, y in zip(conc_fit, abs_fit, strict=False)
]
chart.add(
    f"Fit: A = {slope:.4f}·C + {intercept:.4f} (R² = {r_squared:.4f})",
    fit_points,
    show_dots=False,
    stroke_style={"width": 5},
)

# Prediction interval — both bands in a single series to avoid empty legend
# Upper band followed by lower band with a None gap
pi_points = [
    {"value": (float(x), float(y)), "label": f"Upper 95% PI: {y:.4f} at C = {x:.1f}"}
    for x, y in zip(conc_fit, upper_band, strict=False)
]
pi_points.append(None)
pi_points.extend(
    {"value": (float(x), float(y)), "label": f"Lower 95% PI: {y:.4f} at C = {x:.1f}"}
    for x, y in zip(conc_fit, lower_band, strict=False)
)
chart.add("95% Prediction Interval", pi_points, show_dots=False, stroke_style={"width": 4}, stroke_dasharray="10,5")

# Unknown sample crosshair — both H and V lines in single series
unknown_points = [
    {"value": (-0.3, unknown_absorbance), "label": f"Unknown: A = {unknown_absorbance:.3f}"},
    {
        "value": (float(unknown_concentration), unknown_absorbance),
        "label": f"Intersection: C = {unknown_concentration:.2f} mg/L",
    },
    None,
    {"value": (float(unknown_concentration), unknown_absorbance), "label": f"C = {unknown_concentration:.2f} mg/L"},
    {"value": (float(unknown_concentration), 0.0), "label": f"Determined: {unknown_concentration:.2f} mg/L"},
]
chart.add(
    f"Unknown → {unknown_concentration:.2f} mg/L",
    unknown_points,
    stroke_dasharray="14,7",
    dots_size=14,
    stroke_style={"width": 4},
)

# Save — dual render leveraging pygal's native SVG+HTML interactivity
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
