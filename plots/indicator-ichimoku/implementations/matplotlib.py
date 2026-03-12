""" pyplots.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-12
"""

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


# Data - Generate 200 trading days of realistic stock price data
np.random.seed(42)
n_days = 200
dates = pd.bdate_range(start="2024-01-02", periods=n_days)

# Create a trend story: uptrend → consolidation → breakdown → recovery
trend = np.concatenate(
    [
        np.linspace(0, 0.12, 60),  # steady uptrend
        np.linspace(0.12, 0.10, 30),  # consolidation / topping
        np.linspace(0.10, -0.08, 50),  # bearish breakdown through cloud
        np.linspace(-0.08, 0.02, 60),  # partial recovery
    ]
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

# Compute Ichimoku components using standard parameters (9, 26, 52)
tenkan_period = 9
kijun_period = 26
senkou_b_period = 52
displacement = 26

high_series = df["high"]
low_series = df["low"]

tenkan_sen = (high_series.rolling(tenkan_period).max() + low_series.rolling(tenkan_period).min()) / 2
kijun_sen = (high_series.rolling(kijun_period).max() + low_series.rolling(kijun_period).min()) / 2

senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
senkou_span_b = ((high_series.rolling(senkou_b_period).max() + low_series.rolling(senkou_b_period).min()) / 2).shift(
    displacement
)

chikou_span = df["close"].shift(-displacement)

df["tenkan_sen"] = tenkan_sen
df["kijun_sen"] = kijun_sen
df["senkou_span_a"] = senkou_span_a
df["senkou_span_b"] = senkou_span_b
df["chikou_span"] = chikou_span

# Trim to last 120 days for a clean view with enough indicator history
trim_start = 80
df_plot = df.iloc[trim_start:].reset_index(drop=True)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_facecolor("#fafafa")
ax.set_facecolor("#fafafa")

date_nums = mdates.date2num(df_plot["date"])
bullish = df_plot["close"] >= df_plot["open"]

color_up = "#1565c0"
color_down = "#e65100"
candle_colors = np.where(bullish, color_up, color_down)
width = 0.65

# Candlestick wicks
ax.vlines(date_nums, df_plot["low"], df_plot["high"], colors=candle_colors, linewidth=1.2, zorder=3)

# Candlestick bodies
body_bottoms = np.where(bullish, df_plot["open"], df_plot["close"])
body_heights = np.abs(df_plot["close"] - df_plot["open"])
body_heights = np.where(body_heights < 0.01, 0.01, body_heights)
ax.bar(
    date_nums,
    body_heights,
    bottom=body_bottoms,
    width=width,
    color=candle_colors,
    edgecolor=candle_colors,
    linewidth=0.6,
    zorder=4,
)

# Kumo (cloud) - fill between Senkou Span A and Senkou Span B
span_a = df_plot["senkou_span_a"]
span_b = df_plot["senkou_span_b"]
valid_cloud = span_a.notna() & span_b.notna()

if valid_cloud.any():
    cloud_dates = date_nums[valid_cloud]
    cloud_a = span_a[valid_cloud].values
    cloud_b = span_b[valid_cloud].values

    ax.fill_between(
        cloud_dates, cloud_a, cloud_b, where=cloud_a >= cloud_b, color=color_up, alpha=0.18, interpolate=True, zorder=1
    )
    ax.fill_between(
        cloud_dates, cloud_a, cloud_b, where=cloud_a < cloud_b, color=color_down, alpha=0.18, interpolate=True, zorder=1
    )

    ax.plot(cloud_dates, cloud_a, color=color_up, linewidth=1.0, alpha=0.5, zorder=2)
    ax.plot(cloud_dates, cloud_b, color=color_down, linewidth=1.0, alpha=0.5, zorder=2)

# Tenkan-sen (Conversion Line)
tenkan_valid = df_plot["tenkan_sen"].notna()
ax.plot(
    date_nums[tenkan_valid],
    df_plot["tenkan_sen"][tenkan_valid],
    color="#1976d2",
    linewidth=2.0,
    alpha=0.9,
    zorder=5,
    label="Tenkan-sen (9)",
)

# Kijun-sen (Base Line)
kijun_valid = df_plot["kijun_sen"].notna()
ax.plot(
    date_nums[kijun_valid],
    df_plot["kijun_sen"][kijun_valid],
    color="#e65100",
    linewidth=2.0,
    alpha=0.9,
    zorder=5,
    label="Kijun-sen (26)",
)

# Chikou Span (Lagging Span)
chikou_valid = df_plot["chikou_span"].notna()
ax.plot(
    date_nums[chikou_valid],
    df_plot["chikou_span"][chikou_valid],
    color="#7b1fa2",
    linewidth=1.5,
    alpha=0.6,
    linestyle="--",
    zorder=2,
    label="Chikou Span",
)

# Highlight TK crossover signals with subtle markers
tenkan_vals = df_plot["tenkan_sen"].values
kijun_vals = df_plot["kijun_sen"].values
for i in range(1, len(df_plot)):
    if np.isnan(tenkan_vals[i]) or np.isnan(kijun_vals[i]):
        continue
    if np.isnan(tenkan_vals[i - 1]) or np.isnan(kijun_vals[i - 1]):
        continue
    # Bearish cross: tenkan crosses below kijun
    if tenkan_vals[i - 1] >= kijun_vals[i - 1] and tenkan_vals[i] < kijun_vals[i]:
        ax.annotate(
            "TK\u2193",
            xy=(date_nums[i], kijun_vals[i]),
            fontsize=13,
            fontweight="bold",
            color="#c62828",
            ha="center",
            va="bottom",
            xytext=(0, 12),
            textcoords="offset points",
            zorder=10,
        )
    # Bullish cross: tenkan crosses above kijun
    elif tenkan_vals[i - 1] <= kijun_vals[i - 1] and tenkan_vals[i] > kijun_vals[i]:
        ax.annotate(
            "TK\u2191",
            xy=(date_nums[i], kijun_vals[i]),
            fontsize=13,
            fontweight="bold",
            color="#1565c0",
            ha="center",
            va="top",
            xytext=(0, -12),
            textcoords="offset points",
            zorder=10,
        )

# Date formatting
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))

