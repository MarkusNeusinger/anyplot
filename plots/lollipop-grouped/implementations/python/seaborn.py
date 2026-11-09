"""anyplot.ai
lollipop-grouped: Grouped Lollipop Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
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

# Imprint palette: all eight positions, one per series in order (first series always #009E73)
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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
REGION = "Region"  # role: category
PRODUCT_LINE = "Product line"  # role: series
REVENUE = "Revenue (M$)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
np.random.seed(42)
base_values = {"Electronics": 50, "Clothing": 35, "Food": 25}
rows = []
for region in ["North", "South", "East", "West"]:
    for line, base in base_values.items():
        rows.append({REGION: region, PRODUCT_LINE: line, REVENUE: base + np.random.uniform(-15, 25)})
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
# Regions sorted by total revenue, product lines kept in the data's order
regions = df.groupby(REGION, sort=False)[REVENUE].sum().sort_values(ascending=False).index.tolist()
lines = df[PRODUCT_LINE].drop_duplicates().tolist()
n_lines = len(lines)
step = 0.75 / n_lines
offsets = {line: (i - (n_lines - 1) / 2) * step for i, line in enumerate(lines)}

plot_df = df.dropna(subset=[REVENUE]).copy()
plot_df["x"] = plot_df[REGION].map({r: i for i, r in enumerate(regions)}) + plot_df[PRODUCT_LINE].map(offsets)
colors = {line: IMPRINT_PALETTE[i] for i, line in enumerate(lines)}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Stems from the shared zero baseline
ax.vlines(plot_df["x"], 0, plot_df[REVENUE], colors=plot_df[PRODUCT_LINE].map(colors), linewidth=1.4, zorder=1)

# Markers via seaborn, one hue per product line
sns.scatterplot(
    data=plot_df,
    x="x",
    y=REVENUE,
    hue=PRODUCT_LINE,
    hue_order=lines,
    palette=IMPRINT_PALETTE[:n_lines],
    s=80,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    zorder=2,
    ax=ax,
)

# Style
ax.set_title("lollipop-grouped · python · seaborn · anyplot.ai", fontsize=12, color=INK)
ax.set_xticks(range(len(regions)), regions)
ax.set_xlim(-0.6, len(regions) - 0.4)
ax.set_ylim(0, plot_df[REVENUE].max() * 1.15)
ax.set_xlabel(REGION, fontsize=10)
ax.set_ylabel(REVENUE, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.tick_params(axis="x", length=0)
ax.yaxis.grid(True, linewidth=0.6)
ax.set_axisbelow(True)
sns.despine(ax=ax)

legend = ax.legend(title=PRODUCT_LINE, fontsize=8, title_fontsize=8, loc="upper right", frameon=True)
legend.get_frame().set_linewidth(0.6)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
