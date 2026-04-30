""" anyplot.ai
rug-basic: Basic Rug Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-04-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import EventCollection


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - trimodal response times with outliers to show clustering, gaps, and extremes
np.random.seed(42)
core_values = np.concatenate(
    [
        np.random.normal(25, 4, 50),  # Tight cluster around 25 ms
        np.random.normal(55, 7, 35),  # Wider cluster around 55 ms
        np.random.normal(75, 3, 15),  # Small cluster at high end
    ]
)
outliers = np.array([5.2, 7.8, 95.3, 98.6])  # Extreme outliers at both ends
values = np.concatenate([core_values, outliers])

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Rug plot using EventCollection — idiomatic matplotlib for 1D event distributions
events = EventCollection(
    values, orientation="horizontal", lineoffset=0.35, linelength=0.7, linewidth=2.5, color=BRAND, alpha=0.7
)
ax.add_collection(events)

ax.set_xlim(-2, 107)
ax.set_ylim(0, 1)

# Hide y-axis — rug plots focus on the x-distribution only
ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)

# Cluster annotations (keep strength from previous version, theme-adaptive)
ax.text(25, 0.88, "Dense cluster\n(n=50)", ha="center", fontsize=16, color=INK_SOFT)
ax.text(55, 0.88, "Wider spread\n(n=35)", ha="center", fontsize=16, color=INK_SOFT)
ax.text(75, 0.88, "Small group\n(n=15)", ha="center", fontsize=16, color=INK_SOFT)

# Outlier callouts at both extremes
ax.text(6.5, 0.60, "outliers", ha="center", fontsize=14, color=INK_MUTED, style="italic")
ax.text(96.9, 0.60, "outliers", ha="center", fontsize=14, color=INK_MUTED, style="italic")

# Labels and title
ax.set_xlabel("Response Time (ms)", fontsize=20, color=INK)
ax.set_title("rug-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)
ax.tick_params(axis="x", labelsize=16, colors=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
