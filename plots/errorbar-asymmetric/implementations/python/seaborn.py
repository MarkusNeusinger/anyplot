"""anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-13
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
        "grid.alpha": 0.10,
    },
)

# Constants
BOUNDS_NOTE = "10th–90th percentile"  # what the error arms represent

# Columns: set these to your table's column names
DEVICE = "Device Model"  # role: x
BATTERY = "Battery Life (hours)"  # role: y
ERROR_LOWER = "Lower error (hours)"  # role: error_lower
ERROR_UPPER = "Upper error (hours)"  # role: error_upper

# Data: replace this block with your own table, for example df = pd.read_csv("battery.csv")
# Median battery life per device model; errors are distances to the 10th and 90th percentile
df = pd.DataFrame(
    {
        DEVICE: ["Model A", "Model B", "Model C", "Model D", "Model E", "Model F", "Model G", "Model H"],
        BATTERY: [8.5, 12.3, 6.2, 15.8, 9.7, 11.2, 7.4, 14.1],
        ERROR_LOWER: [1.2, 2.5, 0.8, 3.2, 1.5, 2.0, 1.0, 2.8],
        ERROR_UPPER: [2.8, 1.5, 2.2, 1.8, 3.5, 1.2, 2.6, 1.4],
    }
)

# Plot: reads only df and the constants above
x = np.arange(len(df))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.scatterplot(x=x, y=df[BATTERY], s=110, color=IMPRINT_PALETTE[0], zorder=5, ax=ax)
ax.errorbar(
    x=x,
    y=df[BATTERY],
    yerr=[df[ERROR_LOWER], df[ERROR_UPPER]],
    fmt="none",
    ecolor=IMPRINT_PALETTE[0],
    elinewidth=1.6,
    capsize=5,
    capthick=1.6,
    zorder=4,
)

# Style
ax.set_xticks(x, df[DEVICE])
ax.set_xlabel(DEVICE, fontsize=10)
ax.set_ylabel(BATTERY, fontsize=10)
ax.set_title("errorbar-asymmetric · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8)
ax.grid(True, alpha=0.10, linestyle="-", linewidth=0.8)
sns.despine(ax=ax)

ax.annotate(
    BOUNDS_NOTE,
    xy=(0.02, 0.96),
    xycoords="axes fraction",
    fontsize=9,
    ha="left",
    va="top",
    color=INK,
    bbox={"boxstyle": "round,pad=0.5", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "linewidth": 0.8, "alpha": 0.9},
)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
