""" pyplots.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: highcharts unknown | Python 3.14.3
Quality: 90/100 | Created: 2026-03-11
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.axes.labels import AxisLabelOptions
from highcharts_core.options.axes.x_axis import XAxis
from highcharts_core.options.axes.y_axis import YAxis
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
from highcharts_core.utility_classes.javascript_functions import CallbackFunction
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data — turbine blade fatigue-life (hours) with censored observations
np.random.seed(42)
n_failures = 25
n_censored = 5
shape_true = 2.5
scale_true = 8000

failure_times = np.sort(stats.weibull_min.rvs(shape_true, scale=scale_true, size=n_failures))
censored_times = np.random.uniform(2000, 7000, size=n_censored)

all_times = np.concatenate([failure_times, censored_times])
is_failure = np.concatenate([np.ones(n_failures), np.zeros(n_censored)])

sort_idx = np.argsort(all_times)
all_times = all_times[sort_idx]
is_failure = is_failure[sort_idx]

# Median rank plotting positions for failures only (i-0.3)/(n+0.4)
failure_rank = 0
failure_plot_x = []
failure_plot_y = []
censored_plot_x = []
censored_plot_y = []

for i in range(len(all_times)):
    if is_failure[i] == 1:
        failure_rank += 1
        median_rank = (failure_rank - 0.3) / (n_failures + 0.4)
        weibull_y = np.log(-np.log(1 - median_rank))
        failure_plot_x.append(float(np.log(all_times[i])))
        failure_plot_y.append(float(weibull_y))
    else:
        adj_rank = (failure_rank + 0.5 - 0.3) / (n_failures + 0.4)
        adj_rank = min(adj_rank, 0.99)
        weibull_y = np.log(-np.log(1 - adj_rank))
        censored_plot_x.append(float(np.log(all_times[i])))
        censored_plot_y.append(float(weibull_y))

# Fit line to failure data (least squares on ln(t) vs ln(-ln(1-F)))
fit_x = np.array(failure_plot_x)
fit_y = np.array(failure_plot_y)
slope, intercept = np.polyfit(fit_x, fit_y, 1)

beta = slope
eta = np.exp(-intercept / slope)

# Fitted line endpoints
x_range = np.array([min(fit_x) - 0.3, max(fit_x) + 0.3])
y_fit = slope * x_range + intercept

# Reference line at 63.2% (characteristic life)
y_632 = np.log(-np.log(1 - 0.632))
ln_eta = np.log(eta)

# Actual time tick values for x-axis labels
time_ticks = [1000, 2000, 3000, 5000, 8000, 12000, 18000]
ln_time_ticks = [float(np.log(t)) for t in time_ticks]

# Probability tick values for y-axis labels
prob_ticks = [0.01, 0.05, 0.10, 0.20, 0.50, 0.632, 0.90, 0.99]
weibull_ticks = [float(np.log(-np.log(1 - p))) for p in prob_ticks]
prob_labels = ["1%", "5%", "10%", "20%", "50%", "63.2%", "90%", "99%"]

# Build formatter JS functions
x_map_entries = ",".join(f"'{ln_t:.4f}':'{t:,}'" for t, ln_t in zip(time_ticks, ln_time_ticks, strict=True))
x_formatter = CallbackFunction.from_js_literal(
    f"function() {{ var m = {{{x_map_entries}}}; "
    "var k = this.value.toFixed(4); return m[k] || Math.round(Math.exp(this.value)); }"
)

y_map_entries = ",".join(f"'{w:.4f}':'{p}'" for p, w in zip(prob_labels, weibull_ticks, strict=True))
y_formatter = CallbackFunction.from_js_literal(
    f"function() {{ var m = {{{y_map_entries}}}; var k = this.value.toFixed(4); return m[k] || ''; }}"
)

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "marginTop": 180,
    "marginBottom": 300,
    "marginLeft": 280,
    "marginRight": 340,
    "plotBorderWidth": 1,
    "plotBorderColor": "rgba(0, 0, 0, 0.08)",
    "plotBackgroundColor": "#ffffff",
}

chart.options.title = {
    "text": "probability-weibull \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "60px", "fontWeight": "600", "color": "#2c3e50", "letterSpacing": "1px"},
    "margin": 50,
}

chart.options.subtitle = {
    "text": (f"Turbine Blade Fatigue Life \u2014 \u03b2 = {beta:.2f}, \u03b7 = {eta:.0f} hours"),
    "style": {"fontSize": "38px", "color": "#7f8c8d", "fontWeight": "400"},
}

# X-axis (ln scale with time labels)
x_axis = XAxis()
x_axis.title = {
    "text": "Time to Failure (hours)",
    "style": {"fontSize": "44px", "color": "#34495e", "fontWeight": "500"},
    "margin": 30,
}
x_labels = AxisLabelOptions()
x_labels.style = {"fontSize": "34px", "color": "#7f8c8d"}
x_labels.formatter = x_formatter
x_axis.labels = x_labels
x_axis.tick_positions = ln_time_ticks
x_axis.min = float(np.log(800))
x_axis.max = float(np.log(20000))
x_axis.grid_line_width = 1
x_axis.grid_line_color = "rgba(0, 0, 0, 0.06)"
x_axis.grid_line_dash_style = "Dot"
x_axis.line_width = 0
x_axis.tick_width = 0
chart.options.x_axis = x_axis

# Y-axis (Weibull linearized scale with probability labels)
y_axis = YAxis()
y_axis.title = {
    "text": "Cumulative Failure Probability",
    "style": {"fontSize": "44px", "color": "#34495e", "fontWeight": "500"},
    "margin": 30,
}
y_labels = AxisLabelOptions()
y_labels.style = {"fontSize": "34px", "color": "#7f8c8d"}
y_labels.formatter = y_formatter
y_axis.labels = y_labels
y_axis.tick_positions = weibull_ticks
y_axis.grid_line_width = 1
y_axis.grid_line_color = "rgba(0, 0, 0, 0.06)"
y_axis.grid_line_dash_style = "Dot"
y_axis.line_width = 0
y_axis.tick_width = 0
y_axis.plot_lines = [
    {
        "value": y_632,
        "color": "rgba(231, 76, 60, 0.6)",
        "width": 3,
        "dashStyle": "LongDash",
        "label": {
            "text": "63.2% \u2014 Characteristic Life",
            "style": {"fontSize": "30px", "color": "rgba(231, 76, 60, 0.8)", "fontWeight": "500"},
            "align": "left",
            "x": 15,
            "y": -12,
        },
        "zIndex": 4,
    }
]
chart.options.y_axis = y_axis

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -40,
    "y": 80,
    "floating": True,
    "backgroundColor": "rgba(255, 255, 255, 0.90)",
    "borderWidth": 1,
    "borderColor": "#e0e0e0",
    "borderRadius": 8,
    "itemStyle": {"fontSize": "30px", "fontWeight": "400", "color": "#34495e"},
    "padding": 16,
    "symbolRadius": 6,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:24px;color:{point.color}">\u25cf</span> '
        '<span style="font-size:26px">'
        "Time: <b>{point.x:.2f}</b> (ln hours)<br/>"
        "Weibull Y: <b>{point.y:.3f}</b></span>"
    ),
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#306998",
    "borderRadius": 10,
    "borderWidth": 2,
    "style": {"fontSize": "26px"},
}

# Failure data points (filled markers)
failures = ScatterSeries()
failures.data = [[x, y] for x, y in zip(failure_plot_x, failure_plot_y, strict=True)]
failures.name = "Failures"
failures.color = "#306998"
failures.marker = {
    "radius": 14,
    "symbol": "circle",
    "lineWidth": 2,
    "lineColor": "#ffffff",
    "fillColor": "#306998",
    "states": {"hover": {"radiusPlus": 4, "lineWidthPlus": 1}},
}
failures.z_index = 3

# Censored data points (hollow markers)
censored = ScatterSeries()
censored.data = [[x, y] for x, y in zip(censored_plot_x, censored_plot_y, strict=True)]
censored.name = "Censored (suspended)"
censored.color = "#e67e22"
censored.marker = {
    "radius": 14,
    "symbol": "circle",
    "lineWidth": 3,
    "lineColor": "#e67e22",
    "fillColor": "#fafbfc",
    "states": {"hover": {"radiusPlus": 4}},
}
censored.z_index = 3

# Fitted Weibull line
fit_line = SplineSeries()
fit_line.data = [[float(x_range[0]), float(y_fit[0])], [float(x_range[1]), float(y_fit[1])]]
fit_line.name = f"Weibull Fit (\u03b2={beta:.2f}, \u03b7={eta:.0f}h)"
fit_line.color = "#e74c3c"
fit_line.line_width = 4
fit_line.dash_style = "Solid"
fit_line.marker = {"enabled": False}
fit_line.enable_mouse_tracking = False
fit_line.z_index = 2

# Characteristic life vertical marker
eta_line = SplineSeries()
eta_line.data = [[float(ln_eta), float(min(weibull_ticks) - 0.3)], [float(ln_eta), float(y_632)]]
eta_line.name = f"\u03b7 = {eta:.0f}h"
eta_line.color = "rgba(231, 76, 60, 0.4)"
eta_line.line_width = 3
eta_line.dash_style = "ShortDot"
eta_line.marker = {"enabled": False}
eta_line.enable_mouse_tracking = False
eta_line.z_index = 1

chart.add_series(failures)
chart.add_series(censored)
chart.add_series(fit_line)
chart.add_series(eta_line)

# Download Highcharts JS
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
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
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
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

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
