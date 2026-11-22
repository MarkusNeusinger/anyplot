""" anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per sector in order
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

# Columns: set these to your table's column names
DIM1 = "Market Cap Similarity (Dim 1)"  # role: x
DIM2 = "Growth Profile (Dim 2)"  # role: y
TICKER = "Ticker"  # role: label
SECTOR = "Sector"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("embedding.csv")
rng = np.random.default_rng(42)
tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "NFLX",
    "COIN", "RIOT",
    "JPM", "BAC", "GS", "WFC",
    "XOM", "CVX",
    "JNJ", "PFE", "AbbV", "MRK",
    "WMT", "TGT", "AZO", "HD",
]  # fmt: skip
base_x = np.array(
    [-2.5, -2.0, -2.2, -2.8, -1.8, -1.2, -1.5, -0.8, 0.2, 1.2, 2.5, 2.8]
    + [3.2, 3.0, -0.5, 0.3, 1.5, 1.8, 2.0, 2.3, 0.8, 1.0, 2.5, 0.2]
)
base_y = np.array(
    [3.5, 3.2, 2.8, 3.8, 4.0, 3.0, 2.5, 2.2, 1.8, 0.5, -3.0, -3.5]
    + [-2.8, -3.2, -2.5, -2.0, -1.5, -1.2, -0.8, -1.0, 1.0, 0.3, 1.5, 0.8]
)
df = pd.DataFrame(
    {
        DIM1: base_x + rng.uniform(-0.15, 0.15, len(base_x)),
        DIM2: base_y + rng.uniform(-0.15, 0.15, len(base_y)),
        TICKER: tickers,
        SECTOR: ["Technology"] * 8 + ["Cryptocurrency"] * 2 + ["Finance"] * 4 + ["Energy"] * 2
        + ["Healthcare"] * 4 + ["Retail"] * 4,
    }
)  # fmt: skip

# Plot: reads only df and the constants above
sectors = list(dict.fromkeys(df[SECTOR]))
sector_color = {sector: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, sector in enumerate(sectors)}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Each label is anchored at its exact (x, y) value; translucency keeps overlaps readable
for x, y, ticker, sector in zip(df[DIM1], df[DIM2], df[TICKER], df[SECTOR], strict=True):
    ax.text(
        x, y, ticker, fontsize=9, fontweight="bold", ha="center", va="center", color=sector_color[sector], alpha=0.9
    )

# Style
ax.set_xlabel(DIM1, fontsize=10)
ax.set_ylabel(DIM2, fontsize=10)
ax.set_title("scatter-text · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium")
ax.tick_params(axis="both", labelsize=8)
ax.yaxis.grid(True, linewidth=0.8)
sns.despine(ax=ax)

legend_elements = [
    Line2D([0], [0], marker="o", color="none", markerfacecolor=color, markersize=6, label=sector)
    for sector, color in sector_color.items()
]
ax.legend(handles=legend_elements, title=SECTOR, loc="lower left", framealpha=0.95, fontsize=8, title_fontsize=9)

ax.set_xlim(df[DIM1].min() - 0.8, df[DIM1].max() + 0.8)
ax.set_ylim(df[DIM2].min() - 0.8, df[DIM2].max() + 0.8)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
