""" pyplots.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 86/100 | Created: 2026-01-17
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Skew-T transformation parameters
# The skew angle is 45 degrees, so for every 1 unit increase in log-p, temperature shifts
SKEW_SLOPE = 45  # degrees
SKEW_FACTOR = np.tan(np.radians(SKEW_SLOPE))  # ~1.0 for 45 degrees

# Pressure range (hPa) - log scale with surface at bottom
P_MIN = 100  # Top of diagram (stratosphere)
P_MAX = 1050  # Bottom of diagram (surface)
P_SURFACE = 1000  # Reference pressure

# Temperature range (°C) - extended to fill upper atmosphere better
T_MIN = -80
T_MAX = 50


# Skew-T transformation functions
def skew_transform(temp, pressure):
    """Transform temperature to skewed x-coordinate based on log pressure."""
    log_p = np.log10(pressure / P_SURFACE)  # Normalized log pressure
    return temp + SKEW_FACTOR * log_p * 40  # Scale factor for visual appearance


# Generate synthetic atmospheric sounding data
np.random.seed(42)

# Pressure levels (typical radiosonde) - extended to 100 hPa for full upper atmosphere coverage
pressure_levels = np.array(
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
        175,
        150,
        125,
        100,
    ]
)

# Temperature profile (realistic lapse rate with inversion)
# Surface ~25°C, standard lapse rate ~6.5°C/km, with tropopause around 200 hPa
base_temp = 25
temp_profile = []
for p in pressure_levels:
    altitude_km = 44.3308 * (1 - (p / 1013.25) ** 0.190284)  # Barometric formula approx
    if p > 200:  # Troposphere
        t = base_temp - 6.5 * altitude_km + np.random.normal(0, 1)
    else:  # Stratosphere (isothermal/warming)
        t = -55 + (200 - p) * 0.02 + np.random.normal(0, 0.5)
    temp_profile.append(t)
temp_profile = np.array(temp_profile)

# Dewpoint profile (always <= temperature, represents moisture)
# Higher moisture near surface, decreasing with altitude
dewpoint_profile = []
for p, t in zip(pressure_levels, temp_profile, strict=True):
    if p > 700:  # Lower atmosphere - more moist
        depression = 5 + np.random.uniform(0, 5)
    elif p > 400:  # Mid-levels - drier
        depression = 15 + np.random.uniform(0, 10)
    else:  # Upper levels - very dry
        depression = 30 + np.random.uniform(0, 15)
    dp = min(t - depression, t)
    dewpoint_profile.append(dp)
dewpoint_profile = np.array(dewpoint_profile)

# Create reference lines data

# 1. Temperature isotherms (skewed lines at 45 degrees)
isotherm_temps = np.arange(-100, 60, 10)  # Every 10°C - extended range
isotherm_data = []
for t_ref in isotherm_temps:
    p_range = np.array([P_MIN, P_MAX])
    x_skewed = skew_transform(np.array([t_ref, t_ref]), p_range)
    isotherm_data.append(
        {"x": x_skewed[0], "xend": x_skewed[1], "y": P_MIN, "yend": P_MAX, "temp": t_ref, "type": "isotherm"}
    )
isotherm_df = pd.DataFrame(isotherm_data)

# 2. Isobars (horizontal pressure lines)
isobar_pressures = [1000, 850, 700, 500, 300, 200, 100]
isobar_data = []
for p in isobar_pressures:
    x_left = skew_transform(T_MIN - 20, p)
    x_right = skew_transform(T_MAX + 20, p)
    isobar_data.append({"x": x_left, "xend": x_right, "y": p, "yend": p, "pressure": p, "type": "isobar"})
isobar_df = pd.DataFrame(isobar_data)

# 3. Dry adiabats (lines of constant potential temperature)
# These curve upward as air rises and cools adiabatically
dry_adiabat_data = []
theta_values = np.arange(-40, 100, 10)  # Potential temperatures - extended range
for theta in theta_values:
    points_x = []
    points_y = []
    for p in np.arange(P_MIN, P_MAX + 1, 25):
        # Poisson equation: T = theta * (p/1000)^(R/cp)
        # R/cp ≈ 0.286 for dry air
        t = (theta + 273.15) * (p / 1000) ** 0.286 - 273.15
        x = skew_transform(t, p)
        points_x.append(x)
        points_y.append(p)
    for i in range(len(points_x) - 1):
        dry_adiabat_data.append(
            {
                "x": points_x[i],
                "xend": points_x[i + 1],
                "y": points_y[i],
                "yend": points_y[i + 1],
                "theta": theta,
                "type": "dry_adiabat",
            }
        )
dry_adiabat_df = pd.DataFrame(dry_adiabat_data)

# 4. Moist adiabats (saturated adiabatic lapse rate)
moist_adiabat_data = []
moist_theta_values = np.arange(-30, 50, 10)  # Extended range
for theta_e in moist_theta_values:
    points_x = []
    points_y = []
    t_current = theta_e + 5  # Start warmer than dry
    for p in np.arange(P_MAX, P_MIN - 1, -25):
        x = skew_transform(t_current, p)
        points_x.append(x)
        points_y.append(p)
        # Approximate moist adiabatic lapse rate (varies with temperature)
        if t_current > 0:
            lapse = 5.5  # °C per pressure decrement (approx 500m)
        else:
            lapse = 6.0
        t_current -= lapse * 0.05  # Scale for pressure step
    for i in range(len(points_x) - 1):
        moist_adiabat_data.append(
            {
                "x": points_x[i],
                "xend": points_x[i + 1],
                "y": points_y[i],
                "yend": points_y[i + 1],
                "theta_e": theta_e,
                "type": "moist_adiabat",
            }
        )
moist_adiabat_df = pd.DataFrame(moist_adiabat_data)

# 5. Mixing ratio lines (lines of constant saturation mixing ratio)
mixing_ratio_data = []
mixing_ratios = [1, 2, 4, 7, 10, 15, 20]  # g/kg
for w in mixing_ratios:
    points_x = []
    points_y = []
    for p in np.arange(P_MIN + 50, P_MAX + 1, 25):
        # Approximate dewpoint from mixing ratio: Td ≈ (234.67 * ln(e)) / (17.67 - ln(e))
        # where e = w * p / (622 + w) in hPa
        e = w * p / (622 + w)
        if e > 0:
            td = (243.5 * np.log(e / 6.112)) / (17.67 - np.log(e / 6.112))
            if T_MIN - 20 < td < T_MAX + 20:
                x = skew_transform(td, p)
                points_x.append(x)
                points_y.append(p)
    if len(points_x) > 1:
        for i in range(len(points_x) - 1):
            mixing_ratio_data.append(
                {
                    "x": points_x[i],
                    "xend": points_x[i + 1],
                    "y": points_y[i],
                    "yend": points_y[i + 1],
                    "w": w,
                    "type": "mixing_ratio",
                }
            )
mixing_ratio_df = pd.DataFrame(mixing_ratio_data)

# Create profile data (temperature and dewpoint) using plotnine's aesthetic mapping
temp_skewed = skew_transform(temp_profile, pressure_levels)
dewpoint_skewed = skew_transform(dewpoint_profile, pressure_levels)

profile_df = pd.DataFrame(
    {
        "pressure": np.concatenate([pressure_levels, pressure_levels]),
        "x": np.concatenate([temp_skewed, dewpoint_skewed]),
        "variable": ["Temperature"] * len(pressure_levels) + ["Dewpoint"] * len(pressure_levels),
        "line_style": ["solid"] * len(pressure_levels) + ["dashed"] * len(pressure_levels),
    }
)

# Calculate axis limits
x_min = skew_transform(T_MIN - 10, P_MAX)
x_max = skew_transform(T_MAX + 10, P_MIN)

# Create dataframes for reference lines with line type for legend
# Use subset of lines for legend representation
isotherm_legend = isotherm_df.copy()
isotherm_legend["line_type"] = "Isotherms (10°C)"

dry_adiabat_legend = dry_adiabat_df.copy()
dry_adiabat_legend["line_type"] = "Dry Adiabats"

moist_adiabat_legend = moist_adiabat_df.copy()
moist_adiabat_legend["line_type"] = "Moist Adiabats"

mixing_ratio_legend = mixing_ratio_df.copy()
mixing_ratio_legend["line_type"] = "Mixing Ratios"

# Combine all reference lines for unified legend
all_ref_lines = pd.concat([isotherm_legend, dry_adiabat_legend, moist_adiabat_legend, mixing_ratio_legend])

# Y-axis (pressure) - use log-transformed values manually for proper tick display
pressure_breaks = [1000, 850, 700, 500, 400, 300, 200, 150, 100]
pressure_labels = [str(p) for p in pressure_breaks]

# Build the plot using plotnine's grammar of graphics with aesthetic mapping
plot = (
    ggplot(profile_df, aes(x="x", y="pressure"))
    # Reference lines - drawn first (background)
    # Isobars (horizontal pressure lines) - more visible dark gray with thicker line
    + geom_segment(
        aes(x="x", xend="xend", y="y", yend="yend"),
        data=isobar_df,
        color="#666666",
        size=1.0,
        linetype="solid",
        inherit_aes=False,
    )
    # Reference lines with color/linetype for legend - using plotnine's aesthetic mapping
    + geom_segment(
        aes(x="x", xend="xend", y="y", yend="yend", color="line_type", linetype="line_type"),
        data=all_ref_lines,
        size=0.9,
        inherit_aes=False,
    )
    # Temperature and dewpoint profiles using aesthetic mapping for color and linetype
    + geom_line(
        aes(x="x", y="pressure", color="variable", linetype="variable", group="variable"),
        data=profile_df,
        size=3.5,
        inherit_aes=False,
    )
    # Color scale combining reference lines and profiles
    + scale_color_manual(
        values={
            "Isotherms (10°C)": "#4A90D9",
            "Dry Adiabats": "#D2691E",
            "Moist Adiabats": "#228B22",
            "Mixing Ratios": "#8B008B",
            "Temperature": "#CC0000",
            "Dewpoint": "#0066CC",
        },
        name="Lines",
        breaks=["Temperature", "Dewpoint", "Isotherms (10°C)", "Dry Adiabats", "Moist Adiabats", "Mixing Ratios"],
    )
    + scale_linetype_manual(
        values={
            "Isotherms (10°C)": "solid",
            "Dry Adiabats": "dashed",
            "Moist Adiabats": "dotted",
            "Mixing Ratios": "dashdot",
            "Temperature": "solid",
            "Dewpoint": "dashed",
        },
        name="Lines",
        breaks=["Temperature", "Dewpoint", "Isotherms (10°C)", "Dry Adiabats", "Moist Adiabats", "Mixing Ratios"],
    )
    # Y-axis: log scale with explicit breaks and labels
    + scale_y_continuous(
        trans="log10",
        limits=(1100, 90),  # Inverted: surface at bottom, top at 90 hPa
        breaks=pressure_breaks,
        labels=pressure_labels,
    )
    # X-axis (skewed temperature coordinates - hide ticks but keep label)
    + scale_x_continuous(breaks=[], labels=[], limits=(x_min - 10, x_max + 20))
    # Annotations for profile lines - larger size for visibility in high-res image
    + annotate(
        "text",
        x=skew_transform(temp_profile[np.argmin(np.abs(pressure_levels - 600))], 600) + 8,
        y=600,
        label="T",
        color="#CC0000",
        size=22,
        fontweight="bold",
    )
    + annotate(
        "text",
        x=skew_transform(dewpoint_profile[np.argmin(np.abs(pressure_levels - 600))], 600) - 8,
        y=600,
        label="Td",
        color="#0066CC",
        size=22,
        fontweight="bold",
    )
    + labs(x="Temperature (°C, skewed 45°)", y="Pressure (hPa)", title="skewt-logp-atmospheric · plotnine · pyplots.ai")
    + theme(
        figure_size=(16, 16),  # Square for this specialized diagram
        plot_background=element_rect(fill="white"),
        panel_background=element_rect(fill="white"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color="#333333", size=1),
        text=element_text(size=14),
        axis_title=element_text(size=22),
        axis_title_x=element_text(margin={"t": 15}),
        axis_title_y=element_text(margin={"r": 15}),
        axis_text_x=element_blank(),  # Hide x-axis labels (skewed coords)
        axis_text_y=element_text(size=18, color="#333333"),  # Pressure labels
        plot_title=element_text(size=26, ha="center"),
        legend_position="right",
        legend_title=element_text(size=20, fontweight="bold"),
        legend_text=element_text(size=16),
        legend_background=element_rect(fill="white", alpha=0.95),
        legend_key_width=50,
        legend_key_height=20,
        axis_ticks_major_y=element_line(color="#333333", size=1),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
