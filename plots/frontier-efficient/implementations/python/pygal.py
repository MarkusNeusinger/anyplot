""" pyplots.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-08
"""

import numpy as np
import pygal
from pygal.style import Style


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
# Using many random samples and selecting pareto-optimal ones
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
# Sort by risk and find maximum return for each risk bucket
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

# Custom style for pyplots - increased font sizes for better readability
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#2ECC71", "#1A1A1A", "#9B59B6", "#E74C3C"),
    title_font_size=56,
    label_font_size=40,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=24,
    value_label_font_size=24,
    tooltip_font_size=24,
    stroke_width=4,
    opacity=0.6,
    opacity_hover=0.9,
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
    title="frontier-efficient · pygal · pyplots.ai",
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
# Adjust thresholds based on actual data distribution
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

# Add efficient frontier as connected line - using dark color to stand out
frontier_points = list(zip(frontier_risks, frontier_returns, strict=False))
chart.add("Efficient Frontier", frontier_points, stroke=True, dots_size=0, stroke_style={"width": 8})

# Add special marker points with larger sizes for visibility
chart.add("Min Variance", [(min_var_risk, min_var_return)], dots_size=25)
chart.add("Max Sharpe", [(max_sharpe_risk, max_sharpe_return)], dots_size=25)

# Save outputs
chart.render_to_png("plot.png")

# Save HTML for interactive version
with open("plot.html", "w") as f:
    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Efficient Frontier - pygal</title>
    <style>
        body {{ margin: 0; padding: 20px; background: white; }}
        svg {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    {chart.render(is_unicode=True)}
</body>
</html>""")
