""" pyplots.ai
scatter-basic: Basic Scatter Plot
Library: matplotlib 3.10.8 | Python 3.14
Quality: 94/100 | Created: 2025-12-22
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patheffects import withStroke


# Data - study hours vs exam scores (realistic educational context)
np.random.seed(42)
n = 120
study_hours = np.random.uniform(1, 12, n)
base_scores = 40 + study_hours * 5 + np.random.randn(n) * 8
# Add a few clear outliers for scatter pattern diversity
base_scores[10] = 42  # low-study, low-score (expected)
base_scores[45] = 88  # mid-study, high outlier
base_scores[78] = 48  # high-study, low outlier (underperformer)
base_scores[102] = 95  # mid-study, high outlier
exam_scores = np.clip(base_scores, 35, 100)

# Trend line via polynomial fit
z = np.polyfit(study_hours, exam_scores, 1)
p = np.poly1d(z)
x_trend = np.linspace(study_hours.min(), study_hours.max(), 200)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Trend line first (behind scatter)
ax.plot(
    x_trend,
    p(x_trend),
    color="#306998",
    linewidth=2.5,
    linestyle="--",
    alpha=0.6,
    zorder=2,
    label=f"Trend (r = {np.corrcoef(study_hours, exam_scores)[0, 1]:.2f})",
)

# Main scatter
scatter = ax.scatter(
    study_hours,
    exam_scores,
    c=exam_scores,
    cmap="viridis",
    alpha=0.75,
    s=120,
    edgecolors="white",
    linewidths=0.5,
    vmin=35,
    vmax=100,
    zorder=3,
)

# Annotate the underperformer outlier
ax.annotate(
    "Underperformer",
    xy=(study_hours[78], exam_scores[78]),
    xytext=(study_hours[78] + 0.8, exam_scores[78] - 6),
    fontsize=13,
    color="#555555",
    arrowprops={"arrowstyle": "->", "color": "#888888", "lw": 1.2},
    path_effects=[withStroke(linewidth=3, foreground="white")],
    zorder=4,
)

# Annotate the ceiling effect region
ceiling_mask = exam_scores >= 97
if ceiling_mask.sum() > 0:
    cx = study_hours[ceiling_mask].mean()
    ax.annotate(
        "Ceiling effect at 100%",
        xy=(cx, 100),
        xytext=(cx - 2.5, 104),
        fontsize=13,
        color="#555555",
        ha="center",
        arrowprops={"arrowstyle": "->", "color": "#888888", "lw": 1.2},
        path_effects=[withStroke(linewidth=3, foreground="white")],
        zorder=4,
    )

# Colorbar
cbar = fig.colorbar(scatter, ax=ax, pad=0.015, shrink=0.82, aspect=25)
cbar.set_label("Exam Score (%)", fontsize=18)
cbar.ax.tick_params(labelsize=14)
cbar.outline.set_linewidth(0.3)

# Legend for trend line
ax.legend(fontsize=16, loc="lower right", framealpha=0.9, edgecolor="none")

# Style
ax.set_xlabel("Study Hours (per week)", fontsize=20)
ax.set_ylabel("Exam Score (%)", fontsize=20)
ax.set_title("scatter-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, linestyle="--")
ax.set_xlim(0, 13)
ax.set_ylim(30, 108)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
