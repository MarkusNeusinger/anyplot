"""anyplot.ai
line-confidence: Line Plot with Confidence Interval
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-09
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

# Imprint palette: position 1 is the single series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
TIME = "Discharge time (min)"  # role: x
VOLTAGE = "Cell voltage (V)"  # role: y
LOWER = "Lower bound (V)"  # role: y_lower
UPPER = "Upper bound (V)"  # role: y_upper

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
# Predicted Li-ion cell voltage under constant load, 95% interval from a model ensemble
rng = np.random.default_rng(42)
minutes = np.arange(0, 181, 6)
predicted = 4.15 - 0.0022 * minutes - 0.55 * np.exp((minutes - 180) / 22) + rng.normal(0, 0.006, len(minutes))
half_width = 1.96 * (0.008 + 0.00022 * minutes)  # the ensemble spreads out with discharge time
df = pd.DataFrame({TIME: minutes, VOLTAGE: predicted, LOWER: predicted - half_width, UPPER: predicted + half_width})

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

ax.fill_between(df[TIME], df[LOWER], df[UPPER], color=BRAND, alpha=0.25, linewidth=0, label="95% prediction interval")
sns.lineplot(
    data=df, x=TIME, y=VOLTAGE, color=BRAND, linewidth=2, marker="o", markersize=3.5, label="Predicted voltage", ax=ax
)

# Style
title = "Battery Discharge Forecast · line-confidence · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=round(12 * min(1.0, 67 / len(title))), fontweight="medium", color=INK)
ax.set_xlabel(TIME, fontsize=10)
ax.set_ylabel(VOLTAGE, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.yaxis.grid(True, linewidth=0.8)
ax.set_axisbelow(True)
sns.despine(ax=ax)

# Band first in the legend, then the line
handles, labels = ax.get_legend_handles_labels()
order = [labels.index("95% prediction interval"), labels.index("Predicted voltage")]
ax.legend([handles[i] for i in order], [labels[i] for i in order], fontsize=8, loc="lower left", framealpha=0.95)

ax.set_xlim(df[TIME].min(), df[TIME].max())
pad = 0.04 * (df[UPPER].max() - df[LOWER].min())
ax.set_ylim(df[LOWER].min() - pad, df[UPPER].max() + pad)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
