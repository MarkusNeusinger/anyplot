""" pyplots.ai
subplot-grid: Subplot Grid Layout
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Financial dashboard scenario
np.random.seed(42)

# Generate trading days
days = 100
dates = pd.date_range("2024-01-01", periods=days, freq="B")

# Stock price (random walk with upward drift)
price_returns = np.random.normal(0.001, 0.02, days)
price = 100 * np.cumprod(1 + price_returns)

# Volume (random with some correlation to price changes)
base_volume = np.random.lognormal(mean=15, sigma=0.5, size=days)
volume = base_volume * (1 + np.abs(price_returns) * 10)

# Daily returns
returns = np.diff(price) / price[:-1] * 100
returns = np.insert(returns, 0, 0)

# Create DataFrame
df = pd.DataFrame(
    {
        "Date": dates,
        "Price": price,
        "Volume": volume / 1e6,  # Scale to millions
        "Return": returns,
    }
)

# Create 2x2 subplot grid
fig, axes = plt.subplots(2, 2, figsize=(16, 9))

# Subplot 1: Price Line Chart (top-left)
ax1 = axes[0, 0]
sns.lineplot(data=df, x="Date", y="Price", ax=ax1, color="#306998", linewidth=2.5)
ax1.set_title("Stock Price", fontsize=20, fontweight="bold", pad=10)
ax1.set_xlabel("Date", fontsize=16)
ax1.set_ylabel("Price ($)", fontsize=16)
ax1.tick_params(axis="both", labelsize=12)
ax1.tick_params(axis="x", rotation=30)
ax1.grid(True, alpha=0.3, linestyle="--")

# Subplot 2: Volume Bar Chart (top-right)
ax2 = axes[0, 1]
# Create bar positions for volume
bar_positions = np.arange(len(df))
colors = ["#306998" if r >= 0 else "#FFD43B" for r in df["Return"]]
ax2.bar(bar_positions[::5], df["Volume"].values[::5], width=4, color=colors[::5], alpha=0.8)
ax2.set_title("Trading Volume", fontsize=20, fontweight="bold", pad=10)
ax2.set_xlabel("Trading Day", fontsize=16)
ax2.set_ylabel("Volume (Millions)", fontsize=16)
ax2.tick_params(axis="both", labelsize=12)
ax2.grid(True, alpha=0.3, linestyle="--", axis="y")
ax2.set_xlim(-2, len(df) + 2)

# Subplot 3: Returns Distribution (bottom-left)
ax3 = axes[1, 0]
sns.histplot(data=df, x="Return", bins=25, ax=ax3, color="#306998", alpha=0.7, edgecolor="white")
ax3.axvline(x=0, color="#FFD43B", linewidth=2.5, linestyle="--", label="Zero Return")
ax3.set_title("Daily Returns Distribution", fontsize=20, fontweight="bold", pad=10)
ax3.set_xlabel("Daily Return (%)", fontsize=16)
ax3.set_ylabel("Frequency", fontsize=16)
ax3.tick_params(axis="both", labelsize=12)
ax3.grid(True, alpha=0.3, linestyle="--")
ax3.legend(fontsize=12, loc="upper right")

# Subplot 4: Price vs Volume Scatter (bottom-right)
ax4 = axes[1, 1]
sns.scatterplot(
    data=df,
    x="Price",
    y="Volume",
    hue="Return",
    palette="RdBu",
    size="Volume",
    sizes=(50, 300),
    alpha=0.7,
    ax=ax4,
    legend=False,
)
ax4.set_title("Price vs Volume", fontsize=20, fontweight="bold", pad=10)
ax4.set_xlabel("Price ($)", fontsize=16)
ax4.set_ylabel("Volume (Millions)", fontsize=16)
ax4.tick_params(axis="both", labelsize=12)
ax4.grid(True, alpha=0.3, linestyle="--")

# Add colorbar for the scatter plot
norm = plt.Normalize(df["Return"].min(), df["Return"].max())
sm = plt.cm.ScalarMappable(cmap="RdBu", norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax4, shrink=0.8, pad=0.02)
cbar.set_label("Daily Return (%)", fontsize=12)
cbar.ax.tick_params(labelsize=10)

# Main title
fig.suptitle("subplot-grid · seaborn · pyplots.ai", fontsize=24, fontweight="bold", y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
