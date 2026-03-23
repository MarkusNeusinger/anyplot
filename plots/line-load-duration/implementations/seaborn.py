""" pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-15
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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

# Classify each hour into a load region for seaborn hue mapping
region = np.where(
    load_sorted > intermediate_capacity,
    "Peak load",
    np.where(load_sorted > base_capacity, "Intermediate load", "Base load"),
)

df = pd.DataFrame({"hour": hours, "load_mw": load_sorted, "region": region})

# Seaborn theme and palette
sns.set_theme(style="ticks", context="talk", font_scale=1.2)
cb_palette = sns.color_palette("colorblind")
region_colors = {"Peak load": cb_palette[3], "Intermediate load": cb_palette[4], "Base load": cb_palette[0]}

fig, ax = plt.subplots(figsize=(16, 9))

# Filled regions using seaborn palette colors (colorblind-safe: red, medium blue, dark blue)
ax.fill_between(
    hours,
    load_sorted,
    intermediate_capacity,
    where=(load_sorted > intermediate_capacity),
    color=region_colors["Peak load"],
    alpha=0.25,
)
ax.fill_between(
    hours,
    np.minimum(load_sorted, intermediate_capacity),
    base_capacity,
    where=(load_sorted > base_capacity),
    color=region_colors["Intermediate load"],
    alpha=0.25,
)
ax.fill_between(hours, np.minimum(load_sorted, base_capacity), 0, color=region_colors["Base load"], alpha=0.25)

# Main load duration curve using seaborn lineplot with hue for region coloring
sns.lineplot(
    data=df,
    x="hour",
    y="load_mw",
    hue="region",
    hue_order=["Peak load", "Intermediate load", "Base load"],
    palette=region_colors,
    linewidth=2.8,
    legend=False,
    ax=ax,
)

# Overlay a solid black line on top for the overall curve silhouette
sns.lineplot(x=hours, y=load_sorted, color="#1a1a1a", linewidth=1.2, alpha=0.6, ax=ax)

# Capacity tier dashed lines
for capacity, label, color in [
    (peak_capacity, "Peak capacity (1,100 MW)", region_colors["Peak load"]),
    (intermediate_capacity, "Intermediate capacity (850 MW)", region_colors["Intermediate load"]),
    (base_capacity, "Base capacity (500 MW)", region_colors["Base load"]),
]:
    ax.axhline(y=capacity, color=color, linestyle="--", linewidth=1.5, alpha=0.7)
    ax.text(hours_in_year * 0.62, capacity + 18, label, fontsize=14, color=color, fontweight="semibold")

# Region labels — positioned within shaded areas to avoid crowding with capacity labels
peak_hours = np.sum(load_sorted > intermediate_capacity)
base_hours = np.sum(load_sorted > base_capacity)

ax.text(
    peak_hours * 0.35,
    (load_sorted[:peak_hours].mean() + intermediate_capacity) / 2,
    "PEAK",
    fontsize=18,
    fontweight="bold",
    color=region_colors["Peak load"],
    ha="center",
    va="center",
    alpha=0.85,
)
ax.text(
    (peak_hours + base_hours) / 2,
    (intermediate_capacity + base_capacity) / 2,
    "INTERMEDIATE",
    fontsize=18,
    fontweight="bold",
    color=region_colors["Intermediate load"],
    ha="center",
    va="center",
    alpha=0.85,
)
ax.text(
    (base_hours + hours_in_year) / 2,
    base_capacity / 2,
    "BASE",
    fontsize=18,
    fontweight="bold",
    color=region_colors["Base load"],
    ha="center",
    va="center",
    alpha=0.85,
)

# Energy annotation with refined box
ax.text(
    hours_in_year * 0.42,
    load_sorted.max() * 0.96,
    f"Total Energy: {total_energy_gwh:,.0f} GWh/year",
    fontsize=16,
    fontweight="semibold",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "#f8f9fa", "edgecolor": "#adb5bd", "alpha": 0.95, "linewidth": 1.2},
)

# Style using seaborn's despine and formatting
ax.set_xlabel("Hours of Year (ranked)", fontsize=20)
ax.set_ylabel("Power Demand (MW)", fontsize=20)
ax.set_title("line-load-duration · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color="#888888")
ax.set_xlim(0, hours_in_year)
ax.set_ylim(0, load_sorted.max() * 1.08)

# Legend using seaborn-built handles from the hue-mapped lineplot
legend_handles = [
    plt.Line2D([0], [0], color=region_colors["Peak load"], linewidth=3, alpha=0.8, label="Peak load"),
    plt.Line2D([0], [0], color=region_colors["Intermediate load"], linewidth=3, alpha=0.8, label="Intermediate load"),
    plt.Line2D([0], [0], color=region_colors["Base load"], linewidth=3, alpha=0.8, label="Base load"),
]
ax.legend(handles=legend_handles, fontsize=14, loc="upper right", framealpha=0.92, edgecolor="#cccccc")

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
