""" anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-19
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

# Okabe-Ito palette — positions 1, 2, 3
OKABE = ["#009E73", "#C475FD", "#4467A3"]

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

# Data — $200 starting price with higher volatility to diverge from sibling impls
np.random.seed(42)
n_days = 150
dates = pd.date_range(start="2024-03-01", periods=n_days, freq="B")
returns = np.random.normal(0.001, 0.025, n_days)
price = 200 * np.cumprod(1 + returns)

price_series = pd.Series(price)
ema_12 = price_series.ewm(span=12, adjust=False).mean().values
ema_26 = price_series.ewm(span=26, adjust=False).mean().values

df = pd.DataFrame({"date": dates, "Close Price": price, "EMA 12": ema_12, "EMA 26": ema_26})

# Crossover detection before melting
cross_up = (df["EMA 12"].shift(1) < df["EMA 26"].shift(1)) & (df["EMA 12"] > df["EMA 26"])
cross_down = (df["EMA 12"].shift(1) > df["EMA 26"].shift(1)) & (df["EMA 12"] < df["EMA 26"])

# Long format for idiomatic seaborn hue grouping
df_long = df.melt(
    id_vars=["date"], value_vars=["Close Price", "EMA 12", "EMA 26"], var_name="series", value_name="price"
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

palette = {"Close Price": OKABE[0], "EMA 12": OKABE[1], "EMA 26": OKABE[2]}

sns.lineplot(
    data=df_long,
    x="date",
    y="price",
    hue="series",
    hue_order=["Close Price", "EMA 12", "EMA 26"],
    palette=palette,
    ax=ax,
)

# Set linewidths: price thicker, EMAs thinner
for line, lw in zip(ax.get_lines(), [3.5, 2.5, 2.5], strict=False):
    line.set_linewidth(lw)

# Crossover markers — green up triangle (bullish), vermillion down triangle (bearish)
ax.scatter(
    df.loc[cross_up, "date"],
    df.loc[cross_up, "EMA 12"],
    color=OKABE[0],
    s=250,
    zorder=5,
    marker="^",
    edgecolors=PAGE_BG,
    linewidth=1.0,
)
ax.scatter(
    df.loc[cross_down, "date"],
    df.loc[cross_down, "EMA 12"],
    color=OKABE[1],
    s=250,
    zorder=5,
    marker="v",
    edgecolors=PAGE_BG,
    linewidth=1.0,
)

# Style
ax.set_title("indicator-ema · python · seaborn · anyplot.ai", fontsize=24, fontweight="bold", pad=20, color=INK)
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Price (USD)", fontsize=20, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

fig.autofmt_xdate(rotation=30)

# Legend — clean single entry per series from hue grouping
legend = ax.legend(fontsize=16, loc="upper left")
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
for text in legend.get_texts():
    text.set_color(INK)

# Grid — y-axis only, subtle
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
