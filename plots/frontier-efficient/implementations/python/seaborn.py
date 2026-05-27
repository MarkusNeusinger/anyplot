""" anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.optimize import minimize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT_1 = "#C475FD"  # Okabe-Ito position 2 (orange)
ACCENT_2 = "#4467A3"  # Okabe-Ito position 3 (blue)

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


# Optimization objective functions
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

# Plot
sns.set_theme(
    style="whitegrid",
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

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Scatter plot of random portfolios colored by Sharpe ratio
scatter = ax.scatter(
    portfolio_risks * 100,
    portfolio_returns * 100,
    c=portfolio_sharpe,
    cmap="viridis",
    s=100,
    alpha=0.6,
    edgecolors=PAGE_BG,
    linewidth=0.5,
)

# Colorbar for Sharpe ratio
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label("Sharpe Ratio", fontsize=18, color=INK)
cbar.ax.tick_params(labelsize=14, colors=INK_SOFT)

# Plot efficient frontier curve (use brand color)
ax.plot(frontier_risks * 100, frontier_returns * 100, color=BRAND, linewidth=4, label="Efficient Frontier", zorder=5)

# Mark minimum variance portfolio
ax.scatter(
    min_var_risk * 100,
    min_var_return * 100,
    color=ACCENT_2,
    s=400,
    marker="*",
    edgecolors=PAGE_BG,
    linewidths=2,
    zorder=10,
    label="Min Variance Portfolio",
)

# Mark maximum Sharpe ratio (tangency) portfolio
ax.scatter(
    max_sharpe_risk * 100,
    max_sharpe_return * 100,
    color=ACCENT_1,
    s=400,
    marker="*",
    edgecolors=PAGE_BG,
    linewidths=2,
    zorder=10,
    label="Max Sharpe Portfolio",
)

# Capital Market Line
cml_x = np.array([0, max_sharpe_risk * 100 * 1.5])
cml_slope = (max_sharpe_return - risk_free_rate) / max_sharpe_risk
cml_y = risk_free_rate * 100 + cml_slope * cml_x
ax.plot(cml_x, cml_y, color=ACCENT_2, linewidth=2.5, linestyle="--", label="Capital Market Line", zorder=4)

# Mark risk-free rate
ax.scatter(0, risk_free_rate * 100, color=ACCENT_2, s=250, marker="o", edgecolors=PAGE_BG, linewidths=2, zorder=10)
ax.annotate(
    f"Risk-Free\n({risk_free_rate * 100:.0f}%)",
    xy=(0, risk_free_rate * 100),
    xytext=(2, risk_free_rate * 100 + 1.5),
    fontsize=14,
    color=INK,
)

# Style
ax.set_xlabel("Risk (Standard Deviation, %)", fontsize=20, color=INK)
ax.set_ylabel("Expected Return (%)", fontsize=20, color=INK)
ax.set_title("frontier-efficient · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.legend(loc="lower right", fontsize=14, framealpha=0.95)
ax.set_xlim(-1, 35)
ax.set_ylim(0, 18)
ax.grid(True, alpha=0.10, linestyle="-")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
