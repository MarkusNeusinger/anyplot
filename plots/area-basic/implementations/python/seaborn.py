""" pyplots.ai
area-basic: Basic Area Chart
Library: seaborn 0.13.2 | Python 3.14.2
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns


# Data - daily website visitors over a month
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=30, freq="D")

# Simulate realistic web traffic with weekly pattern, trend, and a traffic spike
base_visitors = 5000
trend = np.linspace(0, 1500, 30)
weekly_pattern = np.array([1.0, 1.1, 1.15, 1.2, 1.1, 0.7, 0.65] * 5)[:30]
noise = np.random.randn(30) * 300
visitors = (base_visitors + trend) * weekly_pattern + noise
visitors[17] *= 1.45  # Traffic spike from a viral post on day 18
visitors = np.maximum(visitors, 1000)

df = pd.DataFrame({"date": dates, "visitors": visitors})

# Compute monthly average for storytelling annotation
avg_visitors = df["visitors"].mean()

# Plot - use seaborn's theme management for coherent styling
sns.set_theme(
    style="white",
    context="talk",
    font_scale=1.2,
    rc={"axes.spines.top": False, "axes.spines.right": False, "grid.alpha": 0.2, "grid.linewidth": 0.8},
)

fig, ax = plt.subplots(figsize=(16, 9))

# Build a layered gradient fill using seaborn's light_palette
# Multiple fill_between layers at decreasing thresholds create a smooth gradient
palette_colors = sns.light_palette("#306998", n_colors=6)
y_max = df["visitors"].max() * 1.08
n_layers = 5
for i in range(n_layers):
    fraction = (i + 1) / n_layers
    ax.fill_between(df["date"], 0, df["visitors"] * fraction, color=palette_colors[i + 1], alpha=0.12, linewidth=0)

# Use seaborn's lineplot for the area boundary
sns.lineplot(data=df, x="date", y="visitors", ax=ax, color="#306998", linewidth=3)

# Annotate the traffic spike
spike_idx = 17
spike_val = df["visitors"].iloc[spike_idx]
ax.annotate(
    "Viral post",
    xy=(df["date"].iloc[spike_idx], spike_val),
    xytext=(df["date"].iloc[spike_idx - 9], spike_val * 0.82),
    fontsize=16,
    fontweight="semibold",
    color="#1a3a5c",
    arrowprops={"arrowstyle": "->", "color": "#1a3a5c", "lw": 2, "connectionstyle": "arc3,rad=-0.2"},
    ha="center",
    va="top",
)

# Add average line with label for data storytelling
ax.axhline(y=avg_visitors, color="#306998", linestyle="--", linewidth=1.5, alpha=0.5, zorder=1)
ax.text(
    df["date"].iloc[-1],
    avg_visitors + y_max * 0.015,
    f"Monthly avg: {avg_visitors:,.0f}",
    fontsize=14,
    color="#306998",
    ha="right",
    va="bottom",
    fontstyle="italic",
    alpha=0.8,
)

# Style - axis labels and title
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Visitors (count)", fontsize=20)
ax.set_title("area-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, pad=16)
ax.tick_params(axis="both", labelsize=16)

# Use seaborn's despine for idiomatic spine removal
sns.despine(ax=ax)

# Enable y-axis grid below data
ax.yaxis.grid(True)
ax.set_axisbelow(True)

# Y-axis: thousands separator formatting
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

# X-axis: clean date formatting ("Jan 01" style)
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
ax.xaxis.set_minor_locator(mdates.DayLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

# Set y-axis to start at 0
ax.set_ylim(bottom=0, top=y_max)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
