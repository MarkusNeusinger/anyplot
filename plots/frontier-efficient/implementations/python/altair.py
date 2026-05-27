""" anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from scipy.optimize import minimize


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data - Portfolio simulation with efficient frontier
np.random.seed(42)

# Asset parameters (5 assets)
n_assets = 5
n_portfolios = 300

# Expected returns and covariance (realistic annualized values)
expected_returns = np.array([0.08, 0.10, 0.12, 0.15, 0.18])
cov_matrix = np.array(
    [
        [0.04, 0.01, 0.02, 0.01, 0.02],
        [0.01, 0.06, 0.02, 0.03, 0.02],
        [0.02, 0.02, 0.09, 0.04, 0.03],
        [0.01, 0.03, 0.04, 0.12, 0.05],
        [0.02, 0.02, 0.03, 0.05, 0.16],
    ]
)
risk_free_rate = 0.02

# Generate random portfolios
portfolio_returns = []
portfolio_risks = []
portfolio_sharpes = []

for _ in range(n_portfolios):
    weights = np.random.random(n_assets)
    weights /= np.sum(weights)

    ret = np.dot(weights, expected_returns)
    risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe = (ret - risk_free_rate) / risk

    portfolio_returns.append(ret)
    portfolio_risks.append(risk)
    portfolio_sharpes.append(sharpe)

# Find minimum variance portfolio first
constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1},)
bounds = tuple((0, 1) for _ in range(n_assets))
result_minvar = minimize(
    lambda w: np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))),
    np.ones(n_assets) / n_assets,
    method="SLSQP",
    bounds=bounds,
    constraints=constraints,
)
min_var_risk = result_minvar.fun
min_var_return = np.dot(result_minvar.x, expected_returns)

# Calculate efficient frontier using optimization (from min variance to max return)
frontier_risks_opt = []
frontier_returns_opt = []
target_returns = np.linspace(min_var_return, max(expected_returns), 50)

for target in target_returns:
    constraints = (
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},
        {"type": "eq", "fun": lambda w, t=target: np.dot(w, expected_returns) - t},
    )
    bounds = tuple((0, 1) for _ in range(n_assets))
    result = minimize(
        lambda w: np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))),
        np.ones(n_assets) / n_assets,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    if result.success:
        frontier_returns_opt.append(target)
        frontier_risks_opt.append(result.fun)

# Maximum Sharpe ratio portfolio
sharpe_ratios = [(r - risk_free_rate) / v for r, v in zip(frontier_returns_opt, frontier_risks_opt, strict=True)]
max_sharpe_idx = np.argmax(sharpe_ratios)
max_sharpe_risk = frontier_risks_opt[max_sharpe_idx]
max_sharpe_return = frontier_returns_opt[max_sharpe_idx]

# Create DataFrames
portfolios_df = pd.DataFrame(
    {"Risk (Std Dev)": portfolio_risks, "Expected Return": portfolio_returns, "Sharpe Ratio": portfolio_sharpes}
)

frontier_df = pd.DataFrame({"Risk (Std Dev)": frontier_risks_opt, "Expected Return": frontier_returns_opt})

special_points_df = pd.DataFrame(
    {
        "Risk (Std Dev)": [min_var_risk, max_sharpe_risk],
        "Expected Return": [min_var_return, max_sharpe_return],
        "Portfolio": ["Minimum Variance", "Maximum Sharpe Ratio"],
    }
)

# Capital Market Line
cml_risk = np.array([0, max_sharpe_risk * 1.5])
cml_return = risk_free_rate + (max_sharpe_return - risk_free_rate) / max_sharpe_risk * cml_risk
cml_df = pd.DataFrame({"Risk (Std Dev)": cml_risk, "Expected Return": cml_return})

# Risk-free rate point
rf_df = pd.DataFrame({"Risk (Std Dev)": [0], "Expected Return": [risk_free_rate], "Point": ["Risk-Free Rate"]})

# Plot
# Scatter plot of random portfolios colored by Sharpe ratio
scatter = (
    alt.Chart(portfolios_df)
    .mark_circle(size=100, opacity=0.6)
    .encode(
        x=alt.X("Risk (Std Dev):Q", scale=alt.Scale(domain=[0, 0.45]), title="Risk (Standard Deviation)"),
        y=alt.Y("Expected Return:Q", scale=alt.Scale(domain=[0, 0.22]), title="Expected Return"),
        color=alt.Color(
            "Sharpe Ratio:Q",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(title="Sharpe Ratio", titleFontSize=16, labelFontSize=14),
        ),
        tooltip=["Risk (Std Dev)", "Expected Return", "Sharpe Ratio"],
    )
)

# Efficient frontier line
frontier_line = (
    alt.Chart(frontier_df).mark_line(strokeWidth=4, color=BRAND).encode(x="Risk (Std Dev):Q", y="Expected Return:Q")
)

# Capital market line
cml_line = (
    alt.Chart(cml_df)
    .mark_line(strokeWidth=3, strokeDash=[8, 4], color=IMPRINT[1])
    .encode(x="Risk (Std Dev):Q", y="Expected Return:Q")
)

# Special points
special_points = (
    alt.Chart(special_points_df)
    .mark_point(size=400, filled=True, stroke="white", strokeWidth=2)
    .encode(
        x="Risk (Std Dev):Q",
        y="Expected Return:Q",
        color=alt.Color(
            "Portfolio:N",
            scale=alt.Scale(domain=["Minimum Variance", "Maximum Sharpe Ratio"], range=[IMPRINT[1], IMPRINT[2]]),
            legend=alt.Legend(title="Key Portfolios", titleFontSize=16, labelFontSize=14),
        ),
        tooltip=["Portfolio", "Risk (Std Dev)", "Expected Return"],
    )
)

# Risk-free rate point
rf_point = (
    alt.Chart(rf_df)
    .mark_point(size=300, shape="diamond", filled=True, color=INK_SOFT)
    .encode(x="Risk (Std Dev):Q", y="Expected Return:Q", tooltip=["Point", "Expected Return"])
)

# Combine all layers
chart = (
    alt.layer(scatter, frontier_line, cml_line, special_points, rf_point)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("frontier-efficient · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=16,
        titleColor=INK,
        titleFontSize=20,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=16,
        labelFontSize=14,
        symbolSize=200,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
