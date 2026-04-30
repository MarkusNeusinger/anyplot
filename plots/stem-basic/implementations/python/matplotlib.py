"""anyplot.ai
stem-basic: Basic Stem Plot
Library: matplotlib | Python 3.13
Quality: 94/100 | Updated: 2026-04-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - discrete damped oscillation signal
np.random.seed(42)
x = np.arange(0, 30)
y = np.exp(-x / 10) * np.cos(x * 0.8) + np.random.randn(30) * 0.05

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

markerline, stemlines, baseline = ax.stem(x, y, basefmt="-")
plt.setp(stemlines, linewidth=2, color=BRAND, alpha=0.8)
plt.setp(markerline, markersize=12, color=BRAND, markeredgecolor=PAGE_BG, markeredgewidth=2)
plt.setp(baseline, linewidth=1.5, color=INK_SOFT)

# Style
ax.set_xlabel("Sample Index (n)", fontsize=20, color=INK)
ax.set_ylabel("Amplitude (V)", fontsize=20, color=INK)
ax.set_title("stem-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
