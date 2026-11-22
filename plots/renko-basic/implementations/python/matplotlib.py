"""anyplot.ai
renko-basic: Basic Renko Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BULLISH = IMPRINT_PALETTE[0]  # green: price up
BEARISH = IMPRINT_PALETTE[4]  # red: price down

# Constants
BRICK_SIZE = 2.0  # price movement that draws one brick
BRICK_GAP = 0.12  # share of a column left empty between neighbouring bricks

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_points = 200
returns = np.random.normal(0.001, 0.02, n_points)
df = pd.DataFrame({DATE: pd.bdate_range("2024-01-02", periods=n_points), CLOSE: 100 * np.cumprod(1 + returns)})

# Plot: reads only df and the constants above
# Renko construction: a brick is added only when the close moves a full brick beyond the last brick
closes = df[CLOSE].to_numpy()
last_top = np.floor(closes[0] / BRICK_SIZE) * BRICK_SIZE
last_bottom = last_top
bottoms, bullish = [], []
for close in closes:
    while close >= last_top + BRICK_SIZE:
        bottoms.append(last_top)
        bullish.append(True)
        last_bottom, last_top = last_top, last_top + BRICK_SIZE
    while close <= last_bottom - BRICK_SIZE:
        bottoms.append(last_bottom - BRICK_SIZE)
        bullish.append(False)
        last_top, last_bottom = last_bottom, last_bottom - BRICK_SIZE

bricks = pd.DataFrame({"bottom": bottoms, "bullish": bullish})
bricks["index"] = np.arange(1, len(bricks) + 1)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for is_bullish, label in ((True, "Bullish (price up)"), (False, "Bearish (price down)")):
    rows = bricks[bricks["bullish"] == is_bullish]
    ax.bar(
        rows["index"],
        BRICK_SIZE,
        bottom=rows["bottom"],
        width=1 - BRICK_GAP,
        color=BULLISH if is_bullish else BEARISH,
        edgecolor=PAGE_BG,
        linewidth=0.6,
        label=label,
        zorder=3,
    )

ax.set_xlim(0, len(bricks) + 1)
ax.set_ylim(bricks["bottom"].min() - BRICK_SIZE, bricks["bottom"].max() + 5 * BRICK_SIZE)
ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True, nbins=12))

title = "renko-basic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel("Brick index", fontsize=10, color=INK)
ax.set_ylabel(CLOSE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)

leg = ax.legend(loc="upper left", fontsize=8)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
