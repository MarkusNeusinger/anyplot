""" anyplot.ai
histogram-overlapping: Overlapping Histograms
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - employee response times (ms) by department
np.random.seed(42)
engineering = np.random.normal(450, 80, 200)
marketing = np.random.normal(520, 100, 180)
sales = np.random.normal(480, 60, 160)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot overlapping histograms
sns.histplot(
    engineering, bins=25, alpha=0.5, color=IMPRINT[0], label="Engineering", edgecolor=PAGE_BG, linewidth=0.5, ax=ax
)
sns.histplot(
    marketing, bins=25, alpha=0.5, color=IMPRINT[1], label="Marketing", edgecolor=PAGE_BG, linewidth=0.5, ax=ax
)
sns.histplot(sales, bins=25, alpha=0.5, color=IMPRINT[2], label="Sales", edgecolor=PAGE_BG, linewidth=0.5, ax=ax)

# Labels and styling
ax.set_xlabel("Response Time (ms)", fontsize=20, color=INK)
ax.set_ylabel("Count", fontsize=20, color=INK)
ax.set_title("histogram-overlapping · seaborn · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend
legend = ax.legend(fontsize=16, loc="upper right", framealpha=1)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
for text in legend.get_texts():
    text.set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
