""" anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-17
"""

import os
import sys


# Prevent script name from shadowing seaborn package
cwd = os.getcwd()
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.abspath(os.path.dirname(__file__))]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402


# Theme configuration
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"  # Close price (primary)
SECONDARY = "#C475FD"  # SMA (middle band)
TERTIARY = "#4467A3"  # Bollinger Bands

# Apply theme
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

# Data - Generate realistic stock price data with Bollinger Bands
np.random.seed(42)

# Generate 120 trading days of price data
n_days = 120
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Simulate price movement with trend and volatility
returns = np.random.normal(0.0005, 0.015, n_days)
price_base = 150
prices = price_base * np.cumprod(1 + returns)

# Add some volatility clustering (higher volatility periods)
volatility_boost = np.zeros(n_days)
volatility_boost[30:50] = np.random.normal(0, 0.01, 20)  # High volatility period
volatility_boost[80:95] = np.random.normal(0, 0.008, 15)  # Another volatile period
prices = prices * (1 + volatility_boost)

# Calculate Bollinger Bands (20-period SMA, 2 standard deviations)
window = 20
close = pd.Series(prices)
sma = close.rolling(window=window).mean()
std = close.rolling(window=window).std()
upper_band = sma + 2 * std
lower_band = sma - 2 * std

# Create DataFrame
df = pd.DataFrame({"date": dates, "close": close, "sma": sma, "upper_band": upper_band, "lower_band": lower_band})

# Drop NaN values from rolling calculation
df = df.dropna().reset_index(drop=True)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot Bollinger Bands fill between upper and lower
ax.fill_between(
    df["date"], df["lower_band"], df["upper_band"], alpha=0.15, color=TERTIARY, label="Bollinger Band Range"
)

# Plot upper band
ax.plot(df["date"], df["upper_band"], color=TERTIARY, linewidth=2, alpha=0.7, label="Upper Band (+2σ)")

# Plot lower band
ax.plot(df["date"], df["lower_band"], color=TERTIARY, linewidth=2, alpha=0.7, label="Lower Band (-2σ)")

# Plot SMA (middle band) - dashed line
ax.plot(df["date"], df["sma"], color=SECONDARY, linewidth=2.5, linestyle="--", label="20-Day SMA")

# Plot close price - prominent line
ax.plot(df["date"], df["close"], color=BRAND, linewidth=3, label="Close Price")

# Styling
ax.set_title("indicator-bollinger · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

# Legend
ax.legend(fontsize=16, loc="upper left", framealpha=0.95, frameon=True)

# Grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.set_axisbelow(True)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()

# Save to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, f"plot-{THEME}.png")
plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
