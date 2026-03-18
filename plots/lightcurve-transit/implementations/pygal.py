"""pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: pygal 3.1.0 | Python 3.14.3
Quality: 74/100 | Created: 2026-03-18
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - simulated exoplanet transit (phase-folded)
np.random.seed(42)

n_points = 200
phase = np.sort(np.random.uniform(0.0, 1.0, n_points))

# Transit parameters
transit_center = 0.5
transit_duration = 0.08
transit_depth = 0.01

# Smooth transit model using a Gaussian-like dip for limb-darkened shape
model_phase = np.linspace(0.0, 1.0, 500)
sigma = transit_duration / 3.5
model_flux_curve = 1.0 - transit_depth * np.exp(-0.5 * ((model_phase - transit_center) / sigma) ** 2)

# Interpolate model at observation phases
model_flux = np.interp(phase, model_phase, model_flux_curve)

# Observed flux with noise
flux_err = np.random.uniform(0.0015, 0.003, n_points)
flux = model_flux + np.random.normal(0, 1, n_points) * flux_err

# Separate in-transit and out-of-transit points for visual storytelling
in_transit = np.abs(phase - transit_center) < transit_duration * 1.8

# Error bar segments: vertical lines from (x, y-err) to (x, y+err) with None separators
error_bar_points = []
for i in range(n_points):
    x = round(float(phase[i]), 5)
    y_lo = round(float(flux[i] - flux_err[i]), 6)
    y_hi = round(float(flux[i] + flux_err[i]), 6)
    error_bar_points.append((x, y_lo))
    error_bar_points.append((x, y_hi))
    error_bar_points.append(None)

# Colors: series order is Error Bars, Out-of-Transit, In-Transit, Transit Model
custom_style = Style(
    background="#FAFAFA",
    plot_background="#FAFAFA",
    foreground="#2D2D2D",
    foreground_strong="#1A1A1A",
    foreground_subtle="#D8D8D8",
    colors=("#B0B0B0", "#306998", "#C44E52", "#E67E22"),
    title_font_size=56,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=34,
    value_font_size=28,
    stroke_width=3,
    opacity=0.75,
    opacity_hover=0.9,
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    major_label_font_family="sans-serif",
    legend_font_family="sans-serif",
)

# Model curve points (dense, for smooth line)
model_points = [
    (round(float(model_phase[i]), 5), round(float(model_flux_curve[i]), 6)) for i in range(len(model_phase))
]

# Scatter data points with custom tooltips
out_transit_points = []
in_transit_points = []
for i in range(n_points):
    pt = {
        "value": (round(float(phase[i]), 5), round(float(flux[i]), 6)),
        "label": f"φ={phase[i]:.3f}  F={flux[i]:.4f}±{flux_err[i]:.4f}",
    }
    if in_transit[i]:
        in_transit_points.append(pt)
    else:
        out_transit_points.append(pt)

# Plot
flux_min = float(np.min(flux)) - 0.004
flux_max = float(np.max(flux)) + 0.004

chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="lightcurve-transit · pygal · pyplots.ai",
    x_title="Orbital Phase",
    y_title="Relative Flux",
    show_x_guides=False,
    show_y_guides=True,
    dots_size=5,
    range=(flux_min, flux_max),
    xrange=(0.0, 1.0),
    margin_right=80,
    margin_left=60,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    tooltip_border_radius=8,
    x_value_formatter=lambda x: f"{x:.2f}",
    y_value_formatter=lambda y: f"{y:.4f}",
)

# Error bars first (renders behind data points) - subtle gray
chart.add("1σ Error Bars", error_bar_points, stroke=True, show_dots=False, stroke_width=1)

# Out-of-transit data points - blue
chart.add("Out-of-Transit", out_transit_points, stroke=False, dots_size=5)

# In-transit data points - red, larger for emphasis
chart.add("In-Transit", in_transit_points, stroke=False, dots_size=8)

# Transit model overlay - orange, prominent
chart.add("Transit Model", model_points, stroke=True, show_dots=False, stroke_width=5)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
