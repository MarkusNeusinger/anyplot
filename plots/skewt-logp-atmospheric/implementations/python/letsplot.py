""" pyplots.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-17
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_y_log10,
    scale_y_reverse,
    theme,
)


LetsPlot.setup_html()

# Atmospheric sounding data (synthetic radiosonde profile)
np.random.seed(42)

# Pressure levels from surface to upper troposphere (hPa)
pressure = np.array([1000, 950, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100])

# Temperature profile (°C) - typical mid-latitude sounding
# Decreasing with height, with a tropopause around 200 hPa
temperature = np.array([25, 22, 18, 14, 10, 6, 2, -3, -8, -14, -21, -29, -38, -47, -55, -58, -56, -55, -56])

# Dewpoint profile (°C) - typically lower than temperature
# Shows moisture decreasing with height
dewpoint = np.array([18, 16, 12, 8, 4, 0, -5, -12, -20, -28, -35, -42, -50, -58, -65, -70, -72, -75, -78])

# For Skew-T: we need to skew the temperature by adding an offset based on pressure
# The skew factor converts the diagram coordinates
# In a Skew-T, x_plot = T + skew_factor * log(p0/p)
p0 = 1000  # Reference pressure
skew_factor = 40  # Degrees of skew per pressure decade

# Calculate skewed coordinates for plotting
log_pressure = np.log10(p0 / pressure)
temp_skewed = temperature + skew_factor * log_pressure
dewpoint_skewed = dewpoint + skew_factor * log_pressure

# Create DataFrame for main profiles with type for legend
df_temp = pd.DataFrame({"pressure": pressure, "value": temp_skewed, "type": "Temperature"})

df_dewpoint = pd.DataFrame({"pressure": pressure, "value": dewpoint_skewed, "type": "Dewpoint"})

# Generate isotherms (temperature reference lines, skewed 45 degrees)
isotherm_temps = np.arange(-80, 50, 10)  # °C
isotherm_data = []
p_range = np.array([1000, 100])
for t in isotherm_temps:
    log_p_vals = np.log10(p0 / p_range)
    t_skewed = t + skew_factor * log_p_vals
    isotherm_data.append(
        {"x_start": t_skewed[0], "x_end": t_skewed[1], "y_start": p_range[0], "y_end": p_range[1], "temp": t}
    )
df_isotherms = pd.DataFrame(isotherm_data)

# Generate dry adiabats (lines of constant potential temperature)
# theta = T * (p0/p)^(R/cp) where R/cp ≈ 0.286
dry_adiabat_thetas = np.arange(250, 450, 20)  # K
dry_adiabat_data = []
p_levels = np.linspace(1000, 100, 50)
for theta in dry_adiabat_thetas:
    temps = (theta * (p_levels / p0) ** 0.286) - 273.15  # Convert to Celsius
    log_p_vals = np.log10(p0 / p_levels)
    temps_skewed = temps + skew_factor * log_p_vals
    for i in range(len(p_levels)):
        dry_adiabat_data.append(
            {"pressure": p_levels[i], "temp_skewed": temps_skewed[i], "theta": theta, "line_type": "Dry Adiabat"}
        )
df_dry_adiabats = pd.DataFrame(dry_adiabat_data)

# Generate moist adiabats (equivalent potential temperature lines)
# Moist adiabats follow a different curve - steeper at low levels, flatter aloft
# theta_e is conserved along moist adiabats
moist_adiabat_theta_e = np.arange(280, 360, 10)  # K
moist_adiabat_data = []
for theta_e in moist_adiabat_theta_e:
    # Approximate moist adiabat using simplified formula
    # At surface, T ≈ theta_e - 273.15, then follows moist lapse rate (~6.5°C/km)
    t_surface = theta_e - 273.15
    for p in p_levels:
        # Moist adiabatic lapse rate is variable, roughly 6.5 C/km
        # Use pseudo-adiabatic approximation
        height_factor = np.log(p0 / p) * 2.5  # Scale factor for height
        t_moist = t_surface - 6.5 * height_factor * 0.8  # Moist lapse rate effect
        log_p_val = np.log10(p0 / p)
        t_skewed = t_moist + skew_factor * log_p_val
        moist_adiabat_data.append(
            {"pressure": p, "temp_skewed": t_skewed, "theta_e": theta_e, "line_type": "Moist Adiabat"}
        )
df_moist_adiabats = pd.DataFrame(moist_adiabat_data)

# Generate mixing ratio lines (lines of constant water vapor mixing ratio)
# Simplified: ws = 622 * es(T) / (p - es(T)) where es is saturation vapor pressure
mixing_ratios = [1, 2, 4, 7, 10, 15, 20]  # g/kg
mixing_data = []
for ws in mixing_ratios:
    for p in p_levels[::5]:  # Sample every 5th pressure level for smooth lines
        # Approximate temperature for given mixing ratio and pressure
        # Using simplified formula: T ≈ 35 * log(ws * p / 622) - 20
        t = 35 * np.log10(ws * p / 622) - 20
        log_p_val = np.log10(p0 / p)
        t_skewed = t + skew_factor * log_p_val
        mixing_data.append({"pressure": p, "temp_skewed": t_skewed, "ws": ws, "line_type": "Mixing Ratio"})
df_mixing = pd.DataFrame(mixing_data)

# Build the plot using lets-plot
plot = (
    ggplot()
    # Isotherms (skewed temperature lines) - light gray
    + geom_segment(
        aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        data=df_isotherms,
        color="#999999",
        size=0.6,
        alpha=0.8,
    )
    # Dry adiabats - orange dashed (increased visibility)
    + geom_path(
        aes(x="temp_skewed", y="pressure", group="theta"),
        data=df_dry_adiabats,
        color="#D97706",
        size=0.8,
        alpha=0.7,
        linetype="dashed",
    )
    # Moist adiabats - purple dash-dot
    + geom_path(
        aes(x="temp_skewed", y="pressure", group="theta_e"),
        data=df_moist_adiabats,
        color="#7C3AED",
        size=0.8,
        alpha=0.7,
        linetype="dotdash",
    )
    # Mixing ratio lines - green dotted (increased visibility)
    + geom_path(
        aes(x="temp_skewed", y="pressure", group="ws"),
        data=df_mixing,
        color="#059669",
        size=0.8,
        alpha=0.7,
        linetype="dotted",
    )
    # Temperature profile - solid red line
    + geom_path(aes(x="value", y="pressure"), data=df_temp, color="#DC2626", size=2.5)
    # Dewpoint profile - dashed blue line
    + geom_path(aes(x="value", y="pressure"), data=df_dewpoint, color="#2563EB", size=2.5, linetype="dashed")
    # Points on profiles for clarity
    + geom_point(aes(x="value", y="pressure"), data=df_temp, color="#DC2626", size=4)
    + geom_point(aes(x="value", y="pressure"), data=df_dewpoint, color="#2563EB", size=4)
    # Reverse y-axis (pressure decreases upward) and log scale
    + scale_y_log10()
    + scale_y_reverse(limits=[1000, 100])
    # Labels and title
    + labs(x="Temperature (°C) - Skewed", y="Pressure (hPa)", title="skewt-logp-atmospheric · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_blank(),
        axis_line=element_blank(),
    )
)

# Create legend using actual line segments with matching styles
# Position legend in upper right area
legend_x_start = 95
legend_x_end = 115
legend_text_x = 118

# Legend items with their properties matching the actual plot lines
legend_entries = [
    {"label": "Temp", "color": "#DC2626", "linetype": "solid", "size": 2.5, "y": 125},
    {"label": "Dewpt", "color": "#2563EB", "linetype": "dashed", "size": 2.5, "y": 140},
    {"label": "Dry Ad.", "color": "#D97706", "linetype": "dashed", "size": 0.8, "y": 158},
    {"label": "Moist Ad.", "color": "#7C3AED", "linetype": "dotdash", "size": 0.8, "y": 178},
    {"label": "Mix. Ratio", "color": "#059669", "linetype": "dotted", "size": 0.8, "y": 200},
]

# Add legend line segments with actual linetypes
for entry in legend_entries:
    plot = plot + geom_segment(
        aes(x="x_start", xend="x_end", y="y", yend="y"),
        data=pd.DataFrame([{"x_start": legend_x_start, "x_end": legend_x_end, "y": entry["y"]}]),
        color=entry["color"],
        size=entry["size"],
        linetype=entry["linetype"],
    )
    plot = plot + geom_text(x=legend_text_x, y=entry["y"], label=entry["label"], color="#333333", size=12, hjust=0)

# Save the plot
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
