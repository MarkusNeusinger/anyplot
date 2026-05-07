""" anyplot.ai
count-basic: Basic Count Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-07
"""

import os
import sys


sys.path.pop(0)
import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Survey responses with varying frequencies
np.random.seed(42)
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
weights = [0.15, 0.35, 0.25, 0.18, 0.07]
responses = np.random.choice(categories, size=200, p=weights)

# Count occurrences
unique, counts = np.unique(responses, return_counts=True)

# Sort by frequency (descending)
sort_idx = np.argsort(counts)[::-1]
unique = unique[sort_idx]
counts = counts[sort_idx]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
bars = ax.bar(unique, counts, color=BRAND, edgecolor=PAGE_BG, linewidth=0.5, width=0.7)

# Add count labels on top of bars
for bar, count in zip(bars, counts, strict=True):
    ax.annotate(
        f"{count}",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 8),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )

# Style
ax.set_xlabel("Survey Response", fontsize=20, color=INK)
ax.set_ylabel("Count", fontsize=20, color=INK)
ax.set_title("count-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Adjust y-axis to give room for labels
ax.set_ylim(0, max(counts) * 1.15)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
