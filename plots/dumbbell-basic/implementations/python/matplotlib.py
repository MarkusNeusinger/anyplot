""" anyplot.ai
dumbbell-basic: Basic Dumbbell Chart
Library: matplotlib 3.10.9 | Python 3.14.4
Quality: 85/100 | Created: 2026-04-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = (0.10, 0.10, 0.09, 0.18) if THEME == "light" else (0.94, 0.94, 0.91, 0.22)

BEFORE_COLOR = "#009E73"  # Okabe-Ito 1 — first series
AFTER_COLOR = "#D55E00"  # Okabe-Ito 2

# Data: Employee satisfaction scores before and after workplace policy changes
categories = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations", "Customer Support", "Product"]
before_scores = [65, 58, 72, 45, 68, 52, 40, 75]
after_scores = [82, 71, 78, 73, 75, 68, 62, 88]

# Sort by improvement (largest at top)
differences = [a - b for a, b in zip(after_scores, before_scores, strict=True)]
sorted_indices = np.argsort(differences)
categories = [categories[i] for i in sorted_indices]
before_scores = [before_scores[i] for i in sorted_indices]
after_scores = [after_scores[i] for i in sorted_indices]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

y_positions = np.arange(len(categories))

# Connecting lines
for i, (start, end) in enumerate(zip(before_scores, after_scores, strict=True)):
    ax.plot([start, end], [i, i], color=INK_SOFT, linewidth=2.5, alpha=0.55, zorder=1)

# Dots
ax.scatter(
    before_scores, y_positions, s=320, color=BEFORE_COLOR, label="Before", zorder=2, edgecolors=PAGE_BG, linewidths=2
)
ax.scatter(
    after_scores, y_positions, s=320, color=AFTER_COLOR, label="After", zorder=2, edgecolors=PAGE_BG, linewidths=2
)

# Style
ax.set_yticks(y_positions)
ax.set_yticklabels(categories, color=INK_SOFT)
ax.set_xlabel("Satisfaction Score", fontsize=20, color=INK)
ax.set_ylabel("Department", fontsize=20, color=INK)
ax.set_title("dumbbell-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_xlim(30, 100)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.xaxis.grid(True, color=RULE, linewidth=0.8)
ax.set_axisbelow(True)

leg = ax.legend(fontsize=16, loc="lower right", frameon=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
