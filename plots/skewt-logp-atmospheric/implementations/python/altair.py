""" pyplots.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: altair 6.0.0 | Python 3.13.11
Quality: 72/100 | Created: 2026-01-17
"""

import altair as alt
import numpy as np
import pandas as pd


# Generate realistic atmospheric sounding data
np.random.seed(42)

# Pressure levels (hPa) - surface to upper troposphere
pressure = np.array([1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100])

# Temperature profile (°C) - typical mid-latitude sounding
# Decreases with altitude, with a tropopause around 200-300 hPa
temperature = np.array([25, 20, 15, 5, -15, -28, -45, -52, -55, -55, -55])

# Dewpoint profile (°C) - always less than or equal to temperature
dewpoint = np.array([18, 15, 10, -5, -25, -38, -55, -62, -70, -75, -80])

# Create main data DataFrame
sounding_data = pd.DataFrame(
    {"pressure": pressure, "temperature": temperature, "dewpoint": dewpoint, "log_pressure": np.log10(pressure)}
)

# For Skew-T, we need to skew the temperature axis
# Skewed temperature = T + (log10(1000) - log10(P)) * skew_factor
skew_factor = 40  # Controls the skew angle
sounding_data["temp_skewed"] = (
    sounding_data["temperature"] + (np.log10(1000) - sounding_data["log_pressure"]) * skew_factor
)
sounding_data["dewpoint_skewed"] = (
    sounding_data["dewpoint"] + (np.log10(1000) - sounding_data["log_pressure"]) * skew_factor
)

# Create combined profile data for legend (long format)
profile_legend_data = pd.DataFrame({"profile": ["Temperature", "Dewpoint"], "color": ["#DC143C", "#306998"]})

# Create isotherms (constant temperature lines, skewed)
isotherm_temps = np.arange(-80, 50, 10)  # Temperature range
isotherm_data = []
for t in isotherm_temps:
    for p in np.linspace(100, 1000, 50):
        log_p = np.log10(p)
        t_skewed = t + (np.log10(1000) - log_p) * skew_factor
        isotherm_data.append({"pressure": p, "temp_skewed": t_skewed, "isotherm": t, "log_pressure": log_p})
isotherm_df = pd.DataFrame(isotherm_data)

# Create dry adiabats (lines of constant potential temperature)
# Potential temperature theta = T * (1000/P)^0.286
theta_values = np.arange(250, 450, 20)  # Potential temperatures in Kelvin
dry_adiabat_data = []
for theta in theta_values:
    for p in np.linspace(100, 1000, 50):
        # T = theta * (P/1000)^0.286
        temp_k = theta * (p / 1000) ** 0.286
        temp_c = temp_k - 273.15
        log_p = np.log10(p)
        t_skewed = temp_c + (np.log10(1000) - log_p) * skew_factor
        dry_adiabat_data.append({"pressure": p, "temp_skewed": t_skewed, "theta": theta, "log_pressure": log_p})
dry_adiabat_df = pd.DataFrame(dry_adiabat_data)

# Create moist adiabats (lines of constant equivalent potential temperature)
# Moist adiabats curve more steeply than dry adiabats
theta_e_values = np.arange(280, 380, 20)  # Equivalent potential temperatures in Kelvin
moist_adiabat_data = []
for theta_e in theta_e_values:
    for p in np.linspace(100, 1000, 50):
        # Simplified moist adiabatic lapse rate approximation
        # Temperature decreases more slowly with height for moist air
        temp_k = theta_e * (p / 1000) ** 0.23  # Lower exponent for moist adiabat
        temp_c = temp_k - 273.15
        log_p = np.log10(p)
        t_skewed = temp_c + (np.log10(1000) - log_p) * skew_factor
        moist_adiabat_data.append({"pressure": p, "temp_skewed": t_skewed, "theta_e": theta_e, "log_pressure": log_p})
moist_adiabat_df = pd.DataFrame(moist_adiabat_data)

# Create mixing ratio lines (lines of constant mixing ratio)
# Simplified: mixing ratio relates to dewpoint and pressure
mixing_ratios = [1, 2, 4, 7, 10, 15, 20]  # g/kg
mixing_ratio_data = []
for w in mixing_ratios:
    for p in np.linspace(400, 1000, 30):
        # Approximate saturation vapor pressure from mixing ratio
        # e = (w * p) / (622 + w)
        e = (w * p) / (622 + w)
        # Convert to dewpoint using simplified formula
        # Td ≈ (243.5 * ln(e/6.112)) / (17.67 - ln(e/6.112))
        if e > 0.1:
            ln_e = np.log(e / 6.112)
            td = (243.5 * ln_e) / (17.67 - ln_e) if (17.67 - ln_e) != 0 else -40
            log_p = np.log10(p)
            t_skewed = td + (np.log10(1000) - log_p) * skew_factor
            if -100 < td < 50:  # Filter reasonable values
                mixing_ratio_data.append(
                    {"pressure": p, "temp_skewed": t_skewed, "mixing_ratio": w, "log_pressure": log_p}
                )
mixing_ratio_df = pd.DataFrame(mixing_ratio_data)

