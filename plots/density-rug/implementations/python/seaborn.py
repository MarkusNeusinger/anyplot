""" anyplot.ai
density-rug: Density Plot with Rug Marks
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Seaborn theme
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

# Columns: set these to your table's column names
ERROR = "Measurement Error (μm)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("errors.csv")
# Sensor measurement errors: mostly small, a few large (exponential decay plus noise, clipped to 0-80)
np.random.seed(17)
errors = np.random.exponential(scale=15, size=250)
errors = errors + np.random.normal(0, 2, size=250)
df = pd.DataFrame({ERROR: np.clip(errors, 0, 80)})

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.kdeplot(data=df, x=ERROR, ax=ax, fill=True, alpha=0.35, color=IMPRINT_PALETTE[0], linewidth=1.8, bw_adjust=0.9)
sns.rugplot(data=df, x=ERROR, ax=ax, color=IMPRINT_PALETTE[0], alpha=0.5, height=0.04, linewidth=0.7)

# Style
ax.set_title("density-rug · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(ERROR, fontsize=10, color=INK)
ax.set_ylabel("Density", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.5, color=INK)
ax.set_axisbelow(True)
sns.despine(ax=ax)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
