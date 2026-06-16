""" anyplot.ai
pp-basic: Probability-Probability (P-P) Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Updated: 2026-06-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential colormap — single-polarity (brand green -> blue)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Data — Manufacturing QC: do steel-bolt tensile strengths (MPa) follow a normal distribution?
# A main production batch plus a slightly skewed tail from over-hardened bolts.
np.random.seed(42)
sample_size = 200
main_batch = np.random.normal(loc=520, scale=35, size=int(sample_size * 0.85))
hardened_bolts = np.random.exponential(scale=18, size=int(sample_size * 0.15)) + 560
tensile_strengths = np.concatenate([main_batch, hardened_bolts])

# P-P coordinates: empirical CDF (plotting position) vs fitted-normal theoretical CDF
sorted_strengths = np.sort(tensile_strengths)
empirical_cdf = np.arange(1, len(sorted_strengths) + 1) / (len(sorted_strengths) + 1)
mu, sigma = stats.norm.fit(sorted_strengths)
theoretical_cdf = stats.norm.cdf(sorted_strengths, loc=mu, scale=sigma)
deviation = np.abs(empirical_cdf - theoretical_cdf)

df = pd.DataFrame({"theoretical": theoretical_cdf, "empirical": empirical_cdf, "deviation": deviation})

# Plot — square canvas keeps the 45-degree diagonal meaningful (6 x 6 in @ 400 dpi = 2400 x 2400 px)
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
    },
)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400)
fig.set_facecolor(PAGE_BG)
ax.set_facecolor(PAGE_BG)

# 45-degree reference line — perfect distributional fit
ax.plot([0, 1], [0, 1], color=INK_SOFT, linewidth=2.0, linestyle="--", alpha=0.7, zorder=1)

# P-P scatter, coloured by absolute deviation from the fitted normal
sns.scatterplot(
    data=df,
    x="theoretical",
    y="empirical",
    hue="deviation",
    palette=imprint_seq,
    s=45,
    alpha=0.8,
    edgecolor=PAGE_BG,
    linewidth=0.5,
    legend=False,
    zorder=2,
    ax=ax,
)

# Colorbar for the deviation encoding
norm = plt.Normalize(df["deviation"].min(), df["deviation"].max())
sm = plt.cm.ScalarMappable(cmap=imprint_seq, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.6, aspect=22, pad=0.02)
cbar.set_label("Absolute deviation from normal fit", fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_xlabel("Theoretical cumulative probability (normal)", fontsize=10, color=INK)
ax.set_ylabel("Empirical cumulative probability", fontsize=10, color=INK)
ax.set_title("pp-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect("equal")
ax.grid(True, linewidth=0.8)
sns.despine(ax=ax)
for spine in ax.spines.values():
    spine.set_color(INK_SOFT)

# Save — bbox_inches stays default (None) so figsize x dpi yields the exact 2400 x 2400 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
