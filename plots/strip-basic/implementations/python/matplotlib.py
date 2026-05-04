""" anyplot.ai
strip-basic: Basic Strip Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-04
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data — employee satisfaction scores by department (1–10 scale)
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "HR"]
distributions = {
    "Engineering": (7.2, 1.5, 45),
    "Marketing": (6.5, 1.8, 38),
    "Sales": (7.8, 1.2, 52),
    "HR": (6.0, 2.0, 35),
}

dept_scores = {dept: np.clip(np.random.normal(mean, std, n), 1, 10) for dept, (mean, std, n) in distributions.items()}

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, dept in enumerate(departments):
    scores = dept_scores[dept]
    jitter = np.random.uniform(-0.2, 0.2, len(scores))
    ax.scatter(i + jitter, scores, s=200, alpha=0.6, color=OKABE_ITO[i], edgecolors=PAGE_BG, linewidth=0.5)

# Mean reference lines
for i, dept in enumerate(departments):
    mean_val = dept_scores[dept].mean()
    ax.hlines(mean_val, i - 0.35, i + 0.35, colors=INK, linewidth=2.5)

# Style
ax.set_xticks(range(len(departments)))
ax.set_xticklabels(departments)
ax.set_xlabel("Department", fontsize=20, color=INK)
ax.set_ylabel("Satisfaction Score (1–10)", fontsize=20, color=INK)
ax.set_title("strip-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.set_ylim(0.5, 10.5)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