# X-axis domain - tight fit to actual data range with small margin
# Temperature skewed values range roughly from -40 to 65 based on data
x_domain = [-50, 70]
y_axis = alt.Y("pressure:Q", scale=alt.Scale(type="log", domain=[1000, 100]), title="Pressure (hPa)")

# Isotherms - skewed temperature lines (gray, dashed, increased opacity)
isotherms = (
    alt.Chart(isotherm_df)
    .mark_line(strokeDash=[4, 4], strokeWidth=1.2, opacity=0.6)
    .encode(
        x=alt.X("temp_skewed:Q", title="Temperature (°C, skewed)", scale=alt.Scale(domain=x_domain)),
        y=y_axis,
        detail="isotherm:N",
        color=alt.value("#888888"),
    )
)

# Dry adiabats (green lines, increased opacity)
dry_adiabats = (
    alt.Chart(dry_adiabat_df)
    .mark_line(strokeWidth=1.2, opacity=0.65)
    .encode(
        x=alt.X("temp_skewed:Q", scale=alt.Scale(domain=x_domain)),
        y=y_axis,
        detail="theta:N",
        color=alt.value("#228B22"),
    )
)

# Moist adiabats (purple/magenta dashed lines)
moist_adiabats = (
    alt.Chart(moist_adiabat_df)
    .mark_line(strokeDash=[6, 3], strokeWidth=1.2, opacity=0.65)
    .encode(
        x=alt.X("temp_skewed:Q", scale=alt.Scale(domain=x_domain)),
        y=y_axis,
        detail="theta_e:N",
        color=alt.value("#9932CC"),
    )
)

# Mixing ratio lines (blue, dashed, increased opacity)
mixing_lines = (
    alt.Chart(mixing_ratio_df)
    .mark_line(strokeDash=[2, 2], strokeWidth=1.2, opacity=0.65)
    .encode(
        x=alt.X("temp_skewed:Q", scale=alt.Scale(domain=x_domain)),
        y=y_axis,
        detail="mixing_ratio:N",
        color=alt.value("#4169E1"),
    )
)

# Temperature profile (solid red line)
temp_profile = (
    alt.Chart(sounding_data)
    .mark_line(strokeWidth=4, color="#DC143C")
    .encode(
        x=alt.X("temp_skewed:Q", scale=alt.Scale(domain=x_domain)), y=y_axis, tooltip=["pressure:Q", "temperature:Q"]
    )
)

# Temperature profile points
temp_points = (
    alt.Chart(sounding_data)
    .mark_circle(size=120, color="#DC143C")
    .encode(
        x=alt.X("temp_skewed:Q", scale=alt.Scale(domain=x_domain)), y=y_axis, tooltip=["pressure:Q", "temperature:Q"]
    )
)

# Dewpoint profile (dashed blue line)
dewpoint_profile = (
    alt.Chart(sounding_data)
    .mark_line(strokeWidth=4, strokeDash=[8, 4], color="#306998")
    .encode(
        x=alt.X("dewpoint_skewed:Q", scale=alt.Scale(domain=x_domain)), y=y_axis, tooltip=["pressure:Q", "dewpoint:Q"]
    )
)

# Dewpoint profile points
dewpoint_points = (
    alt.Chart(sounding_data)
    .mark_circle(size=120, color="#306998")
    .encode(
        x=alt.X("dewpoint_skewed:Q", scale=alt.Scale(domain=x_domain)), y=y_axis, tooltip=["pressure:Q", "dewpoint:Q"]
    )
)

# Create legend data for visible points that will generate the legend
legend_df = pd.DataFrame(
    {
        "x": [-45, -45, -45, -45, -45, -45],
        "y": [980, 900, 820, 740, 660, 580],
        "element": ["Temperature", "Dewpoint", "Isotherm", "Dry Adiabat", "Moist Adiabat", "Mixing Ratio"],
    }
)

# Use mark_point to create visible legend entries - points placed outside visible area but within domain
combined_legend = (
    alt.Chart(legend_df)
    .mark_point(size=150, filled=True)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=x_domain)),
        y=alt.Y("y:Q", scale=alt.Scale(type="log", domain=[1000, 100])),
        color=alt.Color(
            "element:N",
            scale=alt.Scale(
                domain=["Temperature", "Dewpoint", "Isotherm", "Dry Adiabat", "Moist Adiabat", "Mixing Ratio"],
                range=["#DC143C", "#306998", "#888888", "#228B22", "#9932CC", "#4169E1"],
            ),
            legend=alt.Legend(
                title="Legend",
                orient="right",
                titleFontSize=16,
                labelFontSize=14,
                symbolSize=300,
                symbolStrokeWidth=3,
                offset=10,
            ),
        ),
    )
)

# Combine all layers including legend
chart = (
    alt.layer(
        isotherms,
        dry_adiabats,
        moist_adiabats,
        mixing_lines,
        temp_profile,
        temp_points,
        dewpoint_profile,
        dewpoint_points,
        combined_legend,
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title("skewt-logp-atmospheric · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridColor="#EEEEEE")
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=16, labelFontSize=14, padding=10, cornerRadius=5)
    .interactive()
)

# Save output
chart.save("plot.png", scale_factor=3.0)
