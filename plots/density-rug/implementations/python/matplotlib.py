""" anyplot.ai
density-rug: Density Plot with Rug Marks
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Response times (ms) for a web service with bimodal distribution
np.random.seed(42)
# Mix of fast responses (cache hits) and slower responses (database queries)
fast_responses = np.random.normal(loc=45, scale=8, size=80)
slow_responses = np.random.normal(loc=120, scale=25, size=70)
response_times = np.concatenate([fast_responses, slow_responses])
response_times = response_times[response_times > 0]  # Keep only positive values

# Compute KDE
kde = gaussian_kde(response_times, bw_method="scott")
x_range = np.linspace(response_times.min() - 10, response_times.max() + 10, 500)
density = kde(x_range)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# KDE curve with fill
ax.fill_between(x_range, density, alpha=0.4, color=BRAND)
ax.plot(x_range, density, color=BRAND, linewidth=3)

# Rug marks along x-axis
rug_height = 0.015 * density.max()
for val in response_times:
    ax.plot([val, val], [0, rug_height], color=BRAND, alpha=0.6, linewidth=2)

# Style
ax.set_xlabel("Response Time (ms)", fontsize=20, color=INK)
ax.set_ylabel("Density", fontsize=20, color=INK)
ax.set_title("density-rug · Python · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Set y-axis to start at 0 with some padding at top
ax.set_ylim(bottom=-0.0005, top=density.max() * 1.1)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
