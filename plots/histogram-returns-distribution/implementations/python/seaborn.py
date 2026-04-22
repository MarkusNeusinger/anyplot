""" pyplots.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-16
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy import stats


# Set random seed for reproducibility
np.random.seed(42)

# Generate synthetic daily returns data (252 trading days)
n_days = 252
daily_returns = np.random.normal(loc=0.0005, scale=0.015, size=n_days) * 100  # Convert to percentage

# Calculate statistics
mean_return = np.mean(daily_returns)
std_return = np.std(daily_returns)
skewness = stats.skew(daily_returns)
kurtosis = stats.kurtosis(daily_returns)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_context("talk", font_scale=1.2)

# Create histogram with density normalization
# Highlight tail regions beyond 2 standard deviations
lower_tail = mean_return - 2 * std_return
upper_tail = mean_return + 2 * std_return

# Separate data into tail and non-tail regions
tail_data = daily_returns[(daily_returns < lower_tail) | (daily_returns > upper_tail)]
non_tail_data = daily_returns[(daily_returns >= lower_tail) & (daily_returns <= upper_tail)]

# Create histogram using histplot with stat='density'
bins = np.linspace(daily_returns.min(), daily_returns.max(), 35)
sns.histplot(non_tail_data, bins=bins, stat="density", color="#306998", alpha=0.7, ax=ax, label="Returns")
sns.histplot(tail_data, bins=bins, stat="density", color="#FFD43B", alpha=0.9, ax=ax, label="Tail regions (>2σ)")

# Overlay normal distribution curve
x_range = np.linspace(daily_returns.min() - 0.5, daily_returns.max() + 0.5, 200)
normal_pdf = stats.norm.pdf(x_range, mean_return, std_return)
ax.plot(x_range, normal_pdf, color="#C44E52", linewidth=3, linestyle="-", label="Normal distribution")

# Add vertical lines for tail boundaries
ax.axvline(lower_tail, color="#555555", linestyle="--", linewidth=2, alpha=0.7)
ax.axvline(upper_tail, color="#555555", linestyle="--", linewidth=2, alpha=0.7)

# Add statistics text box
stats_text = f"Mean: {mean_return:.3f}%\nStd Dev: {std_return:.3f}%\nSkewness: {skewness:.3f}\nKurtosis: {kurtosis:.3f}"
bbox_props = {"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "#306998", "alpha": 0.9}
ax.text(
    0.97,
    0.97,
    stats_text,
    transform=ax.transAxes,
    fontsize=16,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=bbox_props,
)

# Labels and styling
ax.set_xlabel("Daily Returns (%)", fontsize=20)
ax.set_ylabel("Density", fontsize=20)
ax.set_title("histogram-returns-distribution · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=14, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
