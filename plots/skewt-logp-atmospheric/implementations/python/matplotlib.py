""" pyplots.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-17
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter


# Data - Simulated radiosonde sounding from surface to upper atmosphere
np.random.seed(42)

# Pressure levels (hPa) from surface to upper troposphere
pressure = np.array([1000, 950, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100])

# Temperature profile (°C) - typical mid-latitude sounding
temperature = np.array([25, 22, 19, 15, 12, 8, 5, 1, -3, -8, -14, -21, -28, -37, -45, -52, -56, -58, -56])

# Dewpoint profile (°C) - always <= temperature
dewpoint = np.array([18, 16, 14, 10, 6, 2, -2, -8, -15, -22, -28, -35, -42, -50, -55, -60, -65, -70, -75])

# Create figure
fig, ax = plt.subplots(figsize=(16, 12))

# Set up axes with log scale for pressure (inverted - 1000 hPa at bottom)
ax.set_yscale("log")
ax.set_ylim(1050, 100)
ax.set_xlim(-80, 50)

# Pressure axis formatting
ax.yaxis.set_major_formatter(ScalarFormatter())
ax.set_yticks([1000, 850, 700, 500, 400, 300, 250, 200, 150, 100])

# Pressure range for drawing reference lines
p_range = np.logspace(np.log10(1050), np.log10(100), 100)
p0 = 1000  # Reference pressure

# Draw isotherms (temperature lines) - skewed at 45°
for t in np.arange(-80, 60, 10):
    skew_factor = 45 * (np.log(p_range) - np.log(p0)) / (np.log(100) - np.log(p0))
    t_skewed = t + skew_factor
    ax.plot(t_skewed, p_range, color="#8B0000", alpha=0.3, linewidth=0.8)

# Draw dry adiabats (lines of constant potential temperature)
for theta in np.arange(-30, 150, 10):
    t_adiabat = (theta + 273.15) * (p_range / 1000) ** 0.286 - 273.15
    skew_factor = 45 * (np.log(p_range) - np.log(p0)) / (np.log(100) - np.log(p0))
    t_skewed = t_adiabat + skew_factor
    mask = (t_adiabat > -80) & (t_adiabat < 50)
    if np.any(mask):
        ax.plot(t_skewed[mask], p_range[mask], color="#228B22", alpha=0.3, linewidth=0.8, linestyle="--")

# Draw moist adiabats (simplified)
for theta_e in np.arange(0, 50, 4):
    t_dry = (theta_e + 273.15) * (p_range / 1000) ** 0.286 - 273.15
    moisture_factor = np.clip((t_dry + 30) / 60, 0, 1) * 0.5
    t_moist = t_dry * (1 - moisture_factor * (1 - (p_range / 1000) ** 0.2))
    skew_factor = 45 * (np.log(p_range) - np.log(p0)) / (np.log(100) - np.log(p0))
    t_skewed = t_moist + skew_factor
    mask = (t_moist > -80) & (t_moist < 50)
    if np.any(mask):
        ax.plot(t_skewed[mask], p_range[mask], color="#4169E1", alpha=0.25, linewidth=0.8, linestyle="-.")

# Draw mixing ratio lines
for w in [0.5, 1, 2, 4, 7, 10, 15, 20]:
    e = (w * p_range) / (622 + w)
    td = 243.5 * np.log(e / 6.112) / (17.67 - np.log(e / 6.112))
    skew_factor = 45 * (np.log(p_range) - np.log(p0)) / (np.log(100) - np.log(p0))
    td_skewed = td + skew_factor
    mask = (td > -80) & (td < 50) & (p_range >= 400)
    if np.any(mask):
        ax.plot(td_skewed[mask], p_range[mask], color="#9932CC", alpha=0.25, linewidth=0.8, linestyle=":")

# Apply skew transform to data
skew_factor_data = 45 * (np.log(pressure) - np.log(p0)) / (np.log(100) - np.log(p0))
temp_skewed = temperature + skew_factor_data
dewpoint_skewed = dewpoint + skew_factor_data

# Plot temperature profile (solid red line)
ax.plot(temp_skewed, pressure, color="#C41E3A", linewidth=3.5, solid_capstyle="round")
ax.scatter(temp_skewed, pressure, color="#C41E3A", s=80, zorder=5, edgecolor="white", linewidth=1.5)

# Plot dewpoint profile (dashed blue line)
ax.plot(dewpoint_skewed, pressure, color="#306998", linewidth=3.5, linestyle="--", dash_capstyle="round")
ax.scatter(dewpoint_skewed, pressure, color="#306998", s=80, zorder=5, edgecolor="white", linewidth=1.5)

# Labels and title
ax.set_xlabel("Temperature (°C)", fontsize=22)
ax.set_ylabel("Pressure (hPa)", fontsize=22)
ax.set_title("skewt-logp-atmospheric · matplotlib · pyplots.ai", fontsize=26, fontweight="bold", pad=20)
ax.tick_params(axis="both", labelsize=16)

# Legend
legend_elements = [
    Line2D([0], [0], color="#C41E3A", linewidth=3, label="Temperature"),
    Line2D([0], [0], color="#306998", linewidth=3, linestyle="--", label="Dewpoint"),
    Line2D([0], [0], color="#8B0000", linewidth=1, alpha=0.5, label="Isotherms"),
    Line2D([0], [0], color="#228B22", linewidth=1, alpha=0.5, linestyle="--", label="Dry Adiabats"),
    Line2D([0], [0], color="#4169E1", linewidth=1, alpha=0.5, linestyle="-.", label="Moist Adiabats"),
    Line2D([0], [0], color="#9932CC", linewidth=1, alpha=0.5, linestyle=":", label="Mixing Ratio"),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=14, framealpha=0.95)

# Grid and isobars
ax.grid(True, alpha=0.3, linestyle="-", color="gray")
for p in [850, 700, 500, 300, 200]:
    ax.axhline(y=p, color="gray", alpha=0.3, linewidth=0.5)

# Pressure level annotations
for p, label in [(1000, "1000"), (850, "850"), (700, "700"), (500, "500"), (300, "300"), (200, "200")]:
    ax.annotate(f"{label} hPa", xy=(-78, p), fontsize=12, color="gray", va="center")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
