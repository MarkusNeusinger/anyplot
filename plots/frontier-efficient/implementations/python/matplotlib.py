""" pyplots.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-08
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Simulating portfolios from a 5-asset universe
np.random.seed(42)

# Asset parameters (annualized returns and covariance matrix)
n_assets = 5
expected_returns = np.array([0.12, 0.10, 0.14, 0.08, 0.16])  # Annual returns
asset_volatilities = np.array([0.18, 0.12, 0.25, 0.10, 0.30])

# Create realistic correlation matrix
correlations = np.array(
    [
        [1.00, 0.30, 0.50, 0.20, 0.40],
        [0.30, 1.00, 0.25, 0.60, 0.35],
        [0.50, 0.25, 1.00, 0.15, 0.55],
        [0.20, 0.60, 0.15, 1.00, 0.25],
        [0.40, 0.35, 0.55, 0.25, 1.00],
    ]
)
cov_matrix = np.outer(asset_volatilities, asset_volatilities) * correlations
risk_free_rate = 0.03

# Generate many random portfolios to approximate efficient frontier
n_portfolios = 5000
all_returns = []
all_risks = []
all_sharpes = []
all_weights = []

for _ in range(n_portfolios):
    weights = np.random.random(n_assets)
    weights /= weights.sum()
    ret = np.dot(weights, expected_returns)
    risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe = (ret - risk_free_rate) / risk
    all_returns.append(ret)
    all_risks.append(risk)
    all_sharpes.append(sharpe)
    all_weights.append(weights)

all_returns = np.array(all_returns)
all_risks = np.array(all_risks)
all_sharpes = np.array(all_sharpes)

# Extract efficient frontier points (highest return for each risk level)
# Bin by risk and find max return in each bin
risk_bins = np.linspace(all_risks.min(), all_risks.max(), 50)
efficient_returns = []
efficient_risks = []

for i in range(len(risk_bins) - 1):
    mask = (all_risks >= risk_bins[i]) & (all_risks < risk_bins[i + 1])
    if mask.sum() > 0:
        max_return_idx = np.argmax(all_returns[mask])
        idx = np.where(mask)[0][max_return_idx]
        efficient_returns.append(all_returns[idx])
        efficient_risks.append(all_risks[idx])

efficient_returns = np.array(efficient_returns)
efficient_risks = np.array(efficient_risks)

# Sort by risk for smooth curve
sort_idx = np.argsort(efficient_risks)
efficient_risks = efficient_risks[sort_idx]
efficient_returns = efficient_returns[sort_idx]

# Find minimum variance portfolio (lowest risk)
min_var_idx = np.argmin(all_risks)
min_var_return = all_returns[min_var_idx]
min_var_risk = all_risks[min_var_idx]

# Find maximum Sharpe ratio portfolio
max_sharpe_idx = np.argmax(all_sharpes)
max_sharpe_return = all_returns[max_sharpe_idx]
max_sharpe_risk = all_risks[max_sharpe_idx]

# Filter efficient frontier to points above minimum variance
frontier_mask = efficient_returns >= min_var_return - 0.005
efficient_risks = efficient_risks[frontier_mask]
efficient_returns = efficient_returns[frontier_mask]

# Sample portfolios for scatter plot (subset for visibility)
sample_idx = np.random.choice(len(all_returns), size=300, replace=False)
sample_returns = all_returns[sample_idx]
sample_risks = all_risks[sample_idx]
sample_sharpes = all_sharpes[sample_idx]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Random portfolios colored by Sharpe ratio
scatter = ax.scatter(
    sample_risks * 100, sample_returns * 100, c=sample_sharpes, cmap="viridis", s=80, alpha=0.6, edgecolors="none"
)

# Efficient frontier curve
ax.plot(
    efficient_risks * 100, efficient_returns * 100, color="#306998", linewidth=4, label="Efficient Frontier", zorder=5
)

# Minimum variance portfolio
ax.scatter(
    min_var_risk * 100,
    min_var_return * 100,
    color="#FFD43B",
    s=400,
    marker="D",
    edgecolors="#306998",
    linewidth=2,
    label="Minimum Variance Portfolio",
    zorder=6,
)

# Maximum Sharpe ratio portfolio
ax.scatter(
    max_sharpe_risk * 100,
    max_sharpe_return * 100,
    color="#FF6B6B",
    s=400,
    marker="*",
    edgecolors="#306998",
    linewidth=2,
    label="Maximum Sharpe Ratio Portfolio",
    zorder=6,
)

# Capital Market Line
cml_x_end = max_sharpe_risk * 1.6
cml_slope = (max_sharpe_return - risk_free_rate) / max_sharpe_risk
cml_x = np.array([0, cml_x_end]) * 100
cml_y = (risk_free_rate + cml_slope * np.array([0, cml_x_end])) * 100
ax.plot(cml_x, cml_y, color="#888888", linewidth=2, linestyle="--", label="Capital Market Line", zorder=4)

# Risk-free rate point
ax.scatter(0, risk_free_rate * 100, color="#888888", s=200, marker="o", zorder=6, label="Risk-Free Rate")

# Colorbar for Sharpe ratio
cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Sharpe Ratio", fontsize=18)
cbar.ax.tick_params(labelsize=14)

# Labels and styling
ax.set_xlabel("Risk (Standard Deviation, %)", fontsize=20)
ax.set_ylabel("Expected Return (%)", fontsize=20)
ax.set_title("frontier-efficient · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=14, loc="upper left", framealpha=0.9)
ax.set_xlim(left=0)
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
