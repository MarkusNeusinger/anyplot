"""anyplot.ai
scatter-basic: Basic Scatter Plot
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-06-25
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
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series

mpl.rcParams.update(
    {"font.family": "DejaVu Sans", "axes.titlepad": 18, "axes.labelpad": 12, "axes.unicode_minus": True}
)

# Data — study hours vs exam scores (r ~ 0.7)
np.random.seed(42)
study_hours = np.random.uniform(1, 12, 180)
exam_scores = np.clip(38 + study_hours * 4.5 + np.random.normal(0, 12, 180), 35, 100)

# Title
title = "scatter-basic · python · matplotlib · anyplot.ai"
n = len(title)
title_fontsize = max(8, round(12 * 67 / n)) if n > 67 else 12

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.scatter(study_hours, exam_scores, s=130, alpha=0.65, color=BRAND, edgecolors=PAGE_BG, linewidths=0.6, zorder=3)

# Trend line guides the eye through the positive correlation
coeffs = np.polyfit(study_hours, exam_scores, 1)
x_line = np.linspace(study_hours.min(), study_hours.max(), 200)
y_line = np.polyval(coeffs, x_line)
ax.plot(x_line, y_line, color=INK_SOFT, linewidth=1.8, alpha=0.55, zorder=1)

# Style
ax.set_xlabel("Study Hours per Week", fontsize=10, color=INK)
ax.set_ylabel("Exam Score (%)", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)

ax.tick_params(axis="both", which="both", labelsize=8, colors=INK_SOFT, length=0, pad=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
    ax.spines[spine].set_linewidth(0.8)

ax.grid(True, alpha=0.12, linewidth=0.6, color=INK)
ax.set_axisbelow(True)
ax.margins(x=0.04, y=0.08)

# Pearson r footnote
r = np.corrcoef(study_hours, exam_scores)[0, 1]
fig.text(
    0.985, 0.03, f"n = {len(study_hours)}  ·  Pearson r = {r:.2f}", fontsize=8, color=INK_MUTED, ha="right", va="bottom"
)

fig.subplots_adjust(left=0.09, right=0.97, top=0.90, bottom=0.14)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
