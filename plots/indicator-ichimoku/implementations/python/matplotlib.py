""" anyplot.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-06-08
"""

import os

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — semantic exception: finance up/down maps to green/red
COLOR_UP = "#009E73"  # brand green — bullish candles & cloud
COLOR_DOWN = "#AE3030"  # matte red — bearish candles & cloud
COLOR_TENKAN = "#C475FD"  # lavender — Tenkan-sen
COLOR_KIJUN = "#4467A3"  # blue — Kijun-sen
COLOR_CHIKOU = "#BD8233"  # ochre — Chikou Span

# Data — 200 trading days with uptrend → consolidation → breakdown → recovery
np.random.seed(42)
n_days = 200
dates = pd.bdate_range(start="2024-01-02", periods=n_days)

trend = np.concatenate(
    [np.linspace(0, 0.12, 60), np.linspace(0.12, 0.10, 30), np.linspace(0.10, -0.08, 50), np.linspace(-0.08, 0.02, 60)]
)
noise = np.random.randn(n_days) * 0.008
returns = np.diff(trend, prepend=trend[0]) + noise
price_series = 155 * np.exp(np.cumsum(returns))

open_prices = price_series * (1 + np.random.uniform(-0.005, 0.005, n_days))
close_prices = price_series * (1 + np.random.uniform(-0.012, 0.012, n_days))
intraday_ranges = price_series * np.random.uniform(0.008, 0.025, n_days)
low_prices = np.minimum(open_prices, close_prices) - np.random.uniform(0.2, 0.8, n_days) * intraday_ranges
high_prices = np.maximum(open_prices, close_prices) + np.random.uniform(0.2, 0.8, n_days) * intraday_ranges

df = pd.DataFrame({"date": dates, "open": open_prices, "high": high_prices, "low": low_prices, "close": close_prices})

# Ichimoku components — standard parameters (9, 26, 52)
tenkan_period, kijun_period, senkou_b_period, displacement = 9, 26, 52, 26
high_s = df["high"]
low_s = df["low"]

tenkan_sen = (high_s.rolling(tenkan_period).max() + low_s.rolling(tenkan_period).min()) / 2
kijun_sen = (high_s.rolling(kijun_period).max() + low_s.rolling(kijun_period).min()) / 2
senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
senkou_span_b = ((high_s.rolling(senkou_b_period).max() + low_s.rolling(senkou_b_period).min()) / 2).shift(displacement)
chikou_span = df["close"].shift(-displacement)

df["tenkan_sen"] = tenkan_sen
df["kijun_sen"] = kijun_sen
df["senkou_span_a"] = senkou_span_a
df["senkou_span_b"] = senkou_span_b
df["chikou_span"] = chikou_span

# Trim to last 120 days for a clean view with enough indicator history
df_plot = df.iloc[80:].reset_index(drop=True)

# Canvas — landscape 3200×1800 px (hard contract)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

date_nums = mdates.date2num(df_plot["date"])
bullish = df_plot["close"] >= df_plot["open"]
candle_colors = np.where(bullish, COLOR_UP, COLOR_DOWN)
width = 0.65

# Candlestick wicks
ax.vlines(date_nums, df_plot["low"], df_plot["high"], colors=candle_colors, linewidth=0.8, zorder=3)

# Candlestick bodies — split bullish/bearish for CVD redundant encoding
body_bottoms = np.where(bullish, df_plot["open"], df_plot["close"])
body_heights = np.abs(df_plot["close"] - df_plot["open"])
body_heights = np.where(body_heights < 0.01, 0.01, body_heights)
bullish_idx = bullish.values
# Bullish: solid fill, no special edge
ax.bar(
    date_nums[bullish_idx],
    body_heights[bullish_idx],
    bottom=body_bottoms[bullish_idx],
    width=width,
    color=COLOR_UP,
    edgecolor=COLOR_UP,
    linewidth=0.4,
    zorder=4,
)
# Bearish: dark edge stroke provides shape-based CVD cue beyond color
ax.bar(
    date_nums[~bullish_idx],
    body_heights[~bullish_idx],
    bottom=body_bottoms[~bullish_idx],
    width=width,
    color=COLOR_DOWN,
    edgecolor=INK,
    linewidth=0.9,
    zorder=4,
)

# Kumo (cloud) — filled between Senkou Span A and B
span_a = df_plot["senkou_span_a"]
span_b = df_plot["senkou_span_b"]
valid_cloud = span_a.notna() & span_b.notna()

