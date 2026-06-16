""" anyplot.ai
histogram-stepwise: Step Histogram
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
"""

import os
import sys


# Remove script directory from path to avoid matplotlib.py shadowing the matplotlib package
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir and p not in ("", ".")]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1
ACCENT = "#C475FD"  # Position 2

# Data - Two distributions with distinct shapes
np.random.seed(42)
mc_scores = np.random.normal(loc=72, scale=8, size=250)  # Multiple Choice: symmetric
essay_scores = np.random.beta(a=3, b=1.5, size=250) * 100  # Essay: right-skewed
essay_scores = np.clip(essay_scores, 0, 100)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Step histograms (outline only, no fill)
ax.hist(mc_scores, bins=30, histtype="step", linewidth=3, color=BRAND, label="Multiple Choice")
ax.hist(essay_scores, bins=30, histtype="step", linewidth=3, color=ACCENT, label="Essay Exam", linestyle="--")

# Labels and styling
ax.set_xlabel("Score (%)", fontsize=20, color=INK)
ax.set_ylabel("Number of Students", fontsize=20, color=INK)
ax.set_title("histogram-stepwise · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend with theme-adaptive styling
leg = ax.legend(fontsize=16, loc="upper left", framealpha=0.95)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(1)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

plt.tight_layout()

# Save in the script's directory
output_dir = os.path.dirname(os.path.abspath(__file__))
plt.savefig(os.path.join(output_dir, f"plot-{THEME}.png"), dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
