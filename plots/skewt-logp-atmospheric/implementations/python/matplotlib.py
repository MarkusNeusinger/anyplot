""" anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito — data series
TEMP_COLOR = "#009E73"  # temperature — position 1
DEWPOINT_COLOR = "#D55E00"  # dewpoint — position 2

# Data — simulated mid-latitude radiosonde sounding (surface to upper troposphere)
np.random.seed(42)
pressure = np.array([1000, 950, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100])
temperature = np.array([25, 22, 19, 15, 12, 8, 5, 1, -3, -8, -14, -21, -28, -37, -45, -52, -56, -58, -56])
dewpoint = np.array([18, 16, 14, 10, 6, 2, -2, -8, -15, -22, -28, -35, -42, -50, -55, -60, -65, -70, -75])

# Plot — square canvas for symmetric atmospheric profile
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.set_yscale("log")
ax.set_ylim(1050, 100)
ax.set_xlim(-80, 50)

ax.yaxis.set_major_formatter(ScalarFormatter())
ax.set_yticks([1000, 850, 700, 500, 400, 300, 250, 200, 150, 100])

# Precompute skew offsets (45-degree skew of temperature axis)
p0 = 1000
p_range = np.logspace(np.log10(1050), np.log10(100), 100)
skew_ref = 45 * (np.log(p_range) - np.log(p0)) / (np.log(100) - np.log(p0))
skew_data = 45 * (np.log(pressure) - np.log(p0)) / (np.log(100) - np.log(p0))

# Reference lines — kept very subtle to reduce background clutter
# Isotherms (lines of constant temperature, skewed 45°)
for t in np.arange(-80, 60, 10):
    ax.plot(t + skew_ref, p_range, color="#8B4513", alpha=0.10, linewidth=0.5)

# Dry adiabats (lines of constant potential temperature)
for theta in np.arange(-30, 150, 10):
    t_dry = (theta + 273.15) * (p_range / 1000) ** 0.286 - 273.15
    mask = (t_dry > -80) & (t_dry < 50)
    if np.any(mask):
        ax.plot(t_dry[mask] + skew_ref[mask], p_range[mask], color="#228B22", alpha=0.13, linewidth=0.5, linestyle="--")

# Moist adiabats (simplified saturated-adiabatic lapse rate)
for theta_e in np.arange(0, 50, 4):
    t_dry = (theta_e + 273.15) * (p_range / 1000) ** 0.286 - 273.15
    moisture_factor = np.clip((t_dry + 30) / 60, 0, 1) * 0.5
    t_moist = t_dry * (1 - moisture_factor * (1 - (p_range / 1000) ** 0.2))
    mask = (t_moist > -80) & (t_moist < 50)
    if np.any(mask):
        ax.plot(
            t_moist[mask] + skew_ref[mask], p_range[mask], color="#4169E1", alpha=0.11, linewidth=0.5, linestyle="-."
        )

# Mixing ratio lines (constant water vapor mixing ratio)
for w in [0.5, 1, 2, 4, 7, 10, 15, 20]:
    e = (w * p_range) / (622 + w)
    td = 243.5 * np.log(e / 6.112) / (17.67 - np.log(e / 6.112))
    mask = (td > -80) & (td < 50) & (p_range >= 400)
    if np.any(mask):
        ax.plot(td[mask] + skew_ref[mask], p_range[mask], color="#9932CC", alpha=0.13, linewidth=0.5, linestyle=":")

# Data profiles
temp_skewed = temperature + skew_data
dewpoint_skewed = dewpoint + skew_data

ax.plot(temp_skewed, pressure, color=TEMP_COLOR, linewidth=2.5, solid_capstyle="round", zorder=4)
ax.scatter(temp_skewed, pressure, color=TEMP_COLOR, s=60, zorder=5, edgecolors=PAGE_BG, linewidth=0.8)

ax.plot(dewpoint_skewed, pressure, color=DEWPOINT_COLOR, linewidth=2.5, linestyle="--", dash_capstyle="round", zorder=4)
ax.scatter(dewpoint_skewed, pressure, color=DEWPOINT_COLOR, s=60, zorder=5, edgecolors=PAGE_BG, linewidth=0.8)

# Style
ax.set_xlabel("Temperature (°C)", fontsize=10, color=INK)
ax.set_ylabel("Pressure (hPa)", fontsize=10, color=INK)
ax.set_title(
    "skewt-logp-atmospheric · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10
)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.12, linewidth=0.5, color=INK)
ax.xaxis.grid(True, alpha=0.08, linewidth=0.5, color=INK)

# Legend
legend_elements = [
    Line2D([0], [0], color=TEMP_COLOR, linewidth=2, label="Temperature"),
    Line2D([0], [0], color=DEWPOINT_COLOR, linewidth=2, linestyle="--", label="Dewpoint"),
    Line2D([0], [0], color="#8B4513", linewidth=0.8, alpha=0.6, label="Isotherms"),
    Line2D([0], [0], color="#228B22", linewidth=0.8, alpha=0.6, linestyle="--", label="Dry Adiabats"),
    Line2D([0], [0], color="#4169E1", linewidth=0.8, alpha=0.6, linestyle="-.", label="Moist Adiabats"),
    Line2D([0], [0], color="#9932CC", linewidth=0.8, alpha=0.6, linestyle=":", label="Mixing Ratio"),
]
leg = ax.legend(handles=legend_elements, loc="upper right", fontsize=8, framealpha=0.9)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.13, right=0.97, top=0.93, bottom=0.10)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
