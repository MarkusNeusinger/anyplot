""" pyplots.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-17
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure


# Generate synthetic atmospheric sounding data
np.random.seed(42)

# Pressure levels (hPa) - from surface to upper troposphere
pressure = np.array(
    [
        1000,
        975,
        950,
        925,
        900,
        875,
        850,
        825,
        800,
        775,
        750,
        725,
        700,
        650,
        600,
        550,
        500,
        450,
        400,
        350,
        300,
        250,
        200,
        150,
        100,
    ]
)

# Temperature profile (°C) - typical mid-latitude sounding with inversion
temperature = np.array(
    [25, 23, 21, 19, 17, 15, 13, 11, 9, 7, 5, 3, 1, -3, -8, -14, -20, -28, -36, -44, -52, -58, -62, -66, -68]
)

# Add some realistic variation
temperature = temperature + np.random.randn(len(temperature)) * 0.5

# Dewpoint profile (°C) - always <= temperature
dewpoint = np.array(
    [20, 18, 16, 14, 12, 10, 7, 4, 1, -3, -7, -12, -17, -24, -32, -40, -45, -50, -54, -58, -62, -66, -70, -74, -78]
)
dewpoint = dewpoint + np.random.randn(len(temperature)) * 0.3

# Ensure dewpoint is always less than or equal to temperature
dewpoint = np.minimum(dewpoint, temperature - 0.5)

# Skew factor for temperature transformation
SKEW_FACTOR = 45

# Pressure range for reference lines
p_range = np.logspace(np.log10(1000), np.log10(100), 50)

# Create figure with appropriate size and y-axis (pressure)
p = figure(
    width=4800,
    height=2700,
    title="skewt-logp-atmospheric · bokeh · pyplots.ai",
    x_axis_label="Temperature (°C) - Skewed Coordinates",
    y_axis_label="Pressure (hPa)",
    y_axis_type="log",
    y_range=(1050, 95),  # Inverted: surface at bottom
    x_range=(-50, 50),
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Style the figure
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.background_fill_color = "#f8f9fa"
p.grid.grid_line_alpha = 0.3

# Draw isotherms (skewed temperature lines)
isotherm_temps = np.arange(-80, 50, 10)
for t in isotherm_temps:
    # Inline skew transformation: x = temp - skew_factor * log10(pres / 1000)
    log_p = np.log10(p_range / 1000.0)
    x_iso = np.full_like(p_range, t) - SKEW_FACTOR * log_p
    source_iso = ColumnDataSource(data={"x": x_iso, "y": p_range})
    p.line(x="x", y="y", source=source_iso, line_color="#cccccc", line_width=1.5, line_alpha=0.7)

# Draw dry adiabats (lines of constant potential temperature)
# Dry adiabat: T = theta * (p / p0)^kappa - 273.15
theta_values = np.arange(250, 400, 20)  # Potential temperatures in K
p0 = 1000.0
kappa = 0.286
for theta in theta_values:
    t_adiabat = theta * (p_range / p0) ** kappa - 273.15
    log_p = np.log10(p_range / 1000.0)
    x_adiabat = t_adiabat - SKEW_FACTOR * log_p
    # Only plot within reasonable temperature range
    mask = (t_adiabat > -80) & (t_adiabat < 60)
    if np.any(mask):
        source_ad = ColumnDataSource(data={"x": x_adiabat[mask], "y": p_range[mask]})
        p.line(x="x", y="y", source=source_ad, line_color="#d4a574", line_width=1.5, line_alpha=0.6, line_dash="dashed")

# Draw mixing ratio lines (simplified - vertical lines at specific humidities)
mixing_ratios = [1, 2, 4, 8, 12, 16, 20]  # g/kg
for mr in mixing_ratios:
    # Approximate dewpoint from mixing ratio at different pressures
    td_mr = -40 + 10 * np.log10(mr + 1)  # Simplified approximation
    log_p = np.log10(p_range / 1000.0)
    x_mr = np.full_like(p_range, td_mr) - SKEW_FACTOR * log_p
    source_mr = ColumnDataSource(data={"x": x_mr, "y": p_range})
    p.line(x="x", y="y", source=source_mr, line_color="#8fbf8f", line_width=1.2, line_alpha=0.5, line_dash="dotted")

# Draw moist adiabats (pseudoadiabats) - simplified approximation
moist_start_temps = np.arange(-10, 35, 10)
for t_start in moist_start_temps:
    # Build moist adiabat iteratively (simplified moist adiabatic lapse rate ~6°C/km)
    t_moist = [t_start]
    p_prev = 1000.0
    t_prev = t_start
    for p_level in p_range[1:]:
        dp = p_prev - p_level
        dt = -0.006 * dp * 10 * 0.5  # Approximate moist lapse rate
        t_new = t_prev + dt
        t_moist.append(t_new)
        p_prev = p_level
        t_prev = t_new
    t_moist = np.array(t_moist)
    log_p = np.log10(p_range / 1000.0)
    x_moist = t_moist - SKEW_FACTOR * log_p
    mask = (t_moist > -80) & (t_moist < 60)
    if np.any(mask):
        source_moist = ColumnDataSource(data={"x": x_moist[mask], "y": p_range[mask]})
        p.line(
            x="x", y="y", source=source_moist, line_color="#7eb5d6", line_width=1.5, line_alpha=0.5, line_dash="dotdash"
        )

# Plot temperature profile (solid red line)
log_p_temp = np.log10(pressure / 1000.0)
x_temp = temperature - SKEW_FACTOR * log_p_temp
source_temp = ColumnDataSource(data={"x": x_temp, "y": pressure, "temp": temperature})
p.line(x="x", y="y", source=source_temp, line_color="#e63946", line_width=5, legend_label="Temperature")
p.scatter(x="x", y="y", source=source_temp, size=12, color="#e63946", alpha=0.8)

# Plot dewpoint profile (dashed green line)
x_dewpoint = dewpoint - SKEW_FACTOR * log_p_temp
source_dew = ColumnDataSource(data={"x": x_dewpoint, "y": pressure, "dewpoint": dewpoint})
p.line(x="x", y="y", source=source_dew, line_color="#2a9d8f", line_width=5, line_dash="dashed", legend_label="Dewpoint")
p.scatter(x="x", y="y", source=source_dew, size=12, color="#2a9d8f", alpha=0.8, marker="diamond")

# Add freezing line (0°C isotherm highlighted)
log_p_freeze = np.log10(p_range / 1000.0)
x_freeze = np.full_like(p_range, 0) - SKEW_FACTOR * log_p_freeze
source_freeze = ColumnDataSource(data={"x": x_freeze, "y": p_range})
p.line(
    x="x", y="y", source=source_freeze, line_color="#457b9d", line_width=3, line_alpha=0.8, legend_label="0°C Isotherm"
)

# Configure legend with larger font size for better readability
p.legend.location = "top_left"
p.legend.label_text_font_size = "24pt"
p.legend.background_fill_alpha = 0.8
p.legend.border_line_width = 2
p.legend.glyph_height = 30
p.legend.glyph_width = 30
p.legend.spacing = 10
p.legend.padding = 15

# Add reference line labels using annotations with larger font size
label_dry = Label(x=-35, y=350, text="Dry Adiabats", text_font_size="22pt", text_color="#d4a574", text_alpha=1.0)
label_moist = Label(x=25, y=200, text="Moist Adiabats", text_font_size="22pt", text_color="#7eb5d6", text_alpha=1.0)
label_mixing = Label(x=-48, y=600, text="Mixing Ratio", text_font_size="22pt", text_color="#8fbf8f", text_alpha=1.0)
p.add_layout(label_dry)
p.add_layout(label_moist)
p.add_layout(label_mixing)

# Save outputs
export_png(p, filename="plot.png")

# Save interactive HTML version
output_file("plot.html")
save(p)
