"""anyplot.ai
subplot-grid: Subplot Grid Layout
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions; up days take green, down days the semantic red
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
UP, DOWN = IMPRINT_PALETTE[0], IMPRINT_PALETTE[4]
imprint_div = LinearSegmentedColormap.from_list("imprint_div", [IMPRINT_PALETTE[4], PAGE_BG, IMPRINT_PALETTE[2]])

# Constants
MA_WINDOW = 20  # trading days in the moving average

# Columns: set these to your table's column names
DAY = "Trading day"  # role: x
PRICE = "Price (USD)"  # role: y
VOLUME = "Volume (thousand shares)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("stock.csv")
# 100 trading days of one stock: a random-walk price with slight drift and lognormal volume
np.random.seed(42)
price_changes = np.random.randn(100) * 2 + 0.05
volumes = np.random.lognormal(mean=10, sigma=0.5, size=100)
df = pd.DataFrame({DAY: np.arange(1, 101), PRICE: 100 + np.cumsum(price_changes), VOLUME: volumes / 1000})

# Plot: reads only df and the constants above
days = df.sort_values(DAY)
returns = days[PRICE].pct_change() * 100
moving_average = days[PRICE].rolling(MA_WINDOW).mean()
day_colors = np.where(returns < 0, DOWN, UP)
spread = np.nanmax(np.abs(returns))

fig, axes = plt.subplots(2, 2, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, layout="constrained")
(price_ax, volume_ax), (hist_ax, scatter_ax) = axes
volume_ax.sharex(price_ax)  # both top cells plot the same trading days; the bottom cells keep independent axes

# Stock price with its moving average
price_ax.plot(days[DAY], days[PRICE], color=IMPRINT_PALETTE[0], linewidth=1.8, label="Close")
price_ax.plot(
    days[DAY],
    moving_average,
    color=IMPRINT_PALETTE[1],
    linewidth=1.6,
    linestyle=(0, (4, 2)),
    label=f"{MA_WINDOW}-day MA",
)
price_ax.set_title("Stock price", fontsize=10, fontweight="bold", color=INK, loc="left")
price_ax.set_xlabel(DAY, fontsize=9, color=INK)
price_ax.set_ylabel(PRICE, fontsize=9, color=INK)
price_ax.legend(loc="best", fontsize=8)

# Daily volume, coloured by the direction of the day's price move
volume_ax.bar(days[DAY], days[VOLUME], width=0.8, color=day_colors, linewidth=0)
volume_ax.set_title("Trading volume", fontsize=10, fontweight="bold", color=INK, loc="left")
volume_ax.set_xlabel(DAY, fontsize=9, color=INK)
volume_ax.set_ylabel(VOLUME, fontsize=9, color=INK)
volume_ax.set_ylim(0, days[VOLUME].max() * 1.25)
volume_ax.legend(
    handles=[Patch(color=UP, label="Up day"), Patch(color=DOWN, label="Down day")],
    loc="upper left",
    ncols=2,
    fontsize=8,
)

# Distribution of daily returns
hist_ax.hist(returns.dropna(), bins=20, color=IMPRINT_PALETTE[0], edgecolor=PAGE_BG, linewidth=0.8)
hist_ax.axvline(0, color=INK_SOFT, linewidth=1.0, label="Zero return")
hist_ax.axvline(
    returns.mean(), color=IMPRINT_PALETTE[1], linewidth=1.6, linestyle=(0, (4, 2)), label=f"Mean {returns.mean():.2f}%"
)
hist_ax.set_title("Return distribution", fontsize=10, fontweight="bold", color=INK, loc="left")
hist_ax.set_xlabel("Daily return (%)", fontsize=9, color=INK)
hist_ax.set_ylabel("Trading days", fontsize=9, color=INK)
hist_ax.set_ylim(0, hist_ax.get_ylim()[1] * 1.3)  # headroom keeps the legend clear of the tallest bins
hist_ax.yaxis.set_major_locator(MaxNLocator(integer=True))
hist_ax.legend(loc="best", fontsize=8)

# Volume against the size of the day's move, coloured by its sign
points = scatter_ax.scatter(
    days[VOLUME],
    returns.abs(),
    c=returns,
    cmap=imprint_div,
    norm=TwoSlopeNorm(vcenter=0, vmin=-spread, vmax=spread),
    s=22,
    edgecolors=INK_SOFT,
    linewidths=0.4,
)
scatter_ax.set_title("Volume vs return size", fontsize=10, fontweight="bold", color=INK, loc="left")
scatter_ax.set_xlabel(VOLUME, fontsize=9, color=INK)
scatter_ax.set_ylabel("Absolute daily return (%)", fontsize=9, color=INK)
cbar = fig.colorbar(points, ax=scatter_ax, pad=0.02, aspect=14)
cbar.set_label("Daily return (%)", fontsize=8, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, length=0)
cbar.outline.set_visible(False)

# Style
fig.suptitle("subplot-grid · python · matplotlib · anyplot.ai", fontsize=12, fontweight="bold", color=INK)
for ax in axes.flat:
    ax.set_facecolor(PAGE_BG)
    ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
    ax.grid(True, axis="y" if ax is not scatter_ax else "both", alpha=0.15, color=INK, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_SOFT)
    legend = ax.get_legend()
    if legend:
        legend.get_frame().set_facecolor(ELEVATED_BG)
        legend.get_frame().set_edgecolor(INK_SOFT)
        legend.get_frame().set_linewidth(0.6)
        plt.setp(legend.get_texts(), color=INK_SOFT)
fig.get_layout_engine().set(h_pad=0.06, w_pad=0.08, hspace=0.04, wspace=0.04)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
