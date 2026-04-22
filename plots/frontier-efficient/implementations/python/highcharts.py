""" pyplots.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from scipy.optimize import minimize
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Generate random portfolios and efficient frontier
np.random.seed(42)

# Simulate asset returns and covariance for 5 assets
n_assets = 5
mean_returns = np.array([0.08, 0.12, 0.15, 0.10, 0.18])  # Annual returns
cov_matrix = np.array(
    [
        [0.04, 0.006, 0.010, 0.004, 0.012],
        [0.006, 0.09, 0.015, 0.008, 0.020],
        [0.010, 0.015, 0.16, 0.012, 0.030],
        [0.004, 0.008, 0.012, 0.05, 0.010],
        [0.012, 0.020, 0.030, 0.010, 0.25],
    ]
)

# Generate random portfolios
n_portfolios = 300
portfolio_returns = []
portfolio_risks = []
portfolio_sharpes = []
risk_free_rate = 0.03

for _ in range(n_portfolios):
    weights = np.random.random(n_assets)
    weights /= weights.sum()

    port_return = np.dot(weights, mean_returns)
    port_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe = (port_return - risk_free_rate) / port_risk

    portfolio_returns.append(port_return)
    portfolio_risks.append(port_risk)
    portfolio_sharpes.append(sharpe)

portfolio_returns = np.array(portfolio_returns)
portfolio_risks = np.array(portfolio_risks)
portfolio_sharpes = np.array(portfolio_sharpes)


# Calculate efficient frontier using optimization
def portfolio_stats(weights):
    port_return = np.dot(weights, mean_returns)
    port_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    return port_return, port_risk


def min_variance_for_return(target_return):
    n = len(mean_returns)
    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},
        {"type": "eq", "fun": lambda w: np.dot(w, mean_returns) - target_return},
    ]
    bounds = tuple((0, 1) for _ in range(n))
    result = minimize(
        lambda w: np.dot(w.T, np.dot(cov_matrix, w)),
        np.ones(n) / n,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    return result


# Generate efficient frontier points
target_returns = np.linspace(0.08, 0.18, 50)
frontier_risks = []
frontier_returns = []

for target in target_returns:
    result = min_variance_for_return(target)
    if result.success:
        _, risk = portfolio_stats(result.x)
        frontier_risks.append(risk)
        frontier_returns.append(target)

frontier_risks = np.array(frontier_risks)
frontier_returns = np.array(frontier_returns)

# Find minimum variance portfolio
min_var_idx = np.argmin(frontier_risks)
min_var_risk = frontier_risks[min_var_idx]
min_var_return = frontier_returns[min_var_idx]

# Find maximum Sharpe ratio portfolio
sharpe_ratios = (frontier_returns - risk_free_rate) / frontier_risks
max_sharpe_idx = np.argmax(sharpe_ratios)
tangency_risk = frontier_risks[max_sharpe_idx]
tangency_return = frontier_returns[max_sharpe_idx]

# Prepare data for Highcharts - categorize by Sharpe ratio
low_sharpe = []
mid_sharpe = []
high_sharpe = []

sharpe_33 = np.percentile(portfolio_sharpes, 33)
sharpe_66 = np.percentile(portfolio_sharpes, 66)

for i in range(len(portfolio_risks)):
    point = {"x": round(portfolio_risks[i] * 100, 2), "y": round(portfolio_returns[i] * 100, 2)}
    if portfolio_sharpes[i] < sharpe_33:
        low_sharpe.append(point)
    elif portfolio_sharpes[i] < sharpe_66:
        mid_sharpe.append(point)
    else:
        high_sharpe.append(point)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart options
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 280,
    "marginLeft": 200,
    "marginRight": 300,
    "marginTop": 120,
}

# Title
chart.options.title = {
    "text": "frontier-efficient · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {"text": "Efficient Frontier with Simulated Portfolios", "style": {"fontSize": "32px"}}

# Axes
chart.options.x_axis = {
    "title": {"text": "Risk (Standard Deviation %)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "min": 0,
}

chart.options.y_axis = {
    "title": {"text": "Expected Return (%)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
}

# Plot options
chart.options.plot_options = {
    "scatter": {"marker": {"radius": 10}, "states": {"hover": {"marker": {"enabled": True}}}},
    "line": {"lineWidth": 6, "marker": {"enabled": False}},
}

# Add scatter series for different Sharpe ratio groups
low_sharpe_series = ScatterSeries()
low_sharpe_series.data = low_sharpe
low_sharpe_series.name = "Low Sharpe Ratio"
low_sharpe_series.color = "#8C564B"
low_sharpe_series.marker = {"symbol": "circle", "radius": 10}
chart.add_series(low_sharpe_series)

mid_sharpe_series = ScatterSeries()
mid_sharpe_series.data = mid_sharpe
mid_sharpe_series.name = "Medium Sharpe Ratio"
mid_sharpe_series.color = "#FFD43B"
mid_sharpe_series.marker = {"symbol": "circle", "radius": 10}
chart.add_series(mid_sharpe_series)

high_sharpe_series = ScatterSeries()
high_sharpe_series.data = high_sharpe
high_sharpe_series.name = "High Sharpe Ratio"
high_sharpe_series.color = "#306998"
high_sharpe_series.marker = {"symbol": "circle", "radius": 10}
chart.add_series(high_sharpe_series)

# Efficient frontier line
frontier_data = [
    {"x": round(r * 100, 2), "y": round(ret * 100, 2)} for r, ret in zip(frontier_risks, frontier_returns, strict=True)
]
frontier_series = LineSeries()
frontier_series.data = frontier_data
frontier_series.name = "Efficient Frontier"
frontier_series.color = "#17BECF"
frontier_series.line_width = 8
frontier_series.marker = {"enabled": False}
frontier_series.z_index = 5
chart.add_series(frontier_series)

# Minimum variance portfolio
min_var_series = ScatterSeries()
min_var_series.data = [{"x": round(min_var_risk * 100, 2), "y": round(min_var_return * 100, 2)}]
min_var_series.name = "Minimum Variance"
min_var_series.color = "#9467BD"
min_var_series.marker = {"symbol": "square", "radius": 18, "lineWidth": 3, "lineColor": "#000000"}
min_var_series.z_index = 10
chart.add_series(min_var_series)

# Tangency portfolio (max Sharpe)
tangency_series = ScatterSeries()
tangency_series.data = [{"x": round(tangency_risk * 100, 2), "y": round(tangency_return * 100, 2)}]
tangency_series.name = "Maximum Sharpe Ratio"
tangency_series.color = "#E377C2"
tangency_series.marker = {"symbol": "triangle", "radius": 20, "lineWidth": 3, "lineColor": "#000000"}
tangency_series.z_index = 10
chart.add_series(tangency_series)

# Capital market line (from risk-free rate tangent to frontier)
cml_end_risk = tangency_risk * 2.5
cml_end_return = risk_free_rate + (tangency_return - risk_free_rate) / tangency_risk * cml_end_risk
cml_data = [
    {"x": 0, "y": round(risk_free_rate * 100, 2)},
    {"x": round(cml_end_risk * 100, 2), "y": round(cml_end_return * 100, 2)},
]
cml_series = LineSeries()
cml_series.data = cml_data
cml_series.name = "Capital Market Line"
cml_series.color = "#2CA02C"
cml_series.dash_style = "Dash"
cml_series.line_width = 5
cml_series.marker = {"enabled": False}
cml_series.z_index = 4
chart.add_series(cml_series)

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
