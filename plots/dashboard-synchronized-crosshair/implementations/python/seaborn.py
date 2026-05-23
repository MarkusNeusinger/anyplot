"""anyplot.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-23
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

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
sns.set_context("notebook", font_scale=1.0)

# Anyplot palette — canonical order: green, purple, red, sky-blue, lime, …
ANYPLOT_PALETTE = ["#009E73", "#9418DB", "#B71D27", "#16B8F3", "#99B314", "#D359A7", "#BA843E"]
sns.set_palette(ANYPLOT_PALETTE)

COLOR_PRICE = "#009E73"  # position 1
COLOR_VOLUME = "#9418DB"  # position 2
COLOR_RSI = "#B71D27"  # position 3
COLOR_OVERBOUGHT = "#B71D27"
COLOR_OVERSOLD = "#99B314"
COLOR_CROSSHAIR = "#16B8F3"

# Data — stock-like metrics over 200 trading days
np.random.seed(42)
n_points = 200
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

price_returns = np.random.randn(n_points) * 0.02
price = 100 * np.cumprod(1 + price_returns)
volume = np.abs(price_returns) * 1e8 + np.random.exponential(5e6, n_points)
rsi = np.clip(50 + np.cumsum(np.random.randn(n_points) * 3), 20, 80)
ma20 = pd.Series(price).rolling(20, min_periods=1).mean().values

df = pd.DataFrame({"date": dates, "price": price, "volume": volume, "rsi": rsi, "ma20": ma20})

# Crosshair position for static demonstration
crosshair_idx = 120
crosshair_date = df["date"].iloc[crosshair_idx]
crosshair_price = df["price"].iloc[crosshair_idx]
crosshair_volume = df["volume"].iloc[crosshair_idx]
crosshair_rsi = df["rsi"].iloc[crosshair_idx]

# Figure: 3 stacked panels sharing x-axis (landscape 3200×1800)
fig, axes = plt.subplots(
    3, 1, figsize=(8, 4.5), dpi=400, sharex=True, facecolor=PAGE_BG, gridspec_kw={"height_ratios": [2, 1, 1]}
)
ax1, ax2, ax3 = axes

# Chart 1: Price — line with 20-day moving average and area fill
ax1.set_facecolor(PAGE_BG)
sns.lineplot(data=df, x="date", y="price", ax=ax1, color=COLOR_PRICE, linewidth=2.0, errorbar=None, label="Price")
sns.lineplot(
    data=df,
    x="date",
    y="ma20",
    ax=ax1,
    color=INK_SOFT,
    linewidth=1.0,
    linestyle="--",
    alpha=0.7,
    errorbar=None,
    label="20-day MA",
)
ax1.fill_between(df["date"], df["price"], alpha=0.15, color=COLOR_PRICE)
ax1.axvline(x=crosshair_date, color=COLOR_CROSSHAIR, linewidth=1.2, linestyle="--", alpha=0.85)
ax1.scatter(
    [crosshair_date], [crosshair_price], s=60, color=COLOR_CROSSHAIR, zorder=5, edgecolors=PAGE_BG, linewidth=0.8
)
ax1.annotate(
    f"${crosshair_price:.2f}",
    xy=(crosshair_date, crosshair_price),
    xytext=(6, 6),
    textcoords="offset points",
    fontsize=9,
    fontweight="bold",
    color="white",
    bbox={"boxstyle": "round,pad=0.25", "facecolor": COLOR_CROSSHAIR, "edgecolor": "none", "alpha": 0.92},
)
ax1.set_ylabel("Price ($)", fontsize=10, color=INK)
ax1.tick_params(axis="y", labelsize=8)
ax1.tick_params(bottom=False)
ax1.legend(loc="upper left", fontsize=8, framealpha=0.9)
sns.despine(ax=ax1, bottom=True)
ax1.spines["left"].set_color(INK_SOFT)
ax1.yaxis.grid(True, alpha=0.10, linewidth=0.6)

# Chart 2: Volume — seaborn line plot with area fill
ax2.set_facecolor(PAGE_BG)
sns.lineplot(data=df, x="date", y="volume", ax=ax2, color=COLOR_VOLUME, linewidth=1.5, errorbar=None)
ax2.fill_between(df["date"], df["volume"], alpha=0.22, color=COLOR_VOLUME)
ax2.axvline(x=crosshair_date, color=COLOR_CROSSHAIR, linewidth=1.2, linestyle="--", alpha=0.85)
ax2.scatter(
    [crosshair_date], [crosshair_volume], s=60, color=COLOR_CROSSHAIR, zorder=5, edgecolors=PAGE_BG, linewidth=0.8
)
ax2.annotate(
    f"{crosshair_volume / 1e6:.1f}M",
    xy=(crosshair_date, crosshair_volume),
    xytext=(6, 6),
    textcoords="offset points",
    fontsize=9,
    fontweight="bold",
    color="white",
    bbox={"boxstyle": "round,pad=0.25", "facecolor": COLOR_CROSSHAIR, "edgecolor": "none", "alpha": 0.92},
)
ax2.set_ylabel("Volume", fontsize=10, color=INK)
ax2.tick_params(axis="y", labelsize=8)
ax2.tick_params(bottom=False)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x / 1e6:.0f}M"))
sns.despine(ax=ax2, bottom=True)
ax2.spines["left"].set_color(INK_SOFT)
ax2.yaxis.grid(True, alpha=0.10, linewidth=0.6)

# Chart 3: RSI indicator with overbought/oversold reference bands
ax3.set_facecolor(PAGE_BG)
sns.lineplot(data=df, x="date", y="rsi", ax=ax3, color=COLOR_RSI, linewidth=2.0, errorbar=None)
ax3.axhline(y=70, color=COLOR_OVERBOUGHT, linestyle=":", linewidth=1.2, alpha=0.85, label="Overbought (70)")
ax3.axhline(y=30, color=COLOR_OVERSOLD, linestyle=":", linewidth=1.2, alpha=0.85, label="Oversold (30)")
ax3.fill_between(df["date"], 30, 70, alpha=0.08, color=INK_SOFT)
ax3.set_ylim(15, 85)
ax3.axvline(x=crosshair_date, color=COLOR_CROSSHAIR, linewidth=1.2, linestyle="--", alpha=0.85)
ax3.scatter([crosshair_date], [crosshair_rsi], s=60, color=COLOR_CROSSHAIR, zorder=5, edgecolors=PAGE_BG, linewidth=0.8)
ax3.annotate(
    f"{crosshair_rsi:.1f}",
    xy=(crosshair_date, crosshair_rsi),
    xytext=(6, 6),
    textcoords="offset points",
    fontsize=9,
    fontweight="bold",
    color="white",
    bbox={"boxstyle": "round,pad=0.25", "facecolor": COLOR_CROSSHAIR, "edgecolor": "none", "alpha": 0.92},
)
ax3.set_ylabel("RSI", fontsize=10, color=INK)
ax3.set_xlabel("Date", fontsize=10, color=INK)
ax3.tick_params(axis="both", labelsize=8)
ax3.legend(loc="upper right", fontsize=8, framealpha=0.9)
sns.despine(ax=ax3)
ax3.spines["left"].set_color(INK_SOFT)
ax3.spines["bottom"].set_color(INK_SOFT)
ax3.yaxis.grid(True, alpha=0.10, linewidth=0.6)

# X-axis date formatting on bottom panel only
ax3.xaxis.set_major_locator(plt.MaxNLocator(6))
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=30, ha="right")

# Title
fig.suptitle(
    "dashboard-synchronized-crosshair · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK
)

fig.subplots_adjust(top=0.93, bottom=0.12, left=0.12, right=0.97, hspace=0.10)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
