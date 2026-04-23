""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: matplotlib 3.10.8 | Python 3.14.4
Quality: 85/100 | Created: 2026-04-23
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data — study hours vs exam scores (neutral educational context, r ~ 0.7)
np.random.seed(42)
study_hours = np.random.uniform(1, 12, 180)
exam_scores = np.clip(38 + study_hours * 4.5 + np.random.normal(0, 6.5, 180), 35, 100)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.scatter(study_hours, exam_scores, s=140, alpha=0.7, color=BRAND, edgecolors=PAGE_BG, linewidths=0.8)

# Style
ax.set_xlabel("Study Hours per Week", fontsize=20, color=INK)
ax.set_ylabel("Exam Score (%)", fontsize=20, color=INK)
ax.set_title("scatter-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=18)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.set_xlim(0, 13)
ax.set_ylim(30, 105)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
