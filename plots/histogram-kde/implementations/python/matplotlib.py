""" pyplots.ai
histogram-kde: Histogram with KDE Overlay
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 95/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - simulate stock daily returns (realistic financial data)
np.random.seed(42)
# Mix of normal market conditions and some fat tails
normal_returns = np.random.normal(0.0005, 0.015, 800)  # Normal trading days
volatile_returns = np.random.normal(-0.002, 0.035, 150)  # Volatile periods
extreme_returns = np.random.normal(0.001, 0.05, 50)  # Extreme events
returns = np.concatenate([normal_returns, volatile_returns, extreme_returns])
np.random.shuffle(returns)
returns = returns * 100  # Convert to percentage

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Histogram with density scaling (semi-transparent)
ax.hist(
    returns, bins=40, density=True, alpha=0.5, color="#306998", edgecolor="#1e4d6b", linewidth=1.5, label="Histogram"
)

# KDE calculation (Gaussian kernel with Scott's rule bandwidth)
n_data = len(returns)
bandwidth = 1.06 * np.std(returns) * n_data ** (-1 / 5)
x_range = np.linspace(returns.min() - 0.5, returns.max() + 0.5, 500)
kde_values = np.zeros_like(x_range)
for xi in returns:
    kde_values += np.exp(-0.5 * ((x_range - xi) / bandwidth) ** 2)
kde_values /= n_data * bandwidth * np.sqrt(2 * np.pi)

# Plot KDE overlay
ax.plot(x_range, kde_values, color="#FFD43B", linewidth=4, label="KDE")

# Styling
ax.set_xlabel("Daily Return (%)", fontsize=20)
ax.set_ylabel("Density", fontsize=20)
ax.set_title("histogram-kde \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper right")
ax.grid(True, alpha=0.3, linestyle="--")

# Layout and save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
