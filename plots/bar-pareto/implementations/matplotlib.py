"""pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# Data
defect_types = ["Scratches", "Dents", "Misalignment", "Cracks", "Discoloration", "Burrs", "Warping", "Contamination"]
defect_counts = np.array([142, 98, 71, 45, 32, 18, 12, 7])

sort_idx = np.argsort(-defect_counts)
defect_types = [defect_types[i] for i in sort_idx]
defect_counts = defect_counts[sort_idx]

cumulative_pct = np.cumsum(defect_counts) / defect_counts.sum() * 100

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
x = np.arange(len(defect_types))

LINE_COLOR = "#E25A1C"

bars = ax.bar(x, defect_counts, color="#306998", width=0.65, zorder=2)
ax.bar_label(bars, fontsize=14, fontweight="bold", padding=4, color="#1a3a5c")

ax2 = ax.twinx()
ax2.plot(
    x,
    cumulative_pct,
    color=LINE_COLOR,
    marker="o",
    markersize=10,
    linewidth=3,
    markeredgecolor="white",
    markeredgewidth=1.5,
    zorder=3,
)

ax2.axhline(y=80, color=LINE_COLOR, linestyle="--", linewidth=1.5, alpha=0.4, zorder=1)

# Annotate the 80% threshold crossing point
cross_idx = np.searchsorted(cumulative_pct, 80)
cross_x = np.interp(80, cumulative_pct[max(0, cross_idx - 1) : cross_idx + 1], x[max(0, cross_idx - 1) : cross_idx + 1])
ax2.annotate(
    f"80 % reached\n({cross_idx + 1} of {len(defect_types)} types)",
    xy=(cross_x, 80),
    xytext=(cross_x + 1.8, 68),
    fontsize=14,
    color=LINE_COLOR,
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": LINE_COLOR, "lw": 2},
    bbox={"boxstyle": "round,pad=0.4", "fc": "white", "ec": LINE_COLOR, "alpha": 0.9},
    zorder=4,
)

# Style
ax.set_xlabel("Defect Type", fontsize=20)
ax.set_ylabel("Frequency", fontsize=20)
ax2.set_ylabel("Cumulative %", fontsize=20, color=LINE_COLOR)
ax.set_title("bar-pareto · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")

ax.set_xticks(x)
ax.set_xticklabels(defect_types, fontsize=16)
ax.tick_params(axis="y", labelsize=16)
ax2.tick_params(axis="y", labelsize=16, colors=LINE_COLOR)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))

ax2.set_ylim(0, 105)
ax.set_xlim(-0.5, len(defect_types) - 0.5)

ax.spines["top"].set_visible(False)
ax2.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax2.spines["right"].set_color(LINE_COLOR)

ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_axisbelow(True)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
