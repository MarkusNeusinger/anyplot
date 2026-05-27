""" anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-17
"""

import os
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Generate random portfolios and efficient frontier
np.random.seed(42)

# Simulate asset returns and covariance for 5 assets
n_assets = 5
mean_returns = np.array([0.08, 0.12, 0.15, 0.10, 0.18])
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
frontier_risks = []
frontier_returns = []

target_returns = np.linspace(0.08, 0.18, 50)
for target_return in target_returns:
    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},
        {"type": "eq", "fun": lambda w, tr=target_return: np.dot(w, mean_returns) - tr},
    ]
    bounds = tuple((0, 1) for _ in range(n_assets))
    result = minimize(
        lambda w: np.dot(w.T, np.dot(cov_matrix, w)),
        np.ones(n_assets) / n_assets,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    if result.success:
        port_return = np.dot(result.x, mean_returns)
        port_risk = np.sqrt(np.dot(result.x.T, np.dot(cov_matrix, result.x)))
        frontier_risks.append(port_risk)
        frontier_returns.append(port_return)

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
    "backgroundColor": PAGE_BG,
    "marginBottom": 280,
    "marginLeft": 200,
    "marginRight": 300,
    "marginTop": 120,
}

# Title
chart.options.title = {
    "text": "frontier-efficient · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK},
}

# Axes
chart.options.x_axis = {
    "title": {"text": "Risk (Standard Deviation %)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "min": 0,
}

chart.options.y_axis = {
    "title": {"text": "Expected Return (%)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"color": INK_SOFT, "fontSize": "18px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "align": "left",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": 100,
    "y": 100,
}

# Plot options
chart.options.plot_options = {
    "scatter": {"marker": {"radius": 8}, "states": {"hover": {"marker": {"enabled": True}}}},
    "line": {"lineWidth": 6, "marker": {"enabled": False}},
}

# Add scatter series for different Sharpe ratio groups
low_sharpe_series = ScatterSeries()
low_sharpe_series.data = low_sharpe
low_sharpe_series.name = "Low Sharpe Ratio"
low_sharpe_series.color = IMPRINT[1]
low_sharpe_series.marker = {"symbol": "circle", "radius": 8}
chart.add_series(low_sharpe_series)

mid_sharpe_series = ScatterSeries()
mid_sharpe_series.data = mid_sharpe
mid_sharpe_series.name = "Medium Sharpe Ratio"
mid_sharpe_series.color = IMPRINT[2]
mid_sharpe_series.marker = {"symbol": "circle", "radius": 8}
chart.add_series(mid_sharpe_series)

high_sharpe_series = ScatterSeries()
high_sharpe_series.data = high_sharpe
high_sharpe_series.name = "High Sharpe Ratio"
high_sharpe_series.color = IMPRINT[0]
high_sharpe_series.marker = {"symbol": "circle", "radius": 8}
chart.add_series(high_sharpe_series)

# Efficient frontier line
frontier_data = [
    {"x": round(r * 100, 2), "y": round(ret * 100, 2)} for r, ret in zip(frontier_risks, frontier_returns, strict=True)
]
frontier_series = LineSeries()
frontier_series.data = frontier_data
frontier_series.name = "Efficient Frontier"
frontier_series.color = IMPRINT[3]
frontier_series.line_width = 8
frontier_series.marker = {"enabled": False}
frontier_series.z_index = 5
chart.add_series(frontier_series)

# Minimum variance portfolio
min_var_series = ScatterSeries()
min_var_series.data = [{"x": round(min_var_risk * 100, 2), "y": round(min_var_return * 100, 2)}]
min_var_series.name = "Minimum Variance"
min_var_series.color = IMPRINT[4]
min_var_series.marker = {"symbol": "square", "radius": 14, "lineWidth": 3, "lineColor": INK}
min_var_series.z_index = 10
chart.add_series(min_var_series)

# Tangency portfolio (max Sharpe)
tangency_series = ScatterSeries()
tangency_series.data = [{"x": round(tangency_risk * 100, 2), "y": round(tangency_return * 100, 2)}]
tangency_series.name = "Maximum Sharpe Ratio"
tangency_series.color = IMPRINT[5]
tangency_series.marker = {"symbol": "triangle", "radius": 16, "lineWidth": 3, "lineColor": INK}
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
cml_series.color = IMPRINT[6]
cml_series.dash_style = "Dash"
cml_series.line_width = 5
cml_series.marker = {"enabled": False}
cml_series.z_index = 4
chart.add_series(cml_series)

# Download Highcharts JS from jsDelivr CDN (more reliable in CI)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11.4.3/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
)
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")
except urllib.error.HTTPError:
    highcharts_url = "https://code.highcharts.com/highcharts.js"
    with urllib.request.urlopen(
        urllib.request.Request(
            highcharts_url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        ),
        timeout=30,
    ) as response:
        highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML file
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
