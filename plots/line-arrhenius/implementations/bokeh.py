"""pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: bokeh 3.9.0 | Python 3.14.3
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, Label, LinearAxis, NumeralTickFormatter
from bokeh.models.tickers import FixedTicker
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
        "inv_T_fmt": [f"{x:.4f}" for x in inv_T],
        "ln_k_fmt": [f"{y:.2f}" for y in ln_k],
    }
)
line_source = ColumnDataSource(data={"inv_T": inv_T_line, "ln_k": ln_k_line})

# Create figure - toolbar hidden for clean PNG output
p = figure(
    width=4800,
    height=2700,
    title="line-arrhenius · bokeh · pyplots.ai",
    x_axis_label="1/T (K⁻¹)",
    y_axis_label="ln(k)",
    x_range=(inv_T.min() - 0.00015, inv_T.max() + 0.00015),
    y_range=(ln_k.min() - 1.5, ln_k.max() + 3.5),
    toolbar_location=None,
)

# Background styling
p.background_fill_color = "#F5F7FA"
p.border_fill_color = "#FFFFFF"

# Regression line
p.line(
    "inv_T",
    "ln_k",
    source=line_source,
    line_color="#1A3C5E",
    line_width=6,
    line_alpha=0.85,
    legend_label="Linear Fit (ln k = ln A − Eₐ/RT)",
)

# Data points
scatter_renderer = p.scatter(
    "inv_T",
    "ln_k",
    source=scatter_source,
    size=34,
    color="#306998",
    alpha=0.92,
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

# Annotation: slope, activation energy, R² — positioned in upper-right area
eq_text = f"Slope = −Eₐ/R = {slope:.1f} K\nEₐ = {Ea_fitted / 1000:.1f} kJ/mol\nR² = {r_squared:.4f}"
eq_label = Label(
    x=inv_T[8],
    y=ln_k[6] + 3.5,
    text=eq_text,
    text_font_size="36pt",
    text_color="#1A3C5E",
    text_font_style="bold",
    background_fill_color="#FFFFFF",
    background_fill_alpha=0.88,
    border_line_color="#1A3C5E",
    border_line_alpha=0.3,
    border_line_width=2,
)
p.add_layout(eq_label)

# Secondary x-axis for temperature (above) — no tick labels, just tick marks
temp_label_values = [300, 350, 400, 500, 600]
temp_tick_positions = [1.0 / t for t in temp_label_values]
temp_axis = LinearAxis(
    axis_label="Temperature (K)",
    axis_label_text_font_size="30pt",
    axis_label_text_color="#2C3E50",
    axis_label_text_font_style="bold",
    major_label_text_font_size="24pt",
    major_label_text_color="#444444",
    ticker=FixedTicker(ticks=temp_tick_positions),
    major_tick_line_color="#999999",
    minor_tick_line_color=None,
    axis_line_color="#999999",
)
p.add_layout(temp_axis, "above")

# Manually override tick labels on the secondary axis using per-tick Label annotations
# Bokeh renders these inside the plot area, positioned near the top
for t_val in temp_label_values:
    inv_t_val = 1.0 / t_val
    temp_label = Label(
        x=inv_t_val,
        y=ln_k.max() + 3.0,
        text=str(t_val),
        text_font_size="22pt",
        text_color="#444444",
        text_align="center",
        text_baseline="bottom",
    )
    p.add_layout(temp_label)

# Identify axes: after add_layout(above), xaxis[0] = top, xaxis[1] = bottom
bottom_ax = p.xaxis[1]
top_ax = p.xaxis[0]

# Bottom x-axis: fixed ticks with formatting
bottom_ticks = [round(1.0 / t, 4) for t in [600, 500, 400, 350, 300]]
bottom_ax.ticker = FixedTicker(ticks=bottom_ticks)
bottom_ax.formatter = NumeralTickFormatter(format="0.0000")

# Hide top axis tick labels (we use Label annotations instead)
top_ax.major_label_text_font_size = "0pt"

# Title styling
p.title.text_font_size = "42pt"
p.title.text_color = "#1A3C5E"
p.title.align = "center"
p.title.text_font_style = "bold"

# Bottom x-axis styling
bottom_ax.axis_label_text_font_size = "30pt"
bottom_ax.axis_label_text_color = "#2C3E50"
bottom_ax.axis_label_text_font_style = "bold"
bottom_ax.major_label_text_font_size = "24pt"
bottom_ax.major_label_text_color = "#444444"

# Y-axis styling
p.yaxis.axis_label_text_font_size = "30pt"
p.yaxis.axis_label_text_color = "#2C3E50"
p.yaxis.axis_label_text_font_style = "bold"
p.yaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_color = "#444444"

# Legend styling
p.legend.label_text_font_size = "26pt"
p.legend.location = "bottom_left"
p.legend.background_fill_color = "#FFFFFF"
p.legend.background_fill_alpha = 0.92
p.legend.border_line_color = "#BBBBBB"
p.legend.border_line_alpha = 0.5
p.legend.border_line_width = 2
p.legend.glyph_height = 45
p.legend.glyph_width = 45
p.legend.padding = 30
p.legend.spacing = 18
p.legend.margin = 25

# Grid
p.xgrid.grid_line_color = "#C0C8D0"
p.ygrid.grid_line_color = "#C0C8D0"
p.xgrid.grid_line_alpha = 0.35
p.ygrid.grid_line_alpha = 0.35
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

# Axis lines — apply to bottom x-axis and y-axis
for ax in [bottom_ax, p.yaxis[0]]:
    ax.axis_line_color = "#999999"
    ax.axis_line_width = 2
    ax.minor_tick_line_color = None
    ax.major_tick_line_color = "#999999"
    ax.major_tick_out = 8
    ax.major_tick_in = 0

p.outline_line_color = None

# Generous borders to ensure axis labels are never clipped
p.min_border_bottom = 200
p.min_border_left = 180
p.min_border_top = 160
p.min_border_right = 80

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Arrhenius Plot for Reaction Kinetics")
