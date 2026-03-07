""" pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-07
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# Data — NPV sensitivity analysis for a capital investment project
base_npv = 12.5  # Base case NPV in $M

parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Initial CapEx",
    "Operating Costs",
    "Tax Rate",
    "Terminal Value",
    "Working Capital",
    "Inflation Rate",
    "Project Duration",
    "Salvage Value",
]

low_npv = np.array([16.8, 8.2, 14.9, 15.1, 14.0, 10.1, 13.6, 13.4, 10.9, 11.8])
high_npv = np.array([9.1, 17.3, 10.4, 10.2, 11.2, 15.4, 11.5, 11.7, 14.3, 13.3])

# Sort by total range (widest bar at top)
total_range = np.abs(high_npv - low_npv)
sort_idx = np.argsort(total_range)
parameters = [parameters[i] for i in sort_idx]
low_npv = low_npv[sort_idx]
high_npv = high_npv[sort_idx]

# Compute bar segments relative to base
low_delta = low_npv - base_npv
high_delta = high_npv - base_npv

y_pos = np.arange(len(parameters))

# Colorblind-safe palette: teal + warm coral with intensity gradient
base_low = np.array([0.165, 0.616, 0.561])  # #2A9D8F in RGB
base_high = np.array([0.906, 0.435, 0.318])  # #E76F51 in RGB

# Compute per-bar alpha for intensity gradient (wider bars → more saturated)
sorted_range = np.abs(high_npv - low_npv)
range_norm = sorted_range / sorted_range.max()
alphas = 0.45 + 0.55 * range_norm  # range 0.45 to 1.0

n = len(parameters)
top_k = 3  # number of top drivers to emphasize

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

for i in range(n):
    ax.barh(
        y_pos[i],
        low_delta[i],
        left=base_npv,
        height=0.6,
        color=base_low,
        alpha=alphas[i],
        label="Low Scenario" if i == n - 1 else None,
        edgecolor="white",
        linewidth=0.5,
    )
    ax.barh(
        y_pos[i],
        high_delta[i],
        left=base_npv,
        height=0.6,
        color=base_high,
        alpha=alphas[i],
        label="High Scenario" if i == n - 1 else None,
        edgecolor="white",
        linewidth=0.5,
    )

# Bar-end value labels with PathEffects for readability
label_outline = [pe.withStroke(linewidth=2.5, foreground="white")]

for i in range(n):
    is_top = i >= n - top_k  # top drivers (sorted ascending, so last indices are widest)
    label_size = 12 if is_top else 11
    label_weight = "bold" if is_top else "medium"

    # Low scenario label
    lx = low_npv[i]
    offset = -0.15 if low_delta[i] < 0 else 0.15
    ha = "right" if low_delta[i] < 0 else "left"
    ax.text(
        lx + offset,
        y_pos[i],
        f"${lx:.1f}M",
        va="center",
        ha=ha,
        fontsize=label_size,
        fontweight=label_weight,
        color=base_low * 0.75,
        path_effects=label_outline,
    )

    # High scenario label
    hx = high_npv[i]
    offset = 0.15 if high_delta[i] > 0 else -0.15
    ha = "left" if high_delta[i] > 0 else "right"
    ax.text(
        hx + offset,
        y_pos[i],
        f"${hx:.1f}M",
        va="center",
        ha=ha,
        fontsize=label_size,
        fontweight=label_weight,
        color=base_high * 0.75,
        path_effects=label_outline,
    )

# Base case reference line with annotation using PathEffects
ax.axvline(x=base_npv, color="#444444", linewidth=1.5, linestyle="-", zorder=3)
ax.text(
    base_npv + 0.15,
    n - 0.5,
    f"  Base Case: ${base_npv:.1f}M",
    fontsize=13,
    fontweight="bold",
    color="#444444",
    ha="left",
    va="center",
    path_effects=[pe.withStroke(linewidth=3, foreground="white")],
)

# X-axis dollar formatting using FuncFormatter
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.0f}M"))

# Style — bold y-tick labels for top drivers
ax.set_yticks(y_pos)
ytick_labels = ax.set_yticklabels(parameters, fontsize=16)
for i in range(n):
    if i >= n - top_k:
        ytick_labels[i].set_fontweight("bold")
        ytick_labels[i].set_fontsize(17)
ax.set_xlabel("Net Present Value", fontsize=20)
ax.set_title("bar-tornado-sensitivity · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="x", labelsize=16)
ax.tick_params(axis="y", length=0)
ax.legend(fontsize=16, loc="lower right", frameon=False)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.xaxis.grid(True, alpha=0.2, linewidth=0.8)

# Tighten x-axis to data range with minimal padding for labels
xlim = ax.get_xlim()
ax.set_xlim(xlim[0] - 0.3, xlim[1] + 0.3)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
