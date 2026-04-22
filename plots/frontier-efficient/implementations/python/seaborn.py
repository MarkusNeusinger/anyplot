""" pyplots.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.optimize import minimize


# Data - Generate random portfolios and efficient frontier
np.random.seed(42)

# Simulate 5 assets with expected returns and covariance
n_assets = 5
expected_returns = np.array([0.08, 0.12, 0.10, 0.15, 0.07])
# Generate a valid positive semi-definite covariance matrix
volatilities = np.array([0.15, 0.22, 0.18, 0.28, 0.12])
correlation = np.array(
    [
        [1.0, 0.3, 0.2, 0.4, 0.1],
        [0.3, 1.0, 0.5, 0.3, 0.2],
        [0.2, 0.5, 1.0, 0.4, 0.3],
        [0.4, 0.3, 0.4, 1.0, 0.2],
        [0.1, 0.2, 0.3, 0.2, 1.0],
    ]
)
cov_matrix = np.outer(volatilities, volatilities) * correlation

# Generate random portfolios
n_portfolios = 300
portfolio_returns = []
portfolio_risks = []
portfolio_sharpe = []
risk_free_rate = 0.02

for _ in range(n_portfolios):
    weights = np.random.random(n_assets)
    weights /= np.sum(weights)
    ret = np.dot(weights, expected_returns)
    risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe = (ret - risk_free_rate) / risk
    portfolio_returns.append(ret)
    portfolio_risks.append(risk)
    portfolio_sharpe.append(sharpe)

portfolio_returns = np.array(portfolio_returns)
portfolio_risks = np.array(portfolio_risks)
portfolio_sharpe = np.array(portfolio_sharpe)


# Optimization objective functions (required for scipy.optimize)
def calc_vol(w):
    return np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))


def calc_neg_sharpe(w):
    ret = np.dot(w, expected_returns)
    vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
    return -(ret - risk_free_rate) / vol


# Find minimum variance portfolio
constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
bounds = tuple((0, 1) for _ in range(n_assets))
init_weights = np.array([1 / n_assets] * n_assets)

min_var_result = minimize(calc_vol, init_weights, method="SLSQP", bounds=bounds, constraints=constraints)
min_var_weights = min_var_result.x
min_var_risk = calc_vol(min_var_weights)
min_var_return = np.dot(min_var_weights, expected_returns)

# Find maximum Sharpe ratio (tangency) portfolio
max_sharpe_result = minimize(calc_neg_sharpe, init_weights, method="SLSQP", bounds=bounds, constraints=constraints)
max_sharpe_weights = max_sharpe_result.x
max_sharpe_risk = calc_vol(max_sharpe_weights)
max_sharpe_return = np.dot(max_sharpe_weights, expected_returns)

# Generate efficient frontier curve
target_returns = np.linspace(min_var_return, max(expected_returns) * 0.98, 50)
frontier_risks = []
frontier_returns = []

for target in target_returns:
    constraints_ef = [
        {"type": "eq", "fun": lambda x: np.sum(x) - 1},
        {"type": "eq", "fun": lambda x, t=target: np.dot(x, expected_returns) - t},
    ]
    result = minimize(calc_vol, init_weights, method="SLSQP", bounds=bounds, constraints=constraints_ef)
    if result.success:
        frontier_risks.append(calc_vol(result.x))
        frontier_returns.append(target)

frontier_risks = np.array(frontier_risks)
frontier_returns = np.array(frontier_returns)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Scatter plot of random portfolios colored by Sharpe ratio
sns.scatterplot(
    x=portfolio_risks * 100,
    y=portfolio_returns * 100,
    hue=portfolio_sharpe,
    palette="viridis",
    s=100,
    alpha=0.6,
    ax=ax,
    legend=False,
)

# Add colorbar for Sharpe ratio
norm = plt.Normalize(portfolio_sharpe.min(), portfolio_sharpe.max())
sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax)
cbar.set_label("Sharpe Ratio", fontsize=18)
cbar.ax.tick_params(labelsize=14)

# Plot efficient frontier curve
ax.plot(
    frontier_risks * 100, frontier_returns * 100, color="#FFD43B", linewidth=4, label="Efficient Frontier", zorder=5
)

# Mark minimum variance portfolio
ax.scatter(
    min_var_risk * 100,
    min_var_return * 100,
    color="#306998",
    s=400,
    marker="*",
    edgecolors="white",
    linewidths=2,
    zorder=10,
    label="Min Variance Portfolio",
)

# Mark maximum Sharpe ratio (tangency) portfolio
ax.scatter(
    max_sharpe_risk * 100,
    max_sharpe_return * 100,
    color="#E63946",
    s=400,
    marker="*",
    edgecolors="white",
    linewidths=2,
    zorder=10,
    label="Max Sharpe Portfolio",
)

# Capital Market Line (from risk-free rate tangent to max Sharpe portfolio)
cml_x = np.array([0, max_sharpe_risk * 100 * 1.5])
cml_slope = (max_sharpe_return - risk_free_rate) / max_sharpe_risk
cml_y = risk_free_rate * 100 + cml_slope * cml_x
ax.plot(cml_x, cml_y, color="#306998", linewidth=2.5, linestyle="--", label="Capital Market Line", zorder=4)

# Mark risk-free rate
ax.scatter(0, risk_free_rate * 100, color="#306998", s=250, marker="o", edgecolors="white", linewidths=2, zorder=10)
ax.annotate(
    f"Risk-Free\n({risk_free_rate * 100:.0f}%)",
    xy=(0, risk_free_rate * 100),
    xytext=(2, risk_free_rate * 100 + 1.5),
    fontsize=14,
    ha="left",
)

# Labels and styling
ax.set_xlabel("Risk (Standard Deviation, %)", fontsize=20)
ax.set_ylabel("Expected Return (%)", fontsize=20)
ax.set_title("frontier-efficient · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(loc="lower right", fontsize=14, framealpha=0.9)
ax.set_xlim(-1, 35)
ax.set_ylim(0, 18)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
