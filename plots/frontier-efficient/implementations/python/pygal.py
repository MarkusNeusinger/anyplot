""" anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: pygal 3.1.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - Generate simulated portfolios and efficient frontier
np.random.seed(42)

# Simulate 5 assets with expected returns and volatilities
n_assets = 5
expected_returns = np.array([0.08, 0.12, 0.15, 0.10, 0.18])
volatilities = np.array([0.15, 0.20, 0.25, 0.18, 0.30])

# Create correlation matrix and covariance matrix
correlations = np.array(
    [
        [1.0, 0.3, 0.4, 0.2, 0.3],
        [0.3, 1.0, 0.5, 0.3, 0.4],
        [0.4, 0.5, 1.0, 0.3, 0.5],
        [0.2, 0.3, 0.3, 1.0, 0.3],
        [0.3, 0.4, 0.5, 0.3, 1.0],
    ]
)
cov_matrix = np.outer(volatilities, volatilities) * correlations

# Generate 300 random portfolios
n_portfolios = 300
portfolio_returns = []
portfolio_risks = []
portfolio_sharpes = []
risk_free_rate = 0.02

for _ in range(n_portfolios):
    weights = np.random.random(n_assets)
    weights /= weights.sum()
    port_return = np.dot(weights, expected_returns)
    port_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe = (port_return - risk_free_rate) / port_risk
    portfolio_returns.append(port_return)
    portfolio_risks.append(port_risk)
    portfolio_sharpes.append(sharpe)

# Generate efficient frontier by finding optimal portfolios at each risk level
n_samples = 5000
all_returns = []
all_risks = []
all_sharpes = []

for _ in range(n_samples):
    weights = np.random.random(n_assets)
    weights /= weights.sum()
    port_return = np.dot(weights, expected_returns)
    port_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe = (port_return - risk_free_rate) / port_risk
    all_returns.append(port_return)
    all_risks.append(port_risk)
    all_sharpes.append(sharpe)

# Find efficient frontier points (pareto optimal)
risk_buckets = np.linspace(min(all_risks), max(all_risks), 40)
frontier_risks = []
frontier_returns = []

for i in range(len(risk_buckets) - 1):
    mask = (np.array(all_risks) >= risk_buckets[i]) & (np.array(all_risks) < risk_buckets[i + 1])
    if np.any(mask):
        bucket_returns = np.array(all_returns)[mask]
        best_idx = np.argmax(bucket_returns)
        bucket_risks = np.array(all_risks)[mask]
        frontier_risks.append(bucket_risks[best_idx])
        frontier_returns.append(bucket_returns[best_idx])

# Sort frontier by risk
sorted_indices = np.argsort(frontier_risks)
frontier_risks = [frontier_risks[i] for i in sorted_indices]
frontier_returns = [frontier_returns[i] for i in sorted_indices]

# Find minimum variance portfolio (lowest risk)
min_var_idx = np.argmin(all_risks)
min_var_risk = all_risks[min_var_idx]
min_var_return = all_returns[min_var_idx]

# Find maximum Sharpe ratio portfolio
max_sharpe_idx = np.argmax(all_sharpes)
max_sharpe_risk = all_risks[max_sharpe_idx]
max_sharpe_return = all_returns[max_sharpe_idx]

# Custom style - theme-adaptive tokens, Okabe-Ito palette
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Calculate appropriate axis ranges based on actual data
data_max_risk = max(max(portfolio_risks), max(frontier_risks), max_sharpe_risk, min_var_risk)
data_min_risk = min(min(portfolio_risks), min(frontier_risks), max_sharpe_risk, min_var_risk)
data_max_return = max(max(portfolio_returns), max(frontier_returns), max_sharpe_return, min_var_return)
data_min_return = min(min(portfolio_returns), min(frontier_returns), max_sharpe_return, min_var_return)

# Add small padding for better visualization
x_padding = (data_max_risk - data_min_risk) * 0.1
y_padding = (data_max_return - data_min_return) * 0.1

# Create XY chart (scatter plot capability)
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="frontier-efficient · pygal · anyplot.ai",
    x_title="Risk (Standard Deviation)",
    y_title="Expected Return",
    show_x_guides=True,
    show_y_guides=True,
    dots_size=8,
    stroke=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    truncate_legend=-1,
    x_value_formatter=lambda x: f"{x:.1%}",
    y_value_formatter=lambda y: f"{y:.1%}",
    range=(max(0, data_min_return - y_padding), data_max_return + y_padding),
    xrange=(max(0, data_min_risk - x_padding), data_max_risk + x_padding),
)

# Add random portfolios grouped by Sharpe ratio
sharpe_33 = np.percentile(portfolio_sharpes, 33)
sharpe_66 = np.percentile(portfolio_sharpes, 66)

low_sharpe = [
    (portfolio_risks[i], portfolio_returns[i]) for i in range(n_portfolios) if portfolio_sharpes[i] < sharpe_33
]
mid_sharpe = [
    (portfolio_risks[i], portfolio_returns[i])
    for i in range(n_portfolios)
    if sharpe_33 <= portfolio_sharpes[i] < sharpe_66
]
high_sharpe = [
    (portfolio_risks[i], portfolio_returns[i]) for i in range(n_portfolios) if portfolio_sharpes[i] >= sharpe_66
]

chart.add(f"Low Sharpe (<{sharpe_33:.2f})", low_sharpe, dots_size=8)
chart.add(f"Mid Sharpe ({sharpe_33:.2f}-{sharpe_66:.2f})", mid_sharpe, dots_size=8)
chart.add(f"High Sharpe (≥{sharpe_66:.2f})", high_sharpe, dots_size=8)

# Add efficient frontier as connected line
frontier_points = list(zip(frontier_risks, frontier_returns, strict=False))
chart.add("Efficient Frontier", frontier_points, stroke=True, dots_size=0, stroke_style={"width": 8})

# Add special marker points for key portfolios
chart.add("Min Variance", [(min_var_risk, min_var_return)], dots_size=25)
chart.add("Max Sharpe", [(max_sharpe_risk, max_sharpe_return)], dots_size=25)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")

# Save HTML for interactive version
with open(f"plot-{THEME}.html", "w") as f:
    f.write(chart.render().decode("utf-8"))
