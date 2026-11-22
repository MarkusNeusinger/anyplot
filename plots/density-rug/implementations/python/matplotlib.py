"""anyplot.ai
density-rug: Density Plot with Rug Marks
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, position 1 is the brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column constants
RESPONSE_TIME = "Response Time (ms)"  # role: values

# Data - response times of a web service: fast cache hits and slower database queries
np.random.seed(42)
fast_responses = np.random.normal(loc=45, scale=8, size=80)
slow_responses = np.random.normal(loc=120, scale=25, size=70)
response_times = np.concatenate([fast_responses, slow_responses])
df = pd.DataFrame({RESPONSE_TIME: response_times[response_times > 0]})

# Plot: reads only df and the constants above
values = df[RESPONSE_TIME].dropna().to_numpy()
kde = gaussian_kde(values, bw_method="scott")
x_range = np.linspace(values.min() - 10, values.max() + 10, 500)
density = kde(x_range)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.fill_between(x_range, density, alpha=0.4, color=IMPRINT_PALETTE[0], linewidth=0)
ax.plot(x_range, density, color=IMPRINT_PALETTE[0], linewidth=1.8)

# Rug: one tick per observation at its exact value, far shorter than the curve
rug_height = 0.03 * density.max()
ax.vlines(values, 0, rug_height, color=IMPRINT_PALETTE[0], alpha=0.6, linewidth=0.8)

ax.set_xlabel(RESPONSE_TIME, fontsize=10, color=INK)
ax.set_ylabel("Density", fontsize=10, color=INK)
ax.set_title("density-rug · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8, color=INK_SOFT)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.set_ylim(0, density.max() * 1.1)
ax.set_xlim(x_range.min(), x_range.max())

fig.subplots_adjust(left=0.09, right=0.97, top=0.91, bottom=0.13)
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