if valid_cloud.any():
    cloud_dates = date_nums[valid_cloud]
    cloud_a = span_a[valid_cloud].values
    cloud_b = span_b[valid_cloud].values

    ax.fill_between(
        cloud_dates, cloud_a, cloud_b, where=cloud_a >= cloud_b, color=COLOR_UP, alpha=0.18, interpolate=True, zorder=1
    )
    ax.fill_between(
        cloud_dates, cloud_a, cloud_b, where=cloud_a < cloud_b, color=COLOR_DOWN, alpha=0.18, interpolate=True, zorder=1
    )
    ax.plot(cloud_dates, cloud_a, color=COLOR_UP, linewidth=0.8, alpha=0.5, zorder=2)
    ax.plot(cloud_dates, cloud_b, color=COLOR_DOWN, linewidth=0.8, alpha=0.5, zorder=2)

# Tenkan-sen
tenkan_valid = df_plot["tenkan_sen"].notna()
ax.plot(
    date_nums[tenkan_valid],
    df_plot["tenkan_sen"][tenkan_valid],
    color=COLOR_TENKAN,
    linewidth=1.5,
    alpha=0.9,
    zorder=5,
    label="Tenkan-sen (9)",
)

# Kijun-sen
kijun_valid = df_plot["kijun_sen"].notna()
ax.plot(
    date_nums[kijun_valid],
    df_plot["kijun_sen"][kijun_valid],
    color=COLOR_KIJUN,
    linewidth=1.5,
    alpha=0.9,
    zorder=5,
    label="Kijun-sen (26)",
)

# Chikou Span (lagging, plotted 26 periods in the past)
chikou_valid = df_plot["chikou_span"].notna()
ax.plot(
    date_nums[chikou_valid],
    df_plot["chikou_span"][chikou_valid],
    color=COLOR_CHIKOU,
    linewidth=1.2,
    alpha=0.65,
    linestyle="--",
    zorder=2,
    label="Chikou Span",
)

# TK crossover signals
tenkan_vals = df_plot["tenkan_sen"].values
kijun_vals = df_plot["kijun_sen"].values
for i in range(1, len(df_plot)):
    if np.isnan(tenkan_vals[i]) or np.isnan(kijun_vals[i]):
        continue
    if np.isnan(tenkan_vals[i - 1]) or np.isnan(kijun_vals[i - 1]):
        continue
    if tenkan_vals[i - 1] >= kijun_vals[i - 1] and tenkan_vals[i] < kijun_vals[i]:
        ax.annotate(
            "TK↓",
            xy=(date_nums[i], kijun_vals[i]),
            fontsize=6,
            fontweight="bold",
            color=COLOR_DOWN,
            ha="center",
            va="bottom",
            xytext=(0, 6),
            textcoords="offset points",
            zorder=10,
        )
    elif tenkan_vals[i - 1] <= kijun_vals[i - 1] and tenkan_vals[i] > kijun_vals[i]:
        ax.annotate(
            "TK↑",
            xy=(date_nums[i], kijun_vals[i]),
            fontsize=6,
            fontweight="bold",
            color=COLOR_UP,
            ha="center",
            va="top",
            xytext=(0, -6),
            textcoords="offset points",
            zorder=10,
        )

# Date axis formatting
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
ax.tick_params(axis="x", rotation=25)

# Chrome — theme-adaptive
title = "indicator-ichimoku · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=8)
ax.set_xlabel("Date", fontsize=10, color=INK)
ax.set_ylabel("Price (USD)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.5)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_linewidth(0.5)
ax.spines["bottom"].set_color(INK_SOFT)

ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)
ax.set_axisbelow(True)

# Y-axis limits with padding
y_min = df_plot[["low", "senkou_span_a", "senkou_span_b"]].min().min()
y_max = df_plot[["high", "senkou_span_a", "senkou_span_b"]].max().max()
y_pad = (y_max - y_min) * 0.08
ax.set_ylim(y_min - y_pad, y_max + y_pad)

# Legend
legend_handles = [
    mpatches.Patch(color=COLOR_UP, label="Bullish candle / cloud"),
    mpatches.Patch(color=COLOR_DOWN, label="Bearish candle / cloud"),
    plt.Line2D([0], [0], color=COLOR_TENKAN, linewidth=1.5, label="Tenkan-sen (9)"),
    plt.Line2D([0], [0], color=COLOR_KIJUN, linewidth=1.5, label="Kijun-sen (26)"),
    plt.Line2D([0], [0], color=COLOR_CHIKOU, linewidth=1.2, linestyle="--", alpha=0.65, label="Chikou Span"),
]
leg = ax.legend(
    handles=legend_handles,
    fontsize=8,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.16),
    framealpha=0.95,
    edgecolor=INK_SOFT,
    facecolor=ELEVATED_BG,
    ncol=5,
    columnspacing=1.2,
    handletextpad=0.4,
)
if leg:
    plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.07, right=0.97, top=0.93, bottom=0.18)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
