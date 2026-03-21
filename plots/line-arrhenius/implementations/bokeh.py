""" pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-21
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, Label, LinearAxis, Range1d
from bokeh.plotting import figure
from bokeh.resources import CDN
from scipy import stats


# Data - first-order decomposition reaction rate constants at various temperatures
np.random.seed(42)
temperature_K = np.array([300, 325, 350, 375, 400, 425, 450, 475, 500, 525, 550, 575, 600])
activation_energy = 75000  # J/mol (typical organic decomposition)
R = 8.314  # gas constant J/(mol·K)
pre_exponential = 1e12  # s^-1

# Generate rate constants from Arrhenius equation with experimental noise
ln_k_true = np.log(pre_exponential) - activation_energy / (R * temperature_K)
noise = np.random.normal(0, 0.15, len(temperature_K))
ln_k = ln_k_true + noise
inv_T = 1.0 / temperature_K

# Linear regression: ln(k) = ln(A) - Ea/R * (1/T)
slope, intercept, r_value, p_value, std_err = stats.linregress(inv_T, ln_k)
r_squared = r_value**2
Ea_fitted = -slope * R  # activation energy from slope

# Regression line
inv_T_line = np.linspace(inv_T.min() - 0.00005, inv_T.max() + 0.00005, 200)
ln_k_line = slope * inv_T_line + intercept

# Data sources
scatter_source = ColumnDataSource(
    data={
        "inv_T": inv_T,
        "ln_k": ln_k,
        "T_K": temperature_K,
        "inv_T_fmt": [f"{x:.2e}" for x in inv_T],
        "ln_k_fmt": [f"{y:.2f}" for y in ln_k],
    }
)
line_source = ColumnDataSource(data={"inv_T": inv_T_line, "ln_k": ln_k_line})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="line-arrhenius · bokeh · pyplots.ai",
    x_axis_label="1/T (K⁻¹)",
    y_axis_label="ln(k)",
    x_range=(inv_T.min() - 0.0001, inv_T.max() + 0.0001),
    y_range=(ln_k.min() - 1.0, ln_k.max() + 1.5),
)

# Background styling
p.background_fill_color = "#F7F9FC"
p.border_fill_color = "#FFFFFF"

# Regression line
p.line("inv_T", "ln_k", source=line_source, line_color="#1A5276", line_width=5, legend_label="Linear Fit")

# Data points
scatter_renderer = p.scatter(
    "inv_T",
    "ln_k",
    source=scatter_source,
    size=32,
    color="#306998",
    alpha=0.9,
    line_color="white",
    line_width=3,
    legend_label="Experimental Data",
)

# HoverTool
hover = HoverTool(
    renderers=[scatter_renderer],
    tooltips=[("Temperature", "@T_K K"), ("1/T", "@inv_T_fmt K⁻¹"), ("ln(k)", "@ln_k_fmt")],
    mode="mouse",
)
p.add_tools(hover)

# Annotation: R² value and activation energy
eq_text = f"Slope = {slope:.1f} K\nEₐ = {Ea_fitted / 1000:.1f} kJ/mol\nR² = {r_squared:.4f}"
eq_label = Label(
    x=inv_T[2],
    y=ln_k.max() + 0.8,
    text=eq_text,
    text_font_size="34pt",
    text_color="#1A5276",
    text_font_style="bold",
    background_fill_color="#F7F9FC",
    background_fill_alpha=0.9,
)
p.add_layout(eq_label)

# Secondary x-axis showing temperature in K
# Add temperature labels as annotation at the top
p.extra_x_ranges = {"temp_range": Range1d(start=1 / (inv_T.min() - 0.0001), end=1 / (inv_T.max() + 0.0001))}
temp_axis = LinearAxis(
    x_range_name="temp_range",
    axis_label="Temperature (K)",
    axis_label_text_font_size="28pt",
    axis_label_text_color="#2C3E50",
    major_label_text_font_size="22pt",
    major_label_text_color="#555555",
)
p.add_layout(temp_axis, "above")

# Style
p.title.text_font_size = "40pt"
p.title.text_color = "#2C3E50"
p.title.align = "center"

p.xaxis[0].axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis[0].axis_label_text_color = "#2C3E50"
p.yaxis.axis_label_text_color = "#2C3E50"
p.xaxis[0].major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"
p.xaxis[0].major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

p.legend.label_text_font_size = "26pt"
p.legend.location = "bottom_left"
p.legend.background_fill_color = "#F7F9FC"
p.legend.background_fill_alpha = 0.92
p.legend.border_line_color = "#CCCCCC"
p.legend.border_line_alpha = 0.4
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.padding = 25
p.legend.spacing = 15
p.legend.margin = 20

# Grid
p.xgrid.grid_line_color = "#CCCCCC"
p.ygrid.grid_line_color = "#CCCCCC"
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [4, 4]
p.ygrid.grid_line_dash = [4, 4]

p.axis.axis_line_color = "#AAAAAA"
p.axis.axis_line_width = 1
p.axis.minor_tick_line_color = None
p.axis.major_tick_line_color = "#AAAAAA"

p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Arrhenius Plot for Reaction Kinetics")
