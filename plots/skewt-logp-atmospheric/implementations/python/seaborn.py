""" pyplots.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-17
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import ScalarFormatter


# Set seaborn style with whitegrid for subtle grid lines, using talk context for better scaling
sns.set_theme(style="whitegrid", context="talk", font_scale=1.1)
sns.set_palette("colorblind")

# Synthetic atmospheric sounding data (typical mid-latitude summer profile)
np.random.seed(42)
pressure = np.array([1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100])
temperature = np.array([25, 18, 12, 2, -20, -35, -50, -55, -58, -60, -55])
dewpoint = np.array([18, 14, 8, -5, -30, -45, -60, -65, -68, -70, -65])

# Create figure with custom transform for skew-T
fig, ax = plt.subplots(figsize=(16, 9))

# Set up the axes with log scale for pressure (inverted)
ax.set_yscale("log")
ax.set_ylim(1050, 100)  # Inverted: surface at bottom
ax.set_xlim(-50, 50)

# Custom skew transform (45 degrees)
skew_angle = 45
skew_slope = np.tan(np.radians(skew_angle))

# Draw isotherms (temperature lines, skewed)
isotherm_temps = np.arange(-80, 60, 10)
p_range = np.logspace(np.log10(100), np.log10(1050), 100)
for t in isotherm_temps:
    x_iso = t + skew_slope * (np.log(1000 / p_range))
    ax.plot(x_iso, p_range, color="#cccccc", linewidth=0.8, alpha=0.7, zorder=1)

# Draw isobars (horizontal pressure lines)
isobar_levels = [1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100]
for p in isobar_levels:
    ax.axhline(y=p, color="#dddddd", linewidth=0.8, alpha=0.7, zorder=1)

# Draw dry adiabats (potential temperature lines)
theta_values = np.arange(250, 450, 20)  # Potential temperatures in K
for theta in theta_values:
    p_adiabat = np.logspace(np.log10(100), np.log10(1050), 100)
    # T = theta * (p/1000)^(R/cp), where R/cp ≈ 0.286
    t_adiabat = theta * (p_adiabat / 1000) ** 0.286 - 273.15
    x_adiabat = t_adiabat + skew_slope * (np.log(1000 / p_adiabat))
    ax.plot(x_adiabat, p_adiabat, color="#8B4513", linewidth=0.6, alpha=0.5, zorder=1)

# Draw moist adiabats (saturated adiabats - simplified)
theta_e_values = np.arange(270, 370, 20)  # Equivalent potential temperatures
for theta_e in theta_e_values:
    p_moist = np.logspace(np.log10(100), np.log10(1050), 100)
    # Simplified moist adiabat approximation
    t_moist = (theta_e - 30) * (p_moist / 1000) ** 0.3 - 273.15
    x_moist = t_moist + skew_slope * (np.log(1000 / p_moist))
    ax.plot(x_moist, p_moist, color="#228B22", linewidth=0.6, alpha=0.4, linestyle="--", zorder=1)

# Draw mixing ratio lines (constant water vapor mixing ratio)
mixing_ratios = [1, 2, 4, 7, 10, 15, 20]  # g/kg
for w in mixing_ratios:
    p_mix = np.logspace(np.log10(400), np.log10(1050), 50)
    # Simplified mixing ratio to dewpoint: Td ≈ 35 * log10(w) - 15 + adjustment for pressure
    t_mix = 35 * np.log10(w) - 20 + 5 * np.log10(p_mix / 1000)
    x_mix = t_mix + skew_slope * (np.log(1000 / p_mix))
    ax.plot(x_mix, p_mix, color="#4169E1", linewidth=0.5, alpha=0.4, linestyle=":", zorder=1)

# Apply skew transform to data for seaborn plotting
x_temp = temperature + skew_slope * np.log(1000 / pressure)
x_dew = dewpoint + skew_slope * np.log(1000 / pressure)

# Create DataFrame for seaborn plotting
df = pd.DataFrame(
    {
        "x": np.concatenate([x_temp, x_dew]),
        "pressure": np.concatenate([pressure, pressure]),
        "profile": ["Temperature"] * len(pressure) + ["Dewpoint"] * len(pressure),
    }
)

# Plot profiles using seaborn lineplot
sns.lineplot(
    data=df,
    x="x",
    y="pressure",
    hue="profile",
    style="profile",
    markers={"Temperature": "o", "Dewpoint": "s"},
    dashes={"Temperature": "", "Dewpoint": (5, 2)},
    palette={"Temperature": "#E74C3C", "Dewpoint": "#306998"},
    linewidth=4,
    markersize=10,
    ax=ax,
    zorder=5,
    legend=True,
)

# Configure pressure axis - remove overlapping ticks (925 removed to avoid overlap with 1000)
ax.yaxis.set_major_formatter(ScalarFormatter())
display_ticks = [1000, 850, 700, 500, 400, 300, 250, 200, 150, 100]
ax.set_yticks(display_ticks)
ax.set_yticklabels([str(p) for p in display_ticks])

# Labels and title with proper middle dot separator
ax.set_xlabel("Temperature (°C)", fontsize=20)
ax.set_ylabel("Pressure (hPa)", fontsize=20)
ax.set_title("skewt-logp-atmospheric · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Use seaborn's despine to clean up the appearance (keep left and bottom spines only)
sns.despine(ax=ax, top=True, right=True)

# Configure legend from seaborn lineplot
legend = ax.get_legend()
legend.set_title("")
for text in legend.get_texts():
    text.set_fontsize(16)
legend.get_frame().set_alpha(0.9)

# Add reference line labels with better positioning and improved visibility
ax.text(45, 600, "Isotherms", fontsize=14, color="#555555", rotation=45, ha="center", fontweight="bold")
ax.text(-25, 108, "Dry Adiabats", fontsize=13, color="#6B3510", ha="center", fontweight="bold")
ax.text(0, 108, "Moist Adiabats", fontsize=13, color="#1A6B1A", ha="center", fontweight="bold")
ax.text(22, 108, "Mixing Ratio", fontsize=13, color="#2E4A8B", ha="center", fontweight="bold")

# Add subtle background and configure grid styling
ax.set_facecolor("#fafafa")
ax.grid(True, which="major", alpha=0.3, linestyle="-", linewidth=0.5, color="#888888")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
