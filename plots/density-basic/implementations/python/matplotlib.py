"""anyplot.ai
density-basic: Basic Density Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-30
"""

import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from matplotlib.collections import EventCollection
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series

# Column constants
RESPONSE_TIME = "Response Time (ms)"  # role: values

# Data: replace this block with your own table, for example df = pd.DataFrame({RESPONSE_TIME: [...]})
np.random.seed(42)
cached_responses = np.random.normal(45, 12, 350)  # Fast cache-hit requests
db_responses = np.random.normal(140, 25, 150)  # Slower database-query requests
samples = np.concatenate([cached_responses, db_responses])
df = pd.DataFrame({RESPONSE_TIME: samples[samples > 0]})

# Plot
values = df[RESPONSE_TIME].dropna().to_numpy()

# KDE with Silverman bandwidth; the grid ends a few bandwidths beyond the data so tails reach zero
kde = stats.gaussian_kde(values, bw_method="silverman")
bandwidth = kde.factor * values.std(ddof=1)
x_range = np.linspace(max(values.min() - 2 * bandwidth, 0), values.max() + 2 * bandwidth, 600)
density = kde(x_range)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Translucent fill under the curve, then the outline
ax.fill_between(x_range, density, color=BRAND, alpha=0.25, linewidth=0, zorder=1)
ax.plot(x_range, density, linewidth=2.5, color=BRAND, zorder=3)

# Rug of the individual observations in a band below zero
rug_height = density.max() * 0.06
rug = EventCollection(
    values, lineoffset=-rug_height, linelength=rug_height * 1.6, linewidth=1.1, color=BRAND, alpha=0.55, zorder=2
)
ax.add_collection(rug)

# Style
title = "density-basic · python · matplotlib · anyplot.ai"
title_n = len(title)
title_fontsize = max(8, round(12 * 67 / title_n)) if title_n > 67 else 12

ax.set_xlabel(RESPONSE_TIME, fontsize=10, color=INK)
ax.set_ylabel("Density", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=12)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%g"))

# Grid and spines
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Limits: bottom leaves room for the rug band, which carries no density tick labels
ax.set_xlim(x_range[0], x_range[-1])
ax.set_ylim(bottom=-rug_height * 2, top=density.max() * 1.05)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: "" if v < 0 else f"{v:.4g}"))

plt.tight_layout()

# Save — no bbox_inches='tight' (preserves exact 3200×1800 canvas)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
