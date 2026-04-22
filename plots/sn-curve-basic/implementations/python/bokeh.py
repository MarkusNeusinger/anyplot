""" pyplots.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-15
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure


# Data - Typical S-N fatigue test results for steel specimens
np.random.seed(42)

# Generate realistic S-N curve data points
# Basquin equation: S = A * N^b (power law relationship)
# Using typical steel fatigue parameters
A = 1200  # MPa (coefficient)
b = -0.12  # Basquin exponent

# Create stress levels with multiple specimens at each level
stress_levels = np.array([450, 400, 350, 320, 300, 280, 260, 250, 240, 230, 220, 210])

# Generate cycles for each stress level with realistic scatter
cycles_list = []
stress_list = []

for stress in stress_levels:
    # Calculate theoretical cycles from Basquin equation
    N_theoretical = (stress / A) ** (1 / b)
    # Add scatter (typical for fatigue data)
    n_specimens = np.random.randint(2, 5)
    scatter = np.random.lognormal(0, 0.3, n_specimens)
    cycles_actual = N_theoretical * scatter
    cycles_list.extend(cycles_actual)
    stress_list.extend([stress] * n_specimens)

cycles = np.array(cycles_list)
stress = np.array(stress_list)

# Material properties reference values
ultimate_strength = 500  # MPa
yield_strength = 350  # MPa
endurance_limit = 200  # MPa (below which infinite life expected)

# Fit line data (using Basquin equation)
cycles_fit = np.logspace(2, 7, 100)
stress_fit = A * (cycles_fit**b)

# Create ColumnDataSource for data points
source = ColumnDataSource(data={"cycles": cycles, "stress": stress})

# Create ColumnDataSource for fit line
source_fit = ColumnDataSource(data={"cycles_fit": cycles_fit, "stress_fit": stress_fit})

# Create figure with log scales
p = figure(
    width=4800,
    height=2700,
    title="sn-curve-basic · bokeh · pyplots.ai",
    x_axis_label="Number of Cycles to Failure (N)",
    y_axis_label="Stress Amplitude (MPa)",
    x_axis_type="log",
    y_axis_type="log",
    y_range=(150, 600),
    x_range=(100, 2e7),
)

# Plot S-N curve fit line
p.line(
    x="cycles_fit",
    y="stress_fit",
    source=source_fit,
    line_width=5,
    line_color="#306998",
    line_alpha=0.9,
    legend_label="Basquin Fit (S = A·N^b)",
)

# Plot data points
p.scatter(
    x="cycles",
    y="stress",
    source=source,
    size=22,
    fill_color="#306998",
    fill_alpha=0.7,
    line_color="#1a3d5c",
    line_width=2,
    legend_label="Fatigue Test Data",
)

# Add horizontal reference lines for material properties
ultimate_line = Span(
    location=ultimate_strength, dimension="width", line_color="#c0392b", line_width=4, line_dash="dashed"
)
p.add_layout(ultimate_line)

yield_line = Span(location=yield_strength, dimension="width", line_color="#e67e22", line_width=4, line_dash="dashed")
p.add_layout(yield_line)

endurance_line = Span(
    location=endurance_limit, dimension="width", line_color="#27ae60", line_width=4, line_dash="dashed"
)
p.add_layout(endurance_line)

# Add labels for reference lines
ultimate_label = Label(
    x=150,
    y=520,
    text=f"Ultimate Strength ({ultimate_strength} MPa)",
    text_font_size="22pt",
    text_color="#c0392b",
    text_font_style="bold",
)
p.add_layout(ultimate_label)

yield_label = Label(
    x=150,
    y=365,
    text=f"Yield Strength ({yield_strength} MPa)",
    text_font_size="22pt",
    text_color="#e67e22",
    text_font_style="bold",
)
p.add_layout(yield_label)

endurance_label = Label(
    x=150,
    y=208,
    text=f"Endurance Limit ({endurance_limit} MPa)",
    text_font_size="22pt",
    text_color="#27ae60",
    text_font_style="bold",
)
p.add_layout(endurance_label)

# Style the plot
p.title.text_font_size = "36pt"
p.title.text_color = "#2c3e50"
p.xaxis.axis_label_text_font_size = "26pt"
p.yaxis.axis_label_text_font_size = "26pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Legend styling
p.legend.location = "bottom_left"
p.legend.label_text_font_size = "22pt"
p.legend.background_fill_alpha = 0.9
p.legend.border_line_width = 2
p.legend.border_line_color = "#cccccc"
p.legend.glyph_width = 50
p.legend.glyph_height = 35
p.legend.spacing = 12
p.legend.padding = 20

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Save as PNG
export_png(p, filename="plot.png")
