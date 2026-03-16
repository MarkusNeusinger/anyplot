""" pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-16
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# Data
np.random.seed(42)

cohorts = {
    "Jan 2025": {"size": 1245, "base_rate": 0.82, "plateau": 8},
    "Feb 2025": {"size": 1102, "base_rate": 0.80, "plateau": 12},
    "Mar 2025": {"size": 1380, "base_rate": 0.78, "plateau": 15},
    "Apr 2025": {"size": 1510, "base_rate": 0.85, "plateau": 22},
    "May 2025": {"size": 1423, "base_rate": 0.88, "plateau": 30},
}

weeks = np.arange(0, 13)

retention_data = {}
for cohort, info in cohorts.items():
    retention = [100.0]
    for week in weeks[1:]:
        decay = info["base_rate"] ** week * 100
        plateau = info["plateau"]
        value = max(decay, plateau) + np.random.normal(0, 1.0)
        value = max(value, plateau - 2)
        retention.append(round(value, 1))
    retention_data[cohort] = retention

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

colors = ["#4e79a7", "#a0cbe8", "#306998", "#59a14f", "#1a6b4a"]
linewidths = [2.0, 2.2, 2.5, 2.8, 3.2]
alphas = [0.6, 0.65, 0.75, 0.88, 1.0]
marker_sizes = [5, 5.5, 6, 6.5, 7]

for i, (cohort, retention) in enumerate(retention_data.items()):
    size = cohorts[cohort]["size"]
    label = f"{cohort} (n={size:,})"
    ax.plot(
        weeks,
        retention,
        color=colors[i],
        linewidth=linewidths[i],
        alpha=alphas[i],
        marker="o",
        markersize=marker_sizes[i],
        markeredgecolor="white",
        markeredgewidth=0.8,
        label=label,
        zorder=2 + i,
        path_effects=[pe.Stroke(linewidth=linewidths[i] + 1.5, foreground="white"), pe.Normal()],
    )

# Reference line
ax.axhline(y=20, color="#aaaaaa", linestyle="--", linewidth=1.2, alpha=0.7, zorder=1)
ax.annotate(
    "20% retention target",
    xy=(12, 20),
    xytext=(10.5, 24),
    fontsize=13,
    color="#888888",
    fontstyle="italic",
    arrowprops={"arrowstyle": "-", "color": "#aaaaaa", "lw": 0.8},
)

# Y-axis percentage formatter
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}%"))

# Style
ax.set_xlabel("Weeks Since Signup", fontsize=20)
ax.set_ylabel("Retained Users", fontsize=20)
ax.set_title("line-retention-cohort · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)

ax.set_xlim(-0.3, 12.5)
ax.set_ylim(0, 105)
ax.set_xticks(weeks)
ax.set_yticks([0, 20, 40, 60, 80, 100])

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#cccccc")
ax.spines["bottom"].set_color("#cccccc")
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color="#888888")

ax.legend(fontsize=16, loc="upper right", framealpha=0.92, edgecolor="#dddddd", fancybox=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
