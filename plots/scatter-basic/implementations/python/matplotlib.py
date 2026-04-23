"""anyplot.ai
scatter-basic: Basic Scatter Plot
Library: matplotlib | Python 3.13
Quality: pending | Updated: 2026-04-23
"""

import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Okabe-Ito position 1

# Global typography via rcParams (matplotlib-native styling)
mpl.rcParams.update(
    {"font.family": "DejaVu Sans", "axes.titlepad": 22, "axes.labelpad": 14, "axes.unicode_minus": True}
)

# Data — study hours vs exam scores (r ~ 0.7)
np.random.seed(42)
study_hours = np.random.uniform(1, 12, 180)
exam_scores = np.clip(38 + study_hours * 4.5 + np.random.normal(0, 6.5, 180), 35, 100)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.scatter(study_hours, exam_scores, s=95, alpha=0.65, color=BRAND, edgecolors=PAGE_BG, linewidths=0.7)

# Style
ax.set_xlabel("Study Hours per Week", fontsize=20, color=INK, fontweight="regular")
ax.set_ylabel("Exam Score (%)", fontsize=20, color=INK, fontweight="regular")
ax.set_title("scatter-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

ax.tick_params(axis="both", which="both", labelsize=16, colors=INK_SOFT, length=0, pad=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
    ax.spines[spine].set_linewidth(0.8)

ax.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.margins(x=0.04, y=0.08)

# Tertiary metadata footnote (n + Pearson r)
r = np.corrcoef(study_hours, exam_scores)[0, 1]
fig.text(
    0.985,
    0.015,
    f"n = {len(study_hours)}  ·  Pearson r = {r:.2f}",
    fontsize=13,
    color=INK_MUTED,
    ha="right",
    va="bottom",
)

plt.tight_layout(rect=(0, 0.03, 1, 1))
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
