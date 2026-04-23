"""anyplot.ai
scatter-basic: Basic Scatter Plot
Library: seaborn 0.13.2 | Python 3.14
Quality: pending | Created: 2026-04-23
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data — study hours vs exam scores, moderate positive correlation with realistic spread
np.random.seed(42)
n = 160
study_hours = np.random.uniform(1, 10, n)
exam_scores = 11 * study_hours - 0.35 * study_hours**2 + np.random.randn(n) * 7 + 32

df = pd.DataFrame({"Study Hours (per week)": study_hours, "Exam Score (points)": exam_scores})

# Plot
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
    },
)

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

sns.scatterplot(
    data=df,
    x="Study Hours (per week)",
    y="Exam Score (points)",
    color=BRAND,
    s=200,
    alpha=0.7,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    ax=ax,
)

# Style
ax.set_title("scatter-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=16)
ax.set_xlabel("Study Hours (per week)", fontsize=20, color=INK)
ax.set_ylabel("Exam Score (points)", fontsize=20, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
sns.despine(ax=ax)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
