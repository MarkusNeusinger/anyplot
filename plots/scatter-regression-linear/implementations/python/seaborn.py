""" pyplots.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Study hours vs exam scores with realistic correlation
np.random.seed(42)
n_points = 80
study_hours = np.random.uniform(1, 10, n_points)
exam_scores = 45 + 5 * study_hours + np.random.normal(0, 8, n_points)
exam_scores = np.clip(exam_scores, 0, 100)

# Calculate regression statistics using numpy
slope, intercept = np.polyfit(study_hours, exam_scores, 1)
y_pred = slope * study_hours + intercept
ss_res = np.sum((exam_scores - y_pred) ** 2)
ss_tot = np.sum((exam_scores - np.mean(exam_scores)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot with seaborn regplot - includes regression line and confidence band
sns.regplot(
    x=study_hours,
    y=exam_scores,
    ax=ax,
    scatter_kws={"s": 150, "alpha": 0.65, "color": "#306998"},
    line_kws={"color": "#FFD43B", "linewidth": 3},
    ci=95,
    color="#FFD43B",
)

# Add regression equation and R² annotation
equation_text = f"y = {slope:.2f}x + {intercept:.1f}\nR² = {r_squared:.3f}"
ax.annotate(
    equation_text,
    xy=(0.05, 0.95),
    xycoords="axes fraction",
    fontsize=18,
    verticalalignment="top",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "alpha": 0.8, "edgecolor": "#306998"},
)

# Labels and styling
ax.set_xlabel("Study Hours", fontsize=20)
ax.set_ylabel("Exam Score (%)", fontsize=20)
ax.set_title("scatter-regression-linear · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Set axis limits with padding
ax.set_xlim(0, 11)
ax.set_ylim(30, 105)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
