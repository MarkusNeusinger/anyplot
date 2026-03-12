"""pyplots.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-12
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle


# Seaborn theme and context
sns.set_theme(
    style="whitegrid",
    rc={
        "axes.facecolor": "#f8f9fa",
        "figure.facecolor": "white",
        "grid.color": "#dee2e6",
        "text.color": "#212529",
        "axes.labelcolor": "#495057",
        "xtick.color": "#495057",
        "ytick.color": "#495057",
    },
)
sns.set_context("talk", font_scale=1.2)

# Data — 200 trading days of synthetic stock data with trending behavior
np.random.seed(42)
n_days = 200
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")

price = 150.0
drift = np.concatenate(
    [
        np.linspace(0.15, 0.5, 60),
        np.linspace(0.5, -0.2, 40),
        np.linspace(-0.2, -0.4, 30),
        np.linspace(-0.4, 0.3, 40),
        np.linspace(0.3, 0.6, 30),
    ]
)
opens, highs, lows, closes = [], [], [], []
for i in range(n_days):
    change = drift[i] + np.random.randn() * 1.8
    volatility = abs(np.random.randn()) * 1.2 + 0.5
    open_price = price
    close_price = price + change
    high_price = max(open_price, close_price) + abs(np.random.randn()) * volatility
    low_price = min(open_price, close_price) - abs(np.random.randn()) * volatility
    opens.append(open_price)
    highs.append(high_price)
    lows.append(low_price)
    closes.append(close_price)
    price = close_price

df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes})
df["bullish"] = df["close"] >= df["open"]
df["x"] = range(n_days)

# Ichimoku calculations (standard parameters: 9, 26, 52)
tenkan_period, kijun_period, senkou_b_period, displacement = 9, 26, 52, 26

df["tenkan_sen"] = (df["high"].rolling(window=tenkan_period).max() + df["low"].rolling(window=tenkan_period).min()) / 2

df["kijun_sen"] = (df["high"].rolling(window=kijun_period).max() + df["low"].rolling(window=kijun_period).min()) / 2

df["senkou_span_a"] = ((df["tenkan_sen"] + df["kijun_sen"]) / 2).shift(displacement)

df["senkou_span_b"] = (
    (df["high"].rolling(window=senkou_b_period).max() + df["low"].rolling(window=senkou_b_period).min()) / 2
).shift(displacement)

df["chikou_span"] = df["close"].shift(-displacement)

# Trim to visible window (skip early NaN period, keep enough for cloud display)
visible_start = 80
df_vis = df.iloc[visible_start:].copy()
df_vis["x"] = range(len(df_vis))

# Colorblind-safe palette: blue for bullish, amber/orange for bearish
cb_palette = sns.color_palette("colorblind")
up_color = "#306998"
down_color = "#d4820e"
up_edge = sns.dark_palette(up_color, n_colors=4)[2]
down_edge = sns.dark_palette(down_color, n_colors=4)[2]
tenkan_color = "#0072B2"
kijun_color = "#E69F00"
chikou_color = "#8e44ad"
cloud_bull_color = "#0072B2"
cloud_bear_color = "#D55E00"

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Cloud (Kumo) fill — increased alpha for visibility
span_a = df_vis["senkou_span_a"].values
span_b = df_vis["senkou_span_b"].values
x_vals = df_vis["x"].values
mask_valid = ~(np.isnan(span_a) | np.isnan(span_b))
x_cloud = x_vals[mask_valid]
sa_cloud = span_a[mask_valid]
sb_cloud = span_b[mask_valid]

ax.fill_between(
    x_cloud, sa_cloud, sb_cloud, where=sa_cloud >= sb_cloud, color=cloud_bull_color, alpha=0.22, interpolate=True
)
ax.fill_between(
    x_cloud, sa_cloud, sb_cloud, where=sa_cloud < sb_cloud, color=cloud_bear_color, alpha=0.22, interpolate=True
)

# Senkou Span A and B lines
ax.plot(x_cloud, sa_cloud, color=cloud_bull_color, linewidth=1.0, alpha=0.5)
ax.plot(x_cloud, sb_cloud, color=cloud_bear_color, linewidth=1.0, alpha=0.5)

# Candlestick wicks — colorblind-safe colors
wick_colors = [up_edge if b else down_edge for b in df_vis["bullish"]]
ax.vlines(df_vis["x"], df_vis["low"], df_vis["high"], colors=wick_colors, linewidth=1.0)

# Candle bodies — bullish: filled, bearish: hollow (edge only) for colorblind differentiation
body_width = 0.5
bull_rects, bull_fcolors, bull_ecolors = [], [], []
bear_rects, bear_ecolors = [], []
for _, row in df_vis.iterrows():
    bottom = min(row["open"], row["close"])
    height = max(abs(row["close"] - row["open"]), 0.12)
    if abs(row["close"] - row["open"]) < 0.12:
        bottom = (row["open"] + row["close"]) / 2 - 0.06
    rect = Rectangle((row["x"] - body_width / 2, bottom), body_width, height)
    if row["bullish"]:
        bull_rects.append(rect)
        bull_fcolors.append(up_color)
        bull_ecolors.append(up_edge)
    else:
        bear_rects.append(rect)
        bear_ecolors.append(down_edge)

if bull_rects:
    bull_bodies = PatchCollection(bull_rects, facecolors=bull_fcolors, edgecolors=bull_ecolors, linewidths=0.6)
    ax.add_collection(bull_bodies)
if bear_rects:
    bear_bodies = PatchCollection(bear_rects, facecolors="none", edgecolors=bear_ecolors, linewidths=1.4)
    ax.add_collection(bear_bodies)

# Ichimoku indicator lines in long format for seaborn hue-based rendering
tenkan_df = df_vis[["x", "tenkan_sen"]].dropna().rename(columns={"tenkan_sen": "value"})
tenkan_df["indicator"] = "Tenkan-sen (9)"
kijun_df = df_vis[["x", "kijun_sen"]].dropna().rename(columns={"kijun_sen": "value"})
kijun_df["indicator"] = "Kijun-sen (26)"
chikou_df = df_vis[["x", "chikou_span"]].dropna().rename(columns={"chikou_span": "value"})
chikou_df["indicator"] = "Chikou Span"

indicator_df = pd.concat([tenkan_df, kijun_df, chikou_df], ignore_index=True)
indicator_palette = {"Tenkan-sen (9)": tenkan_color, "Kijun-sen (26)": kijun_color, "Chikou Span": chikou_color}
indicator_sizes = {"Tenkan-sen (9)": 1.8, "Kijun-sen (26)": 1.8, "Chikou Span": 1.2}

sns.lineplot(
    data=indicator_df,
    x="x",
    y="value",
    hue="indicator",
    palette=indicator_palette,
    size="indicator",
    sizes=indicator_sizes,
    alpha=0.85,
    ax=ax,
    legend=False,
)

# Data storytelling: find and annotate a TK crossover signal
tenkan_vals = df_vis["tenkan_sen"].values
kijun_vals = df_vis["kijun_sen"].values
cross_indices = []
for i in range(1, len(tenkan_vals)):
    if np.isnan(tenkan_vals[i]) or np.isnan(kijun_vals[i]):
        continue
    if np.isnan(tenkan_vals[i - 1]) or np.isnan(kijun_vals[i - 1]):
        continue
    prev_diff = tenkan_vals[i - 1] - kijun_vals[i - 1]
    curr_diff = tenkan_vals[i] - kijun_vals[i]
    if prev_diff <= 0 < curr_diff:
        cross_indices.append((i, "bullish"))
    elif prev_diff >= 0 > curr_diff:
        cross_indices.append((i, "bearish"))

# Highlight the most prominent bullish crossover
if cross_indices:
    bullish_crosses = [(idx, t) for idx, t in cross_indices if t == "bullish"]
    if bullish_crosses:
        cross_idx = bullish_crosses[0][0]
    else:
        cross_idx = cross_indices[0][0]
    cross_x = df_vis["x"].iloc[cross_idx]
    cross_y = tenkan_vals[cross_idx]
    cross_type = [t for idx, t in cross_indices if idx == cross_idx][0]

    ax.plot(
        cross_x,
        cross_y,
        "o",
        markersize=12,
        markerfacecolor="none",
        markeredgecolor="#333333",
        markeredgewidth=2.0,
        zorder=10,
    )
    label_text = "Bullish TK Cross" if cross_type == "bullish" else "Bearish TK Cross"
    ax.annotate(
        label_text,
        xy=(cross_x, cross_y),
        xytext=(cross_x + 8, cross_y + 4),
        fontsize=13,
        fontweight="bold",
        color="#333333",
        arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 1.5},
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#aaaaaa", "alpha": 0.9},
        zorder=10,
    )

# X-axis date labels
tick_step = max(1, len(df_vis) // 8)
tick_idx = range(0, len(df_vis), tick_step)
ax.set_xticks(list(tick_idx))
ax.set_xticklabels([df_vis.iloc[i]["date"].strftime("%b %d") for i in tick_idx], rotation=30, ha="right")

# Style
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.set_title("indicator-ichimoku \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16, length=0)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.xaxis.grid(False)
ax.set_axisbelow(True)

# Legend with colorblind-safe entries
legend_handles = [
    Patch(facecolor=up_color, edgecolor=up_edge, label="Bullish (filled)"),
    Patch(facecolor="none", edgecolor=down_edge, linewidth=1.4, label="Bearish (hollow)"),
    Line2D([0], [0], color=tenkan_color, linewidth=1.8, label="Tenkan-sen (9)"),
    Line2D([0], [0], color=kijun_color, linewidth=1.8, label="Kijun-sen (26)"),
    Line2D([0], [0], color=chikou_color, linewidth=1.2, alpha=0.6, label="Chikou Span"),
    Patch(facecolor=cloud_bull_color, alpha=0.35, label="Bullish Cloud"),
    Patch(facecolor=cloud_bear_color, alpha=0.35, label="Bearish Cloud"),
]
ax.legend(handles=legend_handles, fontsize=12, loc="upper left", framealpha=0.9, edgecolor="#dee2e6", ncol=2)

# Axis limits
ax.set_xlim(-1, len(df_vis) + 0.5)
y_pad = (df_vis["high"].max() - df_vis["low"].min()) * 0.08
ax.set_ylim(df_vis["low"].min() - y_pad, df_vis["high"].max() + y_pad * 2)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
