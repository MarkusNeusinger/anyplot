"""anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import to_rgb


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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
SWARM_DARKEN = 0.65  # swarm points are the violin hue scaled toward black, for contrast on the translucent fill

# Columns: set these to your table's column names
CELL_TYPE = "Cell Type"  # role: category
EXPRESSION = "Expression Level"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("expression.csv")
np.random.seed(42)
n_per_type = 60
df = pd.DataFrame(
    {
        CELL_TYPE: np.repeat(["Neuron", "Astrocyte", "Oligodendrocyte", "Microglia"], n_per_type),
        EXPRESSION: np.concatenate(
            [
                np.random.normal(85, 12, n_per_type),
                np.random.normal(72, 15, n_per_type),
                # Bimodal: two sub-populations
                np.concatenate([np.random.normal(55, 10, n_per_type // 2), np.random.normal(92, 8, n_per_type // 2)]),
                np.random.normal(65, 14, n_per_type),
            ]
        ),
    }
)

# Plot
n_groups = df[CELL_TYPE].nunique()
violin_colors = IMPRINT_PALETTE[:n_groups]
swarm_colors = [tuple(c * SWARM_DARKEN for c in to_rgb(color)) for color in violin_colors]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Translucent violin so the swarm stays visible on top
sns.violinplot(
    data=df,
    x=CELL_TYPE,
    y=EXPRESSION,
    hue=CELL_TYPE,
    palette=violin_colors,
    alpha=0.4,
    inner=None,
    cut=0,
    linewidth=1.0,
    legend=False,
    ax=ax,
)

# Swarm of individual observations, darker shade of each violin hue
sns.swarmplot(
    data=df,
    x=CELL_TYPE,
    y=EXPRESSION,
    hue=CELL_TYPE,
    palette=swarm_colors,
    size=3.5,
    edgecolor=INK,
    linewidth=0.3,
    legend=False,
    ax=ax,
)

# Style
ax.set_title("violin-swarm · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(CELL_TYPE, fontsize=10)
ax.set_ylabel(EXPRESSION, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.set_axisbelow(True)
sns.despine(ax=ax)

fig.tight_layout()
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
