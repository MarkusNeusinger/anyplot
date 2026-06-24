"""anyplot.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: matplotlib | Python 3.14
Quality: 85/100 | Updated: 2026-06-24
"""

import os
import sys


# Remove script directory from path so "import matplotlib" finds the package, not this file
sys.path.pop(0)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential colormap for time index (single-polarity continuous)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Data — synthetic AR(1) process with strong positive autocorrelation
np.random.seed(42)
n_observations = 500
phi = 0.85
noise = np.random.normal(0, 1, n_observations)
series = np.zeros(n_observations)
series[0] = noise[0]
for i in range(1, n_observations):
    series[i] = phi * series[i - 1] + noise[i]

lag = 1
y_t = series[:-lag]
y_t_lag = series[lag:]
time_index = np.arange(len(y_t))

r_value = np.corrcoef(y_t, y_t_lag)[0, 1]

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

scatter = ax.scatter(
    y_t, y_t_lag, c=time_index, cmap=imprint_seq, s=55, alpha=0.50, edgecolors=PAGE_BG, linewidth=0.3, zorder=2
)

# Diagonal reference line (y = x)
data_min = min(y_t.min(), y_t_lag.min())
data_max = max(y_t.max(), y_t_lag.max())
margin = (data_max - data_min) * 0.05
ax.plot(
    [data_min - margin, data_max + margin],
    [data_min - margin, data_max + margin],
    color=INK_SOFT,
    linewidth=1.5,
    linestyle="--",
    alpha=0.5,
    zorder=1,
)

# Colorbar
cbar = fig.colorbar(scatter, ax=ax, pad=0.02, aspect=30)
cbar.set_label("Time Index", fontsize=10, color=INK_SOFT)
cbar.ax.tick_params(labelsize=8, labelcolor=INK_SOFT, color=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)
cbar.outline.set_linewidth(0.5)

# Correlation annotation
ax.text(
    0.04,
    0.96,
    f"r = {r_value:.3f}",
    transform=ax.transAxes,
    fontsize=10,
    verticalalignment="top",
    fontweight="medium",
    color=INK,
    bbox={"facecolor": ELEVATED_BG, "edgecolor": "none", "alpha": 0.85, "pad": 4},
)

# Style
ax.set_xlabel("y(t)", fontsize=10, color=INK)
ax.set_ylabel(f"y(t + {lag})", fontsize=10, color=INK)

title = "scatter-lag · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)

ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
