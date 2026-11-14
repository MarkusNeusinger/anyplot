"""anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Sequential Imprint colormap for the bin counts
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

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

# Constants
N_BINS = 32  # bins per axis, shared by the heatmap and both marginals

# Columns: set these to your table's column names
AGE = "Customer age (years)"  # role: x
SPENDING = "Annual spending (USD)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("customers.csv")
rng = np.random.default_rng(42)
n_customers = 6000
age = rng.normal(46, 12, n_customers)
age = age[(age >= 18) & (age <= 75)]
spending = 2800 + 45 * (age - 46) + rng.normal(0, 480, len(age))
df = pd.DataFrame({AGE: age, SPENDING: spending})

# Plot: reads only df and the constants above
g = sns.JointGrid(data=df, x=AGE, y=SPENDING, height=4.5, ratio=5, space=0.15)
g.figure.set_size_inches(8, 4.5)
g.figure.set_dpi(400)

# Heatmap of bin counts, with a count color bar
sns.histplot(
    data=df,
    x=AGE,
    y=SPENDING,
    bins=N_BINS,
    cmap=imprint_seq,
    cbar=True,
    cbar_kws={"label": "Customers per bin (count)"},
    ax=g.ax_joint,
)

# Marginals use the same bin count, so their bars sit over the bins they summarize
marginal_style = {"bins": N_BINS, "color": IMPRINT_PALETTE[0], "edgecolor": PAGE_BG, "linewidth": 0.3}
sns.histplot(data=df, x=AGE, ax=g.ax_marg_x, **marginal_style)
sns.histplot(data=df, y=SPENDING, ax=g.ax_marg_y, **marginal_style)

# Style
g.ax_joint.set_xlabel(AGE, fontsize=10, labelpad=6)
g.ax_joint.set_ylabel(SPENDING, fontsize=10, labelpad=6)
g.ax_joint.tick_params(axis="both", labelsize=8)
g.ax_marg_x.set_ylabel("")
g.ax_marg_y.set_xlabel("")
g.ax_marg_x.tick_params(axis="both", labelsize=7)
g.ax_marg_y.tick_params(axis="both", labelsize=7)

cbar = g.ax_joint.collections[0].colorbar
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.set_label("Customers per bin (count)", fontsize=9, color=INK)
cbar.outline.set_edgecolor(INK_SOFT)

g.figure.suptitle("histogram-2d · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
g.figure.subplots_adjust(left=0.09, right=0.94, bottom=0.12, top=0.92)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
