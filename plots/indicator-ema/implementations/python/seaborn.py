""" anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
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

# Imprint palette: canonical order, first series always #009E73
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
DATE = "Date"  # role: date
CLOSE = "Close Price"  # role: close
EMA_SHORT = "EMA 12"  # role: ema_short
EMA_LONG = "EMA 26"  # role: ema_long

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 150
returns = np.random.normal(0.001, 0.025, n_days)
close = 200 * np.cumprod(1 + returns)
df = pd.DataFrame(
    {
        DATE: pd.date_range(start="2024-03-01", periods=n_days, freq="B"),
        CLOSE: close,
        EMA_SHORT: pd.Series(close).ewm(span=12, adjust=False).mean().values,
        EMA_LONG: pd.Series(close).ewm(span=26, adjust=False).mean().values,
    }
)

# Plot: reads only df and the constants above
series = [CLOSE, EMA_SHORT, EMA_LONG]
palette = dict(zip(series, IMPRINT_PALETTE[: len(series)], strict=False))
line_widths = [1.75] + [1.25] * (len(series) - 1)

# Crossovers: where the short EMA moves across the long one
prev_gap = (df[EMA_SHORT] - df[EMA_LONG]).shift(1)
gap = df[EMA_SHORT] - df[EMA_LONG]
cross_up = (prev_gap < 0) & (gap > 0)
cross_down = (prev_gap > 0) & (gap < 0)

df_long = df.melt(id_vars=[DATE], value_vars=series, var_name="series", value_name="price")

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(data=df_long, x=DATE, y="price", hue="series", hue_order=series, palette=palette, ax=ax)

# Price thicker, EMAs thinner
for line, lw in zip(ax.get_lines(), line_widths, strict=False):
    line.set_linewidth(lw)

# Crossover markers: up triangle (short EMA crosses above), down triangle (crosses below)
ax.scatter(
    df.loc[cross_up, DATE],
    df.loc[cross_up, EMA_SHORT],
    color=IMPRINT_PALETTE[0],
    s=70,
    zorder=5,
    marker="^",
    edgecolors=PAGE_BG,
    linewidth=0.5,
)
ax.scatter(
    df.loc[cross_down, DATE],
    df.loc[cross_down, EMA_SHORT],
    color=IMPRINT_PALETTE[1],
    s=70,
    zorder=5,
    marker="v",
    edgecolors=PAGE_BG,
    linewidth=0.5,
)

# Style
ax.set_title("indicator-ema · python · seaborn · anyplot.ai", fontsize=12, fontweight="bold", pad=10, color=INK)
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel("Price (USD)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
fig.autofmt_xdate(rotation=30)

legend = ax.legend(fontsize=8, loc="upper right")
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
for text in legend.get_texts():
    text.set_color(INK)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.set_axisbelow(True)
sns.despine(ax=ax)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.98, top=0.92, bottom=0.2)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
