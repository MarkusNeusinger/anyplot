""" pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-15
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data
np.random.seed(42)
hours_in_year = 8760

base_load = 400
peak_load = 1200
t = np.linspace(0, 1, hours_in_year)
load_profile = base_load + (peak_load - base_load) * (
    0.5 * np.sin(2 * np.pi * t) ** 2
    + 0.25 * np.sin(2 * np.pi * t * 365 / 7) ** 2
    + 0.15 * np.random.normal(0, 1, hours_in_year)
    + 0.1 * np.sin(2 * np.pi * t * 365) ** 2
)
load_profile = np.clip(load_profile, base_load * 0.9, peak_load * 1.05)
load_sorted = np.sort(load_profile)[::-1]
hours = np.arange(hours_in_year)

base_capacity = 500
intermediate_capacity = 850
peak_capacity = 1100

total_energy_gwh = np.trapezoid(load_sorted, hours) / 1000

# Plot
sns.set_context("talk", font_scale=1.2)
fig, ax = plt.subplots(figsize=(16, 9))

peak_color = "#E74C3C"
intermediate_color = "#F39C12"
base_color = "#306998"

ax.fill_between(
    hours,
    load_sorted,
    intermediate_capacity,
    where=(load_sorted > intermediate_capacity),
    color=peak_color,
    alpha=0.3,
    label="Peak load",
)
ax.fill_between(
    hours,
    np.minimum(load_sorted, intermediate_capacity),
    base_capacity,
    where=(load_sorted > base_capacity),
    color=intermediate_color,
    alpha=0.3,
    label="Intermediate load",
)
ax.fill_between(hours, np.minimum(load_sorted, base_capacity), 0, color=base_color, alpha=0.3, label="Base load")

sns.lineplot(x=hours, y=load_sorted, color="#1a1a1a", linewidth=2.5, ax=ax)

# Capacity tier lines
ax.axhline(y=peak_capacity, color=peak_color, linestyle="--", linewidth=1.5, alpha=0.8)
ax.axhline(y=intermediate_capacity, color=intermediate_color, linestyle="--", linewidth=1.5, alpha=0.8)
ax.axhline(y=base_capacity, color=base_color, linestyle="--", linewidth=1.5, alpha=0.8)

ax.text(
    hours_in_year * 0.02,
    peak_capacity + 18,
    "Peak capacity (1,100 MW)",
    fontsize=14,
    color=peak_color,
    fontweight="medium",
)
ax.text(
    hours_in_year * 0.02,
    intermediate_capacity + 18,
    "Intermediate capacity (850 MW)",
    fontsize=14,
    color=intermediate_color,
    fontweight="medium",
)
ax.text(
    hours_in_year * 0.02,
    base_capacity + 18,
    "Base capacity (500 MW)",
    fontsize=14,
    color=base_color,
    fontweight="medium",
)

# Region labels
peak_hours = np.sum(load_sorted > intermediate_capacity)
base_hours = np.sum(load_sorted > base_capacity)

ax.text(
    peak_hours * 0.4,
    peak_capacity + 60,
    "PEAK",
    fontsize=16,
    fontweight="bold",
    color=peak_color,
    ha="center",
    alpha=0.9,
)
ax.text(
    (peak_hours + base_hours) / 2,
    (intermediate_capacity + base_capacity) / 2 + 20,
    "INTERMEDIATE",
    fontsize=16,
    fontweight="bold",
    color="#C87F0A",
    ha="center",
    alpha=0.9,
)
ax.text(
    (base_hours + hours_in_year) / 2,
    base_capacity / 2 + 20,
    "BASE",
    fontsize=16,
    fontweight="bold",
    color=base_color,
    ha="center",
    alpha=0.9,
)

# Energy annotation
ax.text(
    hours_in_year * 0.55,
    load_sorted.max() * 0.95,
    f"Total Energy: {total_energy_gwh:,.0f} GWh/year",
    fontsize=16,
    fontweight="medium",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

# Style
ax.set_xlabel("Hours of Year (ranked)", fontsize=20)
ax.set_ylabel("Power Demand (MW)", fontsize=20)
ax.set_title("line-load-duration · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_xlim(0, hours_in_year)
ax.set_ylim(0, load_sorted.max() * 1.08)

peak_patch = mpatches.Patch(color=peak_color, alpha=0.3, label="Peak load")
inter_patch = mpatches.Patch(color=intermediate_color, alpha=0.3, label="Intermediate load")
base_patch = mpatches.Patch(color=base_color, alpha=0.3, label="Base load")
ax.legend(handles=[peak_patch, inter_patch, base_patch], fontsize=14, loc="upper right", framealpha=0.9)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
