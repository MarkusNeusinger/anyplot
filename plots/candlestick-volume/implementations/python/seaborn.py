"""anyplot.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
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

# Imprint palette: position 1 (green) marks up candles, position 5 (red) marks down candles
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
UP_COLOR = IMPRINT_PALETTE[0]
DOWN_COLOR = IMPRINT_PALETTE[4]

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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
MIN_BODY_SHARE = 0.002  # a doji body is drawn at least this share of the price range tall
BODY_WIDTH = 0.7  # candle and volume bar width in trading-day units

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open ($)"  # role: open
HIGH = "High ($)"  # role: high
LOW = "Low ($)"  # role: low
CLOSE = "Close ($)"  # role: close
VOLUME = "Volume (M shares)"  # role: volume

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
rng = np.random.default_rng(7)
n_days = 70
start_price = 84.0
# Steady downtrend with a mid-series bounce, a mid-cap stock sliding after weak guidance
daily_returns = rng.normal(-0.0022, 0.016, n_days)
daily_returns[35:42] += 0.012
closes = start_price * np.cumprod(1 + daily_returns)
opens = np.concatenate([[start_price], closes[:-1]]) * (1 + rng.normal(0, 0.003, n_days))
highs = np.maximum(opens, closes) * (1 + rng.uniform(0.002, 0.014, n_days))
lows = np.minimum(opens, closes) * (1 - rng.uniform(0.002, 0.014, n_days))
volumes = rng.lognormal(mean=np.log(2.4), sigma=0.25, size=n_days) * (1 + 18 * np.abs(closes - opens) / closes)
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-03-04", periods=n_days, freq="B"),
        OPEN: opens,
        HIGH: highs,
        LOW: lows,
        CLOSE: closes,
        VOLUME: volumes,
    }
)

# Plot: reads only df and the constants above
n_periods = len(df)
df["day_idx"] = np.arange(n_periods)
df["direction"] = np.where(df[CLOSE] >= df[OPEN], "Up (Close ≥ Open)", "Down (Close < Open)")
direction_palette = {"Up (Close ≥ Open)": UP_COLOR, "Down (Close < Open)": DOWN_COLOR}

price_range = df[HIGH].max() - df[LOW].min()
body_bottom = df[[OPEN, CLOSE]].min(axis=1)
body_height = (df[OPEN] - df[CLOSE]).abs().clip(lower=price_range * MIN_BODY_SHARE)

fig, (ax_price, ax_vol) = plt.subplots(
    2, 1, figsize=(8, 4.5), dpi=400, sharex=True, height_ratios=[3, 1], gridspec_kw={"hspace": 0.06}
)

# Upper pane: wicks from low to high via seaborn, one unit per day
wicks = df.melt(id_vars=["day_idx", "direction"], value_vars=[LOW, HIGH], value_name="price")
sns.lineplot(
    data=wicks,
    x="day_idx",
    y="price",
    hue="direction",
    palette=direction_palette,
    units="day_idx",
    estimator=None,
    linewidth=1.2,
    legend=False,
    ax=ax_price,
    zorder=2,
)
# Candle bodies from open to close
ax_price.bar(
    df["day_idx"],
    body_height,
    bottom=body_bottom,
    width=BODY_WIDTH,
    color=df["direction"].map(direction_palette),
    linewidth=0,
    zorder=3,
)

# Lower pane: volume bars in the matching candle colors, from a zero baseline
sns.barplot(
    data=df,
    x="day_idx",
    y=VOLUME,
    hue="direction",
    palette=direction_palette,
    width=BODY_WIDTH,
    dodge=False,
    saturation=1,
    linewidth=0,
    legend=False,
    ax=ax_vol,
)

# Shared date axis: ticks at evenly spaced trading days
tick_idx = np.linspace(0, n_periods - 1, 7, dtype=int)
ax_vol.set_xticks(tick_idx)
ax_vol.set_xticklabels(df[DATE].dt.strftime("%b %d").iloc[tick_idx], rotation=30, ha="right")
ax_vol.set_xlim(-1, n_periods)

# Style
title = "candlestick-volume · python · seaborn · anyplot.ai"
ax_price.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=8)
ax_price.set_ylabel(CLOSE.replace("Close ", "Price "), fontsize=10)
ax_price.set_xlabel("")
ax_vol.set_ylabel(VOLUME, fontsize=10)
ax_vol.set_xlabel(DATE, fontsize=10)
for ax in (ax_price, ax_vol):
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", labelsize=8)
    ax.yaxis.grid(True, linewidth=0.6)
    sns.despine(ax=ax)
ax_price.tick_params(axis="x", length=0)

handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in direction_palette.values()]
ax_price.legend(handles, list(direction_palette), loc="upper right", fontsize=8, framealpha=0.95)

fig.subplots_adjust(left=0.09, right=0.97, top=0.92, bottom=0.15)
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
