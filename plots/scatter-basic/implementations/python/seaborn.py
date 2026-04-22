""" pyplots.ai
scatter-basic: Basic Scatter Plot
Library: seaborn 0.13.2 | Python 3.14
Quality: 96/100 | Created: 2025-12-22
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - study hours vs exam scores with realistic correlation and variety
np.random.seed(42)
n = 150
study_hours = np.random.uniform(1, 10, n)

# Base relationship with slight curvature (diminishing returns at high hours)
exam_scores = 12 * study_hours - 0.4 * study_hours**2 + np.random.randn(n) * 7 + 30

# Add a few natural outliers: high-performing low-study and low-performing high-study
exam_scores[0] = 95  # gifted student, low study
study_hours[0] = 2.5
exam_scores[5] = 28  # struggled despite effort
study_hours[5] = 8.5
exam_scores[10] = 88  # another high performer
study_hours[10] = 3.0
exam_scores[140] = 35  # underperformer
study_hours[140] = 7.8
exam_scores[145] = 92  # moderate study, great result
study_hours[145] = 5.5

df = pd.DataFrame({"Study Hours (per week)": study_hours, "Exam Score (points)": exam_scores})

# Compute Pearson correlation for annotation
r = np.corrcoef(study_hours, exam_scores)[0, 1]

# Plot with seaborn regplot — distinctive seaborn feature combining scatter + regression
sns.set_theme(
    style="ticks",
    context="talk",
    font_scale=1.1,
    rc={"font.family": "sans-serif", "axes.edgecolor": "#888888", "axes.linewidth": 0.8},
)

fig, ax = plt.subplots(figsize=(16, 9))

sns.regplot(
    data=df,
    x="Study Hours (per week)",
    y="Exam Score (points)",
    ax=ax,
    scatter_kws={"alpha": 0.6, "s": 80, "edgecolors": "white", "linewidths": 0.6, "zorder": 3},
    line_kws={"color": "#c44e52", "linewidth": 2.5, "zorder": 4},
    color="#306998",
    ci=95,
)

# Correlation annotation — guides the viewer's interpretation
ax.annotate(
    f"r = {r:.2f}",
    xy=(0.97, 0.06),
    xycoords="axes fraction",
    fontsize=18,
    fontweight="bold",
    color="#444444",
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

# Style
ax.set_title("scatter-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", color="#333333", pad=16)
ax.set_xlabel("Study Hours (per week)", fontsize=20, color="#444444")
ax.set_ylabel("Exam Score (points)", fontsize=20, color="#444444")
ax.tick_params(axis="both", labelsize=16, colors="#555555")
ax.grid(True, alpha=0.15, linestyle="--", linewidth=0.6)
sns.despine(ax=ax)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
