"""anyplot.ai
renko-basic: Basic Renko Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Rectangle


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 for bullish bricks, red anchor for bearish bricks
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BULLISH = IMPRINT_PALETTE[0]
BEARISH = IMPRINT_PALETTE[4]

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
        "grid.alpha": 0.12,
        "legend.facecolor": PAGE_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
BRICK_SIZE = 0.005  # price move that adds one brick (50 pips on a forex pair)
GAP_RATIO = 0.10  # share of each column left empty between neighbouring bricks

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "EUR/USD close"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
rng = np.random.default_rng(7)
n_days = 260
daily_moves = rng.normal(0.0001, 0.0035, n_days)
df = pd.DataFrame({DATE: pd.bdate_range("2025-01-01", periods=n_days), CLOSE: 1.10 * np.cumprod(1 + daily_moves)})

# Plot: reads only df and the constants above
# Renko construction on integer price levels: a brick closes when price moves a full brick
# beyond the last brick, a reversal needs two bricks of movement.
low = high = int(np.floor(df[CLOSE].iloc[0] / BRICK_SIZE))
bricks = []
for price in df[CLOSE] / BRICK_SIZE:
    while price >= high + 1:
        low, high = high, high + 1
        bricks.append((low, "Bullish (up)"))
    while price <= low - 1:
        low, high = low - 1, low
        bricks.append((low, "Bearish (down)"))

renko = pd.DataFrame(bricks, columns=["level", "direction"])
renko["bottom"] = renko["level"] * BRICK_SIZE
renko["column"] = np.arange(len(renko))
colors = {"Bullish (up)": BULLISH, "Bearish (down)": BEARISH}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
for brick in renko.itertuples():
    ax.add_patch(
        Rectangle(
            (brick.column + GAP_RATIO / 2, brick.bottom),
            1 - GAP_RATIO,
            BRICK_SIZE,
            facecolor=colors[brick.direction],
            edgecolor="none",
        )
    )

legend_handles = [Rectangle((0, 0), 1, 1, facecolor=colors[d], edgecolor="none", label=d) for d in colors]
ax.set_xlim(-0.5, len(renko) + 0.5)
ax.set_ylim(renko["bottom"].min() - BRICK_SIZE, renko["bottom"].max() + 2 * BRICK_SIZE)

# Style
ax.set_title("renko-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(f"Brick index (one brick = {BRICK_SIZE:g} price move)", fontsize=10)
ax.set_ylabel(CLOSE, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.set_xticks(np.arange(0, len(renko), max(1, len(renko) // 10)))
ax.yaxis.set_major_formatter("{x:.3f}")
ax.yaxis.grid(True, linewidth=0.8)
ax.set_axisbelow(True)
ax.legend(handles=legend_handles, fontsize=8, loc="lower left", frameon=True)
sns.despine(ax=ax)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
