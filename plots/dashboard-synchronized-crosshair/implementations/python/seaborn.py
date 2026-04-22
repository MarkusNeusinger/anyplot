""" pyplots.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Stock-like data with price, volume, and RSI indicator
np.random.seed(42)
n_points = 200
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

# Price series (random walk)
price_returns = np.random.randn(n_points) * 0.02
price = 100 * np.cumprod(1 + price_returns)

# Volume series (correlated with price volatility)
volume = np.abs(price_returns) * 1e8 + np.random.exponential(5e6, n_points)

# RSI-like indicator (oscillates between 30-70 mostly)
rsi = 50 + np.cumsum(np.random.randn(n_points) * 3)
rsi = np.clip(rsi, 20, 80)

df = pd.DataFrame({"date": dates, "price": price, "volume": volume, "rsi": rsi})

# Create figure with 3 stacked subplots sharing x-axis
fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True, gridspec_kw={"height_ratios": [2, 1, 1], "hspace": 0.05})

# Set seaborn style
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.0)

# Crosshair position (demonstrate at a specific date)
crosshair_idx = 120
crosshair_date = df["date"].iloc[crosshair_idx]
crosshair_price = df["price"].iloc[crosshair_idx]
crosshair_volume = df["volume"].iloc[crosshair_idx]
crosshair_rsi = df["rsi"].iloc[crosshair_idx]

# Chart 1: Price
ax1 = axes[0]
sns.lineplot(data=df, x="date", y="price", ax=ax1, color="#306998", linewidth=2.5)
ax1.set_ylabel("Price ($)", fontsize=18)
ax1.set_xlabel("")
ax1.tick_params(axis="y", labelsize=14)
ax1.fill_between(df["date"], df["price"], alpha=0.15, color="#306998")

# Add crosshair line and marker on chart 1
ax1.axvline(x=crosshair_date, color="#E74C3C", linewidth=2, linestyle="--", alpha=0.8)
ax1.scatter([crosshair_date], [crosshair_price], s=200, color="#E74C3C", zorder=5, edgecolor="white", linewidth=2)
ax1.annotate(
    f"${crosshair_price:.2f}",
    xy=(crosshair_date, crosshair_price),
    xytext=(15, 15),
    textcoords="offset points",
    fontsize=14,
    fontweight="bold",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "#E74C3C", "edgecolor": "none", "alpha": 0.9},
    color="white",
)

# Chart 2: Volume
ax2 = axes[1]
colors = ["#306998" if df["price"].iloc[i] >= df["price"].iloc[max(0, i - 1)] else "#FFD43B" for i in range(len(df))]
ax2.bar(df["date"], df["volume"], width=0.8, color=colors, alpha=0.7)
ax2.set_ylabel("Volume", fontsize=18)
ax2.set_xlabel("")
ax2.tick_params(axis="y", labelsize=14)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x / 1e6:.0f}M"))

# Add crosshair line and marker on chart 2
ax2.axvline(x=crosshair_date, color="#E74C3C", linewidth=2, linestyle="--", alpha=0.8)
ax2.scatter([crosshair_date], [crosshair_volume], s=200, color="#E74C3C", zorder=5, edgecolor="white", linewidth=2)
ax2.annotate(
    f"{crosshair_volume / 1e6:.1f}M",
    xy=(crosshair_date, crosshair_volume),
    xytext=(15, 15),
    textcoords="offset points",
    fontsize=14,
    fontweight="bold",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "#E74C3C", "edgecolor": "none", "alpha": 0.9},
    color="white",
)

# Chart 3: RSI Indicator
ax3 = axes[2]
sns.lineplot(data=df, x="date", y="rsi", ax=ax3, color="#9B59B6", linewidth=2.5)
ax3.set_ylabel("RSI", fontsize=18)
ax3.set_xlabel("Date", fontsize=18)
ax3.tick_params(axis="both", labelsize=14)
ax3.axhline(y=70, color="#E74C3C", linestyle=":", linewidth=1.5, alpha=0.7, label="Overbought (70)")
ax3.axhline(y=30, color="#27AE60", linestyle=":", linewidth=1.5, alpha=0.7, label="Oversold (30)")
ax3.fill_between(df["date"], 30, 70, alpha=0.1, color="gray")
ax3.set_ylim(15, 85)
ax3.legend(loc="upper right", fontsize=12)

# Add crosshair line and marker on chart 3
ax3.axvline(x=crosshair_date, color="#E74C3C", linewidth=2, linestyle="--", alpha=0.8)
ax3.scatter([crosshair_date], [crosshair_rsi], s=200, color="#E74C3C", zorder=5, edgecolor="white", linewidth=2)
ax3.annotate(
    f"{crosshair_rsi:.1f}",
    xy=(crosshair_date, crosshair_rsi),
    xytext=(15, 15),
    textcoords="offset points",
    fontsize=14,
    fontweight="bold",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "#E74C3C", "edgecolor": "none", "alpha": 0.9},
    color="white",
)

# Format x-axis dates
ax3.xaxis.set_major_locator(plt.MaxNLocator(8))
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha="right")

# Main title
fig.suptitle("dashboard-synchronized-crosshair · seaborn · pyplots.ai", fontsize=24, fontweight="bold", y=0.98)

# Add annotation explaining the synchronized crosshair concept
fig.text(
    0.98,
    0.02,
    "Synchronized crosshair shown at highlighted position",
    fontsize=12,
    ha="right",
    style="italic",
    alpha=0.7,
)

plt.tight_layout(rect=[0, 0.02, 1, 0.96])
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
