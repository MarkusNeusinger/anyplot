"""anyplot.ai
stem-basic: Basic Stem Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-07-25
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
POSITIVE = "#009E73"  # Imprint palette position 1 — semantic exception: positive polarity
NEGATIVE = "#AE3030"  # Imprint palette position 5 — semantic exception: negative polarity

# Data - discrete damped oscillation signal
np.random.seed(42)
sample_index = np.arange(0, 30)
amplitude = np.exp(-sample_index / 10) * np.cos(sample_index * 0.8) + np.random.randn(30) * 0.05
is_positive = amplitude >= 0

# Plot — see default-style-guide.md "Visual Sizing Defaults" for the canvas + sizing values
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

markerline_pos, stemlines_pos, _ = ax.stem(sample_index[is_positive], amplitude[is_positive], basefmt=" ")
markerline_neg, stemlines_neg, _ = ax.stem(sample_index[~is_positive], amplitude[~is_positive], basefmt=" ")
ax.axhline(0, linewidth=1.5, color=INK_SOFT)

plt.setp(stemlines_pos, linewidth=2, color=POSITIVE, alpha=0.8)
plt.setp(markerline_pos, markersize=12, color=POSITIVE, markeredgecolor=PAGE_BG, markeredgewidth=2)
plt.setp(stemlines_neg, linewidth=2, color=NEGATIVE, alpha=0.8)
plt.setp(markerline_neg, markersize=12, color=NEGATIVE, markeredgecolor=PAGE_BG, markeredgewidth=2)

# Style
title = "stem-basic · python · matplotlib · anyplot.ai"
ax.set_xlabel("Sample Index (n)", fontsize=10, color=INK)
ax.set_ylabel("Amplitude (V)", fontsize=10, color=INK)
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)  # bbox_inches MUST stay default (None)
