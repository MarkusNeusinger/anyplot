""" pyplots.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 88/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch


# Set seaborn style for consistent aesthetics
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

# Generate realistic stock data for 60 trading days
np.random.seed(42)
n_days = 60

# Start with a base price and generate realistic price movements
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")  # Business days
base_price = 150.0

# Generate price series with trends and volatility
returns = np.random.normal(0.001, 0.02, n_days)  # Daily returns
prices = base_price * np.cumprod(1 + returns)

# Generate OHLC from the price series
opens = np.zeros(n_days)
highs = np.zeros(n_days)
lows = np.zeros(n_days)
closes = np.zeros(n_days)

opens[0] = base_price
for i in range(n_days):
    if i > 0:
        opens[i] = closes[i - 1] + np.random.normal(0, 0.5)
    closes[i] = prices[i]
    # Ensure more significant price moves for better visibility
    daily_range = abs(closes[i] - opens[i]) + np.random.uniform(1.0, 3.0)
    highs[i] = max(opens[i], closes[i]) + np.random.uniform(0.5, daily_range * 0.6)
    lows[i] = min(opens[i], closes[i]) - np.random.uniform(0.5, daily_range * 0.6)

# Generate volume with some correlation to price movements
base_volume = 5_000_000
volume = base_volume + np.random.normal(0, 1_000_000, n_days)
# Higher volume on bigger price moves
price_change = np.abs(closes - opens)
volume = volume + price_change * 500_000
volume = np.clip(volume, 1_000_000, 15_000_000).astype(int)

# Create DataFrame
df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes, "volume": volume})

# Determine bullish vs bearish candles
df["bullish"] = df["close"] >= df["open"]
df["day_idx"] = range(len(df))

# Colors for consistent styling
BULLISH_COLOR = "#306998"  # Python Blue
BEARISH_COLOR = "#FFD43B"  # Python Yellow

# Create figure with two subplots sharing x-axis (75% price, 25% volume)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), height_ratios=[3, 1], sharex=True, gridspec_kw={"hspace": 0.05})

# Set grid below chart elements FIRST before any plotting
for ax in [ax1, ax2]:
    ax.set_axisbelow(True)

# === Upper pane: Candlestick chart using seaborn ===
# Prepare data for seaborn lineplot (wicks) - create long format for high-low lines
df["wick_min"] = df[["open", "close"]].min(axis=1)
df["wick_max"] = df[["open", "close"]].max(axis=1)
df["body_height"] = (df["wick_max"] - df["wick_min"]).clip(lower=0.5)  # Minimum height for visibility
df["direction"] = df["bullish"].map({True: "Bullish", False: "Bearish"})

# Draw high-low wicks using seaborn lineplot with units parameter
wick_long = pd.melt(
    df[["day_idx", "high", "low", "direction"]],
    id_vars=["day_idx", "direction"],
    value_vars=["low", "high"],
    var_name="price_type",
    value_name="price",
).sort_values(["day_idx", "price_type"])

sns.lineplot(
    data=wick_long,
    x="day_idx",
    y="price",
    hue="direction",
    palette={"Bullish": BULLISH_COLOR, "Bearish": BEARISH_COLOR},
    linewidth=2,
    units="day_idx",
    estimator=None,
    legend=False,
    ax=ax1,
    zorder=2,
)

# Draw candle bodies with minimum height for visibility
for _, row in df.iterrows():
    color = BULLISH_COLOR if row["bullish"] else BEARISH_COLOR
    body_low = row["wick_min"]
    body_high = body_low + row["body_height"]
    ax1.fill_between(
        [row["day_idx"] - 0.35, row["day_idx"] + 0.35],
        [body_low] * 2,
        [body_high] * 2,
        color=color,
        alpha=1.0,
        linewidth=0,
        zorder=3,
    )

# Style the price axis
ax1.set_ylabel("Price ($)", fontsize=20)
ax1.set_xlabel("")
ax1.tick_params(axis="both", labelsize=16)
ax1.set_title("candlestick-volume · seaborn · pyplots.ai", fontsize=24, pad=15)

# Set y-axis range with padding
price_min = df["low"].min()
price_max = df["high"].max()
price_padding = (price_max - price_min) * 0.05
ax1.set_ylim(price_min - price_padding, price_max + price_padding)

# === Lower pane: Volume bars ===
# Draw volume bars directly with matplotlib to ensure single bar per day
# Colors match the candlestick bullish/bearish scheme
bar_colors = [BULLISH_COLOR if b else BEARISH_COLOR for b in df["bullish"]]
ax2.bar(df["day_idx"], df["volume"], color=bar_colors, width=0.7, alpha=0.9, zorder=2)

# Style the volume axis with units
ax2.set_ylabel("Volume (M shares)", fontsize=20)
ax2.set_xlabel("Date", fontsize=20)
ax2.tick_params(axis="both", labelsize=16)

# Format y-axis for volume (millions)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x / 1e6:.1f}M"))

# === Aligned grid lines across both panes ===
# Use consistent grid styling (grid already set below via set_axisbelow earlier)
for ax in [ax1, ax2]:
    ax.grid(True, axis="both", alpha=0.3, linestyle="--", linewidth=0.8)

# Configure x-axis with date labels at regular intervals
n_ticks = 6
tick_positions = np.linspace(0, len(df) - 1, n_ticks, dtype=int)
tick_labels = [df.iloc[i]["date"].strftime("%b %d") for i in tick_positions]
ax2.set_xticks(tick_positions)
ax2.set_xticklabels(tick_labels, rotation=45, ha="right")

# Add legend to price pane
legend_elements = [
    Patch(facecolor=BULLISH_COLOR, label="Bullish (Close ≥ Open)"),
    Patch(facecolor=BEARISH_COLOR, label="Bearish (Close < Open)"),
]
ax1.legend(handles=legend_elements, loc="upper left", fontsize=14, framealpha=0.9)

# === Add crosshair cursor spanning both panes ===
# Draw static crosshair lines at a representative position to show the feature
# Using a position at approximately 2/3 of the chart for good visibility
crosshair_idx = int(len(df) * 0.65)
crosshair_price = (df.iloc[crosshair_idx]["high"] + df.iloc[crosshair_idx]["low"]) / 2
crosshair_volume = df.iloc[crosshair_idx]["volume"]

# Vertical crosshair line spanning both panes - more prominent styling
crosshair_color = "#E63946"  # Red for high visibility
for ax in [ax1, ax2]:
    ax.axvline(x=crosshair_idx, color=crosshair_color, linestyle="--", linewidth=2, alpha=0.8, zorder=5)

# Horizontal crosshair lines in both panes for precise reading
ax1.axhline(y=crosshair_price, color=crosshair_color, linestyle="--", linewidth=2, alpha=0.8, zorder=5)
ax2.axhline(y=crosshair_volume, color=crosshair_color, linestyle="--", linewidth=2, alpha=0.8, zorder=5)

# Add crosshair label annotation for price pane with arrow
ax1.annotate(
    f"${crosshair_price:.2f}",
    xy=(crosshair_idx, crosshair_price),
    xytext=(crosshair_idx + 5, crosshair_price + (price_max - price_min) * 0.08),
    fontsize=14,
    fontweight="bold",
    color=crosshair_color,
    va="center",
    arrowprops={"arrowstyle": "->", "color": crosshair_color, "lw": 1.5},
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": crosshair_color, "alpha": 0.95},
)

# Add crosshair label annotation for volume pane with arrow
ax2.annotate(
    f"{crosshair_volume / 1e6:.1f}M shares",
    xy=(crosshair_idx, crosshair_volume),
    xytext=(crosshair_idx + 5, crosshair_volume * 1.15),
    fontsize=14,
    fontweight="bold",
    color=crosshair_color,
    va="center",
    arrowprops={"arrowstyle": "->", "color": crosshair_color, "lw": 1.5},
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": crosshair_color, "alpha": 0.95},
)

# Add date label at crosshair position
crosshair_date = df.iloc[crosshair_idx]["date"].strftime("%b %d, %Y")
ax2.annotate(
    crosshair_date,
    xy=(crosshair_idx, 0),
    xytext=(crosshair_idx, -ax2.get_ylim()[1] * 0.15),
    fontsize=12,
    fontweight="bold",
    color=crosshair_color,
    ha="center",
    va="top",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": crosshair_color, "alpha": 0.95},
    annotation_clip=False,
)

# Adjust layout and save
fig.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.12, hspace=0.05)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
