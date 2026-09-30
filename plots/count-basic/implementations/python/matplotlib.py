"""anyplot.ai
count-basic: Basic Count Plot
Library: matplotlib 3.11.2 | Python 3.13.15
Quality: pending | Updated: 2026-09-27
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
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series

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
total = counts.sum()
percentages = counts / total * 100

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Basic variant: one color for every bar, no per-bar emphasis.
bars = ax.bar(unique, counts, color=BRAND, edgecolor=PAGE_BG, linewidth=1.5, width=0.62)

# Direct value + share labels replace the y-axis (matplotlib's bar_label API);
# an explicit axis title still tells a reader skimming the axis that these
# are response counts before they reach the bar labels.
ax.bar_label(
    bars,
    labels=[f"{c}\n{p:.0f}%" for c, p in zip(counts, percentages, strict=True)],
    padding=10,
    fontsize=10,
    color=INK,
    linespacing=1.3,
)

# Style — minimalist: no numeric y-axis ticks, values are direct-labeled on the
# bars instead; an explicit axis title still tells a reader skimming the axis
# that these are response counts.
ax.set_xlabel("Survey Response", fontsize=10, color=INK)
ax.set_ylabel("Number of Responses", fontsize=10, color=INK)
ax.set_title("count-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)

# Headroom for the two-line bar labels above the tallest bar
ax.set_ylim(0, counts.max() * 1.3)

# Faint reference gridlines (no numeric labels) give returning readers a scale
# anchor without reintroducing a full y-axis — the direct bar labels stay the
# primary reading mode.
ax.set_yticks(np.linspace(0, counts.max() * 1.3, 5))
ax.set_yticklabels([])
ax.tick_params(axis="y", length=0)
ax.yaxis.grid(True, color=INK, alpha=0.08, linewidth=0.8, zorder=0)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