# Style
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price (USD)", fontsize=20)
ax.set_title("indicator-ichimoku \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)
ax.tick_params(axis="x", rotation=30)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.6)
ax.spines["left"].set_color("#999999")
ax.spines["bottom"].set_linewidth(0.6)
ax.spines["bottom"].set_color("#999999")

ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color="#888888")
ax.set_axisbelow(True)

# Legend
legend_handles = [
    mpatches.Patch(color=color_up, label="Bullish candle"),
    mpatches.Patch(color=color_down, label="Bearish candle"),
    plt.Line2D([0], [0], color="#1976d2", linewidth=2.0, label="Tenkan-sen (9)"),
    plt.Line2D([0], [0], color="#e65100", linewidth=2.0, label="Kijun-sen (26)"),
    plt.Line2D([0], [0], color="#7b1fa2", linewidth=1.5, linestyle="--", alpha=0.6, label="Chikou Span"),
    mpatches.Patch(color=color_up, alpha=0.3, label="Bullish Cloud"),
    mpatches.Patch(color=color_down, alpha=0.3, label="Bearish Cloud"),
]
ax.legend(
    handles=legend_handles,
    fontsize=16,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.10),
    framealpha=0.95,
    edgecolor="none",
    facecolor="#fafafa",
    ncol=4,
    columnspacing=1.5,
    handletextpad=0.5,
)

# Axis limits with padding
y_min = df_plot[["low", "senkou_span_a", "senkou_span_b"]].min().min()
y_max = df_plot[["high", "senkou_span_a", "senkou_span_b"]].max().max()
y_pad = (y_max - y_min) * 0.08
ax.set_ylim(y_min - y_pad, y_max + y_pad)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
