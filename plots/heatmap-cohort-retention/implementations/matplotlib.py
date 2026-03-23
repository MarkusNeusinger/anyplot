""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-16
"""

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Data
np.random.seed(42)
cohort_labels = [
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
]
cohort_sizes = [1200, 1350, 980, 1100, 1450, 1280, 1050, 1320, 1180, 1400]
n_cohorts = len(cohort_labels)
n_periods = n_cohorts

# Generate realistic retention data with meaningful variation across cohorts
# Some cohorts retain much better (e.g., May launch campaign), some churn faster
retention = np.full((n_cohorts, n_periods), np.nan)
# Per-cohort decay multipliers: <1 = better retention, >1 = worse retention
decay_profiles = [1.0, 1.15, 1.3, 1.1, 0.55, 0.65, 1.2, 0.85, 1.05, 0.75]

for i in range(n_cohorts):
    max_periods = n_periods - i
    retention[i, 0] = 100.0
    for j in range(1, max_periods):
        base_drop = (15 * np.exp(-0.25 * j) + 1.5) * decay_profiles[i]
        noise = np.random.uniform(-2, 2)
        retention[i, j] = max(retention[i, j - 1] - base_drop - noise, 5)

# Find the best-performing cohort (highest average retention) for emphasis
# Require at least 4 periods to qualify as "best" cohort
avg_retention = [np.nanmean(retention[i, 1 : n_periods - i]) if n_periods - i >= 4 else 0.0 for i in range(n_cohorts)]
best_cohort = int(np.argmax(avg_retention))

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Perceptually-uniform colormap
cmap = plt.cm.viridis
norm = mcolors.Normalize(vmin=0, vmax=100)

# Draw heatmap cells using FancyBboxPatch for rounded corners
for i in range(n_cohorts):
    for j in range(n_periods):
        if np.isnan(retention[i, j]):
            continue
        val = retention[i, j]
        color = cmap(norm(val))
        rect = mpatches.FancyBboxPatch(
            (j - 0.47, i - 0.47),
            0.94,
            0.94,
            boxstyle=mpatches.BoxStyle.Round(pad=0, rounding_size=0.08),
            facecolor=color,
            edgecolor="white",
            linewidth=2.5,
        )
        ax.add_patch(rect)
        # Text color: white on dark cells, dark on light cells
        luminance = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
        text_color = "white" if luminance < 0.5 else "#1a1a2e"
        ax.text(
            j,
            i,
            f"{val:.0f}%",
            ha="center",
            va="center",
            fontsize=15,
            fontweight="bold" if i == best_cohort else "medium",
            color=text_color,
        )

# Style
ax.set_xlim(-0.5, n_periods - 0.5)
ax.set_ylim(n_cohorts - 0.5, -0.5)
ax.set_xticks(range(n_periods))
ax.set_xticklabels([f"Month {p}" for p in range(n_periods)], fontsize=16)
ax.set_yticks(range(n_cohorts))
ytick_labels = []
for idx, (label, size) in enumerate(zip(cohort_labels, cohort_sizes, strict=True)):
    text = f"{label}  (n={size:,})"
    if idx == best_cohort:
        text = f"\u2605 {text}"
    ytick_labels.append(text)
ax.set_yticklabels(ytick_labels, fontsize=16)
ax.set_xlabel("Months Since Signup", fontsize=20)
ax.set_ylabel("Signup Cohort", fontsize=20)
ax.set_title("heatmap-cohort-retention · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)

# Highlight best cohort row with a subtle border
highlight_rect = mpatches.FancyBboxPatch(
    (-0.55, best_cohort - 0.55),
    n_periods - best_cohort + 0.1,
    1.1,
    boxstyle=mpatches.BoxStyle.Round(pad=0, rounding_size=0.12),
    facecolor="none",
    edgecolor="#FFD700",
    linewidth=3,
    linestyle="--",
    zorder=5,
)
ax.add_patch(highlight_rect)

for spine in ax.spines.values():
    spine.set_visible(False)
ax.tick_params(axis="both", length=0)

# Colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.6, aspect=25, pad=0.02)
cbar.set_label("Retention Rate (%)", fontsize=16)
cbar.ax.tick_params(labelsize=16)
cbar.outline.set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
