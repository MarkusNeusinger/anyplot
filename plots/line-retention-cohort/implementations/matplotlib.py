""" pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-16
"""

import matplotlib.pyplot as plt
import numpy as np


# Data
np.random.seed(42)

cohorts = {
    "Jan 2025": {"size": 1245, "base_rate": 0.82},
    "Feb 2025": {"size": 1102, "base_rate": 0.80},
    "Mar 2025": {"size": 1380, "base_rate": 0.78},
    "Apr 2025": {"size": 1510, "base_rate": 0.85},
    "May 2025": {"size": 1423, "base_rate": 0.88},
}

weeks = np.arange(0, 13)

retention_data = {}
for cohort, info in cohorts.items():
    retention = [100.0]
    for week in weeks[1:]:
        decay = info["base_rate"] ** week * 100
        noise = np.random.normal(0, 1.2)
        value = max(decay + noise, 5)
        retention.append(round(value, 1))
    retention_data[cohort] = retention

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

colors = ["#8fadc2", "#7a9db8", "#306998", "#2a7f62", "#1a6b4a"]
linewidths = [2.0, 2.2, 2.5, 2.8, 3.2]
alphas = [0.55, 0.65, 0.75, 0.85, 1.0]

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
        markersize=6,
        markeredgecolor="white",
        markeredgewidth=0.5,
        label=label,
        zorder=2 + i,
    )

# Reference line
ax.axhline(y=20, color="#999999", linestyle="--", linewidth=1.5, alpha=0.6, zorder=1)
ax.text(12.2, 20, "20% target", fontsize=14, color="#999999", va="center", ha="left")

# Style
ax.set_xlabel("Weeks Since Signup", fontsize=20)
ax.set_ylabel("Retained Users (%)", fontsize=20)
ax.set_title("line-retention-cohort · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)

ax.set_xlim(-0.3, 12.5)
ax.set_ylim(0, 105)
ax.set_xticks(weeks)
ax.set_yticks([0, 20, 40, 60, 80, 100])

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

ax.legend(fontsize=14, loc="upper right", framealpha=0.9, edgecolor="none")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
