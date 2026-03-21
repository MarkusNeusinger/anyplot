""" pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: pygal 3.1.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-21
"""

import numpy as np
import pygal
from pygal.style import Style
from scipy import stats


# Data — First-order decomposition reaction rate constants at various temperatures
temperature_K = np.array([300, 330, 360, 400, 440, 480, 520, 560, 600])
np.random.seed(42)
activation_energy = 75000  # J/mol (75 kJ/mol)
R = 8.314  # Gas constant J/(mol·K)
pre_exponential = 1.0e12  # s⁻¹
rate_constant_k = pre_exponential * np.exp(-activation_energy / (R * temperature_K))
# Add realistic experimental scatter (larger noise for visible deviation from fit)
rate_constant_k *= np.exp(np.random.normal(0, 0.25, len(temperature_K)))

# Transformed coordinates for Arrhenius plot
inv_T = 1000.0 / temperature_K  # 1000/T for readable axis values (×10⁻³ K⁻¹)
ln_k = np.log(rate_constant_k)

# Linear regression: ln(k) = ln(A) - Ea/R × (1/T)
slope, intercept, r_value, p_value, std_err = stats.linregress(inv_T, ln_k)
r_squared = r_value**2
Ea_extracted = -slope * R * 1000  # Convert back (factor of 1000 from 1000/T scaling)

# Regression line — extend slightly beyond data for visual clarity
x_pad = 0.04
inv_T_fit = np.linspace(float(min(inv_T)) - x_pad, float(max(inv_T)) + x_pad, 80)
ln_k_fit = slope * inv_T_fit + intercept

# Style — refined palette: teal fit line, warm coral data points, clean typography
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#2c3e50",
    foreground_strong="#1a252f",
    foreground_subtle="#d5d8dc",
    colors=("#1abc9c", "#e74c3c"),
    guide_stroke_color="#ecf0f1",
    major_guide_stroke_color="#d5d8dc",
    guide_stroke_dasharray="4,4",
    title_font_size=68,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=32,
    tooltip_font_size=34,
    stroke_width=4,
    opacity=0.92,
    opacity_hover=1.0,
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    major_label_font_family="sans-serif",
    legend_font_family="sans-serif",
    value_font_family="sans-serif",
)

# Y-axis labels — tight to data range with minimal padding
y_min_data, y_max_data = float(min(ln_k)), float(max(ln_k))
y_floor = int(np.floor(y_min_data))
y_ceil = int(np.ceil(y_max_data))
y_labels_list = list(range(y_floor, y_ceil + 1, 2))
if y_labels_list[-1] < y_ceil:
    y_labels_list.append(y_ceil)

# Chart — pygal XY with tight axis range and polished config
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="line-arrhenius · pygal · pyplots.ai",
    x_title="1000/T (K⁻¹)",
    y_title="ln(k)",
    show_dots=True,
    dots_size=16,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=28,
    truncate_legend=-1,
    margin=50,
    margin_top=80,
    margin_bottom=200,
    margin_left=180,
    margin_right=100,
    tooltip_fancy_mode=True,
    tooltip_border_radius=10,
    x_value_formatter=lambda x: f"{x:.2f}",
    y_value_formatter=lambda y: f"{y:.1f}",
    range=(y_floor - 0.5, y_ceil + 0.5),
    xrange=(float(min(inv_T) - 0.1), float(max(inv_T) + 0.1)),
    y_labels=y_labels_list,
    y_labels_major_every=1,
    print_values=False,
    show_minor_x_labels=False,
    interpolate="cubic",
    css=[
        "file://style.css",
        "file://graph.css",
        "inline:.axis > .line { stroke: transparent !important; } .plot .background { rx: 12; ry: 12; }",
    ],
)

# X-axis labels: 1000/T with temperature in parentheses
x_label_temps = np.array([300, 360, 440, 520, 600])
x_label_positions = sorted(1000.0 / x_label_temps)
chart.x_labels = [float(x) for x in x_label_positions]
chart.x_labels_major = [float(x) for x in x_label_positions]
chart.x_label_rotation = 0
chart.x_value_formatter = lambda x: f"{x:.2f} ({int(round(1000.0 / x))} K)"

# Regression fit line — smooth teal line with Ea and R² encoded in legend
fit_points = [
    {"value": (float(x), float(y)), "label": f"Fit: ln(k) = {slope:.2f} × (1000/T) + {intercept:.2f}"}
    for x, y in zip(inv_T_fit, ln_k_fit, strict=False)
]
chart.add(
    f"Linear Fit: R² = {r_squared:.3f} · Eₐ = {Ea_extracted / 1000:.1f} kJ/mol · slope = {slope:.1f}",
    fit_points,
    show_dots=False,
    stroke_style={"width": 6, "linecap": "round", "linejoin": "round"},
)

# Experimental data points — coral markers with rich tooltips
data_points = [
    {"value": (float(x), float(y)), "label": f"T = {int(t)} K\nk = {k:.3e} s⁻¹\nln(k) = {y:.2f}\n1000/T = {x:.3f}"}
    for x, y, t, k in zip(inv_T, ln_k, temperature_K, rate_constant_k, strict=False)
]
chart.add("Experimental Data", data_points, stroke=False, dots_size=20)

# Save — PNG for static output, HTML with pygal's interactive SVG tooltips
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
