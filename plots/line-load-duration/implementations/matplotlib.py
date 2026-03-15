""" pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-15
"""

import matplotlib.pyplot as plt
import numpy as np


# Data
np.random.seed(42)
hours = 8760

base_load = 400
peak_load = 1200
mid_load = (base_load + peak_load) / 2

hourly_load = np.concatenate(
    [
        np.random.normal(1100, 60, int(hours * 0.05)),
        np.random.normal(900, 80, int(hours * 0.15)),
        np.random.normal(750, 70, int(hours * 0.30)),
        np.random.normal(600, 50, int(hours * 0.30)),
        np.random.normal(480, 30, int(hours * 0.20)),
    ]
)
hourly_load = np.clip(hourly_load, base_load, peak_load)
extra = hours - len(hourly_load)
if extra > 0:
    hourly_load = np.concatenate([hourly_load, np.random.normal(500, 40, extra)])
hourly_load = hourly_load[:hours]
load_mw = np.sort(hourly_load)[::-1]
hour = np.arange(hours)

peak_threshold = 950
intermediate_threshold = 600

peak_end = np.searchsorted(-load_mw, -peak_threshold)
base_start = np.searchsorted(-load_mw, -intermediate_threshold)

total_energy_gwh = np.trapezoid(load_mw, hour) / 1000

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

ax.fill_between(hour[: peak_end + 1], load_mw[: peak_end + 1], color="#E8634A", alpha=0.35, label="Peak Load")
ax.fill_between(
    hour[peak_end : base_start + 1],
    load_mw[peak_end : base_start + 1],
    intermediate_threshold,
    color="#F0A030",
    alpha=0.35,
    label="Intermediate Load",
)
ax.fill_between(hour[peak_end : base_start + 1], intermediate_threshold, color="#306998", alpha=0.25)
ax.fill_between(hour[: peak_end + 1], min(load_mw[peak_end], intermediate_threshold), color="#306998", alpha=0.25)
ax.fill_between(hour[base_start:], load_mw[base_start:], color="#306998", alpha=0.35, label="Base Load")

ax.plot(hour, load_mw, color="#1a1a2e", linewidth=2.5, zorder=5)

# Capacity tier lines
ax.axhline(y=peak_threshold, color="#E8634A", linestyle="--", linewidth=1.5, alpha=0.7)
ax.text(
    hours * 0.02,
    peak_threshold + 15,
    f"Peak Capacity ({peak_threshold} MW)",
    fontsize=14,
    color="#E8634A",
    fontweight="medium",
)

ax.axhline(y=intermediate_threshold, color="#F0A030", linestyle="--", linewidth=1.5, alpha=0.7)
ax.text(
    hours * 0.02,
    intermediate_threshold + 15,
    f"Intermediate Capacity ({intermediate_threshold} MW)",
    fontsize=14,
    color="#F0A030",
    fontweight="medium",
)

ax.axhline(y=base_load, color="#306998", linestyle="--", linewidth=1.5, alpha=0.7)
ax.text(
    hours * 0.02, base_load + 15, f"Base Capacity ({base_load} MW)", fontsize=14, color="#306998", fontweight="medium"
)

# Region labels
ax.text(
    peak_end * 0.4, peak_threshold + 60, "PEAK", fontsize=16, fontweight="bold", color="#E8634A", ha="center", alpha=0.8
)
ax.text(
    (peak_end + base_start) / 2,
    (peak_threshold + intermediate_threshold) / 2 + 20,
    "INTERMEDIATE",
    fontsize=16,
    fontweight="bold",
    color="#c07800",
    ha="center",
    alpha=0.8,
)
ax.text(
    (base_start + hours) / 2,
    (intermediate_threshold + base_load) / 2,
    "BASE",
    fontsize=16,
    fontweight="bold",
    color="#306998",
    ha="center",
    alpha=0.8,
)

# Energy annotation
ax.text(
    hours * 0.72,
    peak_threshold + 40,
    f"Total Energy: {total_energy_gwh:,.0f} GWh/year",
    fontsize=16,
    fontweight="bold",
    color="#1a1a2e",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

# Style
ax.set_xlabel("Hours of Year (ranked by load)", fontsize=20)
ax.set_ylabel("Power Demand (MW)", fontsize=20)
ax.set_title("line-load-duration · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, hours)
ax.set_ylim(base_load - 30, peak_load + 30)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.legend(fontsize=16, loc="upper right", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
