""" pyplots.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: pygal 3.1.0 | Python 3.13.11
Quality: 68/100 | Created: 2026-01-17
"""

import numpy as np
import pygal
from pygal.style import Style


np.random.seed(42)

# Generate realistic atmospheric sounding data
# Pressure levels from surface (1000 hPa) to upper troposphere (100 hPa)
pressure = np.array([1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100])

# Temperature profile (typical mid-latitude sounding, decreasing with altitude)
temperature = np.array([25, 20, 15, 5, -15, -28, -45, -52, -58, -62, -55])

# Dewpoint profile (always <= temperature, converges in clouds)
dewpoint = np.array([18, 15, 12, -2, -22, -38, -55, -60, -65, -70, -65])

# For Skew-T Log-P: Y-axis uses log of pressure
# log_p will be 0 at 1000 hPa and positive going up to lower pressures
log_p = np.log10(1000.0 / pressure)

# Apply skew transformation to temperature (45 degree isotherms)
skew_factor = 35
temp_skewed = temperature + skew_factor * log_p
dewpoint_skewed = dewpoint + skew_factor * log_p

# Create custom style with LARGER fonts for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="#f8f9fa",
    foreground="#2c3e50",
    foreground_strong="#1a252f",
    foreground_subtle="#5d6d7e",
    colors=(
        "#c0392b",  # Temperature - dark red
        "#2471a3",  # Dewpoint - blue
        "#229954",  # Dry adiabat - green
        "#7d3c98",  # Moist adiabat - purple
        "#d35400",  # Mixing ratio - orange
        "#95a5a6",  # Isotherms - gray
    ),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=32,
    stroke_width=4,
)

# Create mapping from log_p values to pressure labels
# These values correspond to standard pressure levels
log_p_values = [0, 0.033, 0.07, 0.155, 0.301, 0.398, 0.523, 0.602, 0.699, 0.824, 1.0]
p_labels = ["1000", "925", "850", "700", "500", "400", "300", "250", "200", "150", "100"]

# Create XY chart with explicit margin for legend visibility
chart = pygal.XY(
    width=4800,
    height=3000,
    style=custom_style,
    title="skewt-logp-atmospheric · pygal · pyplots.ai",
    x_title="Temperature (°C, skewed 45°)",
    y_title="Pressure (hPa)",
    show_dots=True,
    dots_size=8,
    stroke_style={"width": 5},
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=28,
    margin_bottom=180,
    range=(0, 1.02),
    xrange=(-50, 75),
    y_labels=[{"value": v, "label": lbl} for v, lbl in zip(log_p_values, p_labels, strict=False)],
    truncate_legend=-1,
)

# Add temperature profile (solid red line with markers)
temp_points = [(float(temp_skewed[i]), float(log_p[i])) for i in range(len(pressure))]
chart.add("Temperature", temp_points, stroke_style={"width": 6})

# Add dewpoint profile (blue dashed line with markers)
dewpoint_points = [(float(dewpoint_skewed[i]), float(log_p[i])) for i in range(len(pressure))]
chart.add("Dewpoint", dewpoint_points, stroke_style={"width": 5, "dasharray": "15,8"})

# Add ONE dry adiabat (θ=300K) - green curved line
theta = 300
dry_adiabat_points = []
for p in np.linspace(1000, 100, 25):
    lp = np.log10(1000.0 / p)
    T_adiabat = theta * (p / 1000.0) ** 0.286 - 273.15
    T_skewed = T_adiabat + skew_factor * lp
    if -50 <= T_skewed <= 75:
        dry_adiabat_points.append((float(T_skewed), float(lp)))
chart.add("Dry Adiabat θ=300K", dry_adiabat_points, show_dots=False, stroke_style={"width": 3, "dasharray": "6,4"})

# Add ONE moist adiabat (starting at 20°C) - purple curved line
moist_points = []
t_current = 20.0
for p in np.linspace(1000, 150, 20):
    lp = np.log10(1000.0 / p)
    T_skewed = t_current + skew_factor * lp
    if -50 <= T_skewed <= 75:
        moist_points.append((float(T_skewed), float(lp)))
    t_current -= 4.0
chart.add("Moist Adiabat", moist_points, show_dots=False, stroke_style={"width": 3, "dasharray": "10,5"})

# Add ONE mixing ratio line (r=10 g/kg) - orange nearly vertical line
mr_points = []
mr = 10
for p in np.linspace(1000, 300, 15):
    lp = np.log10(1000.0 / p)
    e = mr * p / (622 + mr)
    if e > 0:
        td = (243.5 * np.log(e / 6.112)) / (17.67 - np.log(e / 6.112))
        td_skewed = td + skew_factor * lp
        if -50 <= td_skewed <= 75:
            mr_points.append((float(td_skewed), float(lp)))
chart.add("Mixing Ratio r=10g/kg", mr_points, show_dots=False, stroke_style={"width": 2, "dasharray": "4,6"})

# Add isotherms (0°C and -20°C) - gray diagonal lines showing the skew
for isotherm in [0, -20]:
    isotherm_points = []
    for lp in np.linspace(0, 1.0, 15):
        T_skewed = isotherm + skew_factor * lp
        if -50 <= T_skewed <= 75:
            isotherm_points.append((float(T_skewed), float(lp)))
    chart.add(f"{isotherm}°C Isotherm", isotherm_points, show_dots=False, stroke_style={"width": 2, "dasharray": "8,4"})

# Render to PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
