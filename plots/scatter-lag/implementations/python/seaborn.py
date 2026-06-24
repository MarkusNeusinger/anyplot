"""anyplot.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: seaborn 0.13.2 | Python 3.14.3
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential cmap for temporal index (single-polarity continuous)
midpoint_seq = ["#009E73", "#4467A3"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", midpoint_seq)

# Data — AR(1) with extreme positive autocorrelation (phi=0.9, n=1500)
np.random.seed(42)
n = 1500
phi = 0.9
noise = np.random.normal(0, 1, n)
values = np.zeros(n)
values[0] = noise[0]
for t in range(1, n):
    values[t] = phi * values[t - 1] + noise[t]

lag = 1
y_t = values[:-lag]
y_t_lag = values[lag:]
time_index = np.arange(len(y_t))

df = pd.DataFrame({"y(t)": y_t, "y(t+1)": y_t_lag, "Time Index": time_index})
r = np.corrcoef(y_t, y_t_lag)[0, 1]

# Theme-adaptive chrome
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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.patch.set_facecolor(PAGE_BG)
ax.set_facecolor(PAGE_BG)

scatter = ax.scatter(
    df["y(t)"], df["y(t+1)"], c=df["Time Index"], cmap=imprint_seq, s=8, alpha=0.35, edgecolors="none", zorder=3
)

# Diagonal reference line (y = x) using theme-adaptive neutral
data_min = min(y_t.min(), y_t_lag.min())
data_max = max(y_t.max(), y_t_lag.max())
margin = (data_max - data_min) * 0.04
ax.plot(
    [data_min - margin, data_max + margin],
    [data_min - margin, data_max + margin],
    color=INK_SOFT,
    linewidth=1.5,
    linestyle="--",
    alpha=0.65,
    zorder=2,
)

# Colorbar for temporal structure
cbar = plt.colorbar(scatter, ax=ax, pad=0.02, aspect=28)
cbar.set_label("Time Index", fontsize=8, color=INK_SOFT)
cbar.ax.tick_params(labelsize=7, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)
cbar.outline.set_linewidth(0.5)

# Correlation coefficient annotation
ax.annotate(
    f"r = {r:.2f}",
    xy=(0.04, 0.95),
    xycoords="axes fraction",
    fontsize=9,
    fontweight="bold",
    color=INK,
    ha="left",
    va="top",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9, "linewidth": 0.8},
)

ax.set_title("scatter-lag · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=12)
ax.set_xlabel("y(t)", fontsize=10, color=INK)
ax.set_ylabel("y(t+1)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.grid(True, alpha=0.15, linewidth=0.6, color=INK)
sns.despine(ax=ax)

fig.subplots_adjust(left=0.09, right=0.91, top=0.93, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
