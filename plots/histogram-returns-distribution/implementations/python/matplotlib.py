""" pyplots.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-16
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from scipy import stats


# Data - Generate synthetic daily returns for 252 trading days (1 year)
np.random.seed(42)
n_days = 252
# Simulate daily returns with slight negative skew and fat tails (more realistic)
returns = np.random.standard_t(df=5, size=n_days) * 0.015 + 0.0003  # ~1.5% daily vol

# Calculate statistics
mean_ret = np.mean(returns) * 100
std_ret = np.std(returns) * 100
skewness = stats.skew(returns)
kurtosis = stats.kurtosis(returns)

# Convert to percentage for plotting
returns_pct = returns * 100

# Fit normal distribution to the data
x_range = np.linspace(returns_pct.min() - 1, returns_pct.max() + 1, 200)
normal_pdf = stats.norm.pdf(x_range, mean_ret, std_ret)

# Calculate tail thresholds (2 standard deviations)
lower_tail = mean_ret - 2 * std_ret
upper_tail = mean_ret + 2 * std_ret

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot histogram with density normalization
n, bins, patches = ax.hist(
    returns_pct, bins=35, density=True, alpha=0.7, color="#306998", edgecolor="white", linewidth=1.5
)

# Color tail bins differently
for i, patch in enumerate(patches):
    bin_center = (bins[i] + bins[i + 1]) / 2
    if bin_center < lower_tail or bin_center > upper_tail:
        patch.set_facecolor("#FFD43B")
        patch.set_alpha(0.9)

# Overlay normal distribution curve
ax.plot(x_range, normal_pdf, color="#C75450", linewidth=3, linestyle="--", label="Normal Distribution")

# Add vertical lines for mean and standard deviations
ax.axvline(mean_ret, color="#306998", linewidth=2.5, linestyle="-", alpha=0.8, label="Mean")

# Create manual legend entries for histogram (blue for main, yellow for tails)
hist_patch = Patch(facecolor="#306998", edgecolor="white", alpha=0.7, label="Returns Distribution")
tail_patch = Patch(facecolor="#FFD43B", edgecolor="white", alpha=0.9, label="Tail Regions (>2σ)")
ax.axvline(lower_tail, color="#888888", linewidth=2, linestyle=":", alpha=0.7)
ax.axvline(upper_tail, color="#888888", linewidth=2, linestyle=":", alpha=0.7)

# Statistics text box
stats_text = (
    f"Statistics:\nMean: {mean_ret:.3f}%\nStd Dev: {std_ret:.3f}%\nSkewness: {skewness:.3f}\nKurtosis: {kurtosis:.3f}"
)
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
    family="monospace",
)

# Labels and styling
ax.set_xlabel("Daily Returns (%)", fontsize=20)
ax.set_ylabel("Density", fontsize=20)
ax.set_title("histogram-returns-distribution · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Build legend with correct colors
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles=[hist_patch, tail_patch] + handles, fontsize=16, loc="upper left")

ax.grid(True, alpha=0.3, linestyle="--")

# Add annotations for both tail regions
ax.annotate("Left Tail\n(<-2σ)", xy=(lower_tail - 1, 0.02), fontsize=14, ha="center", color="#888888")
ax.annotate("Right Tail\n(>+2σ)", xy=(upper_tail + 1, 0.02), fontsize=14, ha="center", color="#888888")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
