""" pyplots.ai
drawdown-basic: Drawdown Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Simulate ~2 years of daily portfolio returns
np.random.seed(42)
n_days = 500
dates = pd.date_range("2022-01-01", periods=n_days, freq="B")

# Generate realistic price series with trends, volatility, and recoveries
returns = np.random.normal(0.0005, 0.012, n_days)
# Add some market events (drawdowns) followed by recoveries
returns[50:80] -= 0.006  # First mild drawdown
returns[80:120] += 0.004  # Recovery period
returns[180:230] -= 0.010  # Larger drawdown period
returns[230:300] += 0.005  # Recovery period
returns[350:390] -= 0.008  # Another drawdown
returns[390:450] += 0.003  # Partial recovery

price = 100 * np.cumprod(1 + returns)

# Calculate drawdown
running_max = np.maximum.accumulate(price)
drawdown = (price - running_max) / running_max * 100

# Create DataFrame
df = pd.DataFrame({"Date": dates, "Price": price, "Drawdown": drawdown})

# Find maximum drawdown info
max_dd_idx = df["Drawdown"].idxmin()
max_dd_value = df["Drawdown"].min()
max_dd_date = df.loc[max_dd_idx, "Date"]

# Find recovery points (drawdown returns to zero after being negative)
recovery_mask = (df["Drawdown"] == 0) & (df["Drawdown"].shift(1) < 0)
recovery_dates = df.loc[recovery_mask, "Date"]

# Create plot
sns.set_context("talk", font_scale=1.2)
fig, ax = plt.subplots(figsize=(16, 9))

# Plot drawdown as filled area
ax.fill_between(df["Date"], df["Drawdown"], 0, color="#c44e52", alpha=0.4, label="Drawdown")
sns.lineplot(x="Date", y="Drawdown", data=df, ax=ax, color="#c44e52", linewidth=2.5)

# Zero baseline
ax.axhline(y=0, color="#333333", linewidth=1.5, linestyle="-")

# Mark maximum drawdown point
ax.scatter(
    [max_dd_date],
    [max_dd_value],
    color="#8c1515",
    s=200,
    zorder=5,
    marker="v",
    label=f"Max Drawdown: {max_dd_value:.1f}%",
)

# Mark recovery points
if len(recovery_dates) > 0:
    recovery_dd = [0] * len(recovery_dates)
    ax.scatter(recovery_dates, recovery_dd, color="#306998", s=150, zorder=5, marker="^", label="Recovery (New High)")

# Calculate statistics
max_drawdown = max_dd_value
# Find drawdown duration for max drawdown period
df_before_max = df.loc[:max_dd_idx]
zero_dd_before = df_before_max[df_before_max["Drawdown"] == 0]
dd_start_idx = zero_dd_before.index[-1] if len(zero_dd_before) > 0 else 0
dd_duration = (df.loc[max_dd_idx, "Date"] - df.loc[dd_start_idx, "Date"]).days

# Add statistics annotation
stats_text = f"Max Drawdown: {max_drawdown:.1f}%\nDays to Max DD: {dd_duration}"
ax.annotate(
    stats_text,
    xy=(0.02, 0.02),
    xycoords="axes fraction",
    fontsize=16,
    verticalalignment="bottom",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "gray", "alpha": 0.9},
)

# Styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Drawdown (%)", fontsize=20)
ax.set_title("drawdown-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(loc="lower right", fontsize=14, framealpha=0.9)
ax.grid(True, alpha=0.3, linestyle="--")

# Set y-axis to show negative values properly (drawdowns are negative)
ax.set_ylim(min(df["Drawdown"]) * 1.1, max(df["Drawdown"]) + 2)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
