"""anyplot.ai
facet-grid: Faceted Grid Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-13
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import MaxNLocator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: first series is always brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Setup theme
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
        "grid.color": INK_MUTED,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
COST = "Production Cost ($)"  # role: x
MARGIN = "Profit Margin (%)"  # role: y
PRODUCT_LINE = "Product Line"  # role: row_facet
MONTH = "Month"  # role: col_facet

# Data: replace this block with your own table, for example df = pd.read_csv("margins.csv")
np.random.seed(42)
product_lines = ["Electronics", "Apparel", "Food"]
months = ["Jan", "Feb", "Mar", "Apr"]
n_points = 30

rows = []
for product_idx, product in enumerate(product_lines):
    for month_idx, month in enumerate(months):
        # Margin level rises with the product line index; cost level rises with the month (seasonality)
        base_margin = 15 + 10 * product_idx
        margin_noise = np.random.normal(0, 3, n_points)
        base_cost = 800 + 200 * month_idx
        cost = base_cost + np.random.uniform(-100, 100, n_points)
        margin = np.clip(base_margin + 0.01 * (cost - base_cost) + margin_noise, 5, 40)
        rows.append(pd.DataFrame({COST: cost, MARGIN: margin, PRODUCT_LINE: product, MONTH: month}))

df = pd.concat(rows, ignore_index=True)

# Plot
n_cols = df[MONTH].nunique()
n_rows = df[PRODUCT_LINE].nunique()
panel_h = 4.5 / n_rows
g = sns.FacetGrid(
    df, row=PRODUCT_LINE, col=MONTH, height=panel_h, aspect=8 / (n_cols * panel_h), margin_titles=True, despine=True
)
g.figure.set_dpi(400)
g.figure.set_size_inches(8, 4.5)

g.map_dataframe(
    sns.regplot,
    x=COST,
    y=MARGIN,
    scatter_kws={"color": IMPRINT_PALETTE[0], "s": 14, "alpha": 0.75, "edgecolor": PAGE_BG, "linewidths": 0.3},
    line_kws={"color": INK_SOFT, "linewidth": 1.2, "alpha": 0.7},
    ci=None,
)

# Facet labels: month across the top, product line down the right
g.set_titles(row_template="{row_name}", col_template="{col_name}", size=9, fontweight="medium")

for ax in g.axes.flat:
    ax.tick_params(axis="both", labelsize=7, length=2, pad=1.5)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=3))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.grid(True, alpha=0.12, linestyle="-", linewidth=0.5)

# Axis titles once for the whole figure
g.set_axis_labels(COST, MARGIN, fontsize=9)

title = "facet-grid · python · seaborn · anyplot.ai"
g.figure.suptitle(title, fontsize=12, fontweight="medium", color=INK)
g.figure.subplots_adjust(left=0.07, right=0.93, bottom=0.11, top=0.88, wspace=0.12, hspace=0.3)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
