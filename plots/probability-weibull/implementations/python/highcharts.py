""" anyplot.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-07
"""

import os
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
from PIL import Image
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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

# Reference positions
y_632 = np.log(-np.log(1 - 0.632))
ln_eta = float(np.log(eta))

# Actual time tick values for x-axis labels
time_ticks = [1000, 2000, 3000, 5000, 8000, 12000, 18000]
ln_time_ticks = [float(np.log(t)) for t in time_ticks]

# Probability tick values for y-axis labels
prob_ticks = [0.01, 0.05, 0.10, 0.20, 0.50, 0.632, 0.90, 0.99]
weibull_ticks = [float(np.log(-np.log(1 - p))) for p in prob_ticks]
prob_labels = ["1%", "5%", "10%", "20%", "50%", "63.2%", "90%", "99%"]

# JS formatter for x-axis (display original hours, not ln values)
x_map_entries = ",".join(f"'{ln_t:.4f}':'{t:,}'" for t, ln_t in zip(time_ticks, ln_time_ticks, strict=True))
x_formatter = CallbackFunction.from_js_literal(
    f"function() {{ var m = {{{x_map_entries}}}; "
    "var k = this.value.toFixed(4); return m[k] || Math.round(Math.exp(this.value)); }"
)

# JS formatter for y-axis (display cumulative probability %)
y_map_entries = ",".join(f"'{w:.4f}':'{p}'" for p, w in zip(prob_labels, weibull_ticks, strict=True))
y_formatter = CallbackFunction.from_js_literal(
    f"function() {{ var m = {{{y_map_entries}}}; var k = this.value.toFixed(4); return m[k] || ''; }}"
)

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif", "color": INK},
    "marginTop": 160,
    "marginBottom": 240,
    "marginLeft": 240,
    "marginRight": 200,
    "plotBorderWidth": 1,
    "plotBorderColor": GRID,
    "plotBackgroundColor": PAGE_BG,
}

chart.options.title = {
    "text": "probability-weibull · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "600", "color": INK},
    "margin": 40,
}

chart.options.subtitle = {
    "text": f"Turbine Blade Fatigue Life — β = {beta:.2f}, η = {eta:.0f} hours",
    "style": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "400"},
}

# X-axis (Weibull: ln(time) internally, displayed as original hours)
x_axis = XAxis()
x_axis.title = {
    "text": "Time to Failure (hours)",
    "style": {"fontSize": "56px", "color": INK, "fontWeight": "500"},
    "margin": 24,
}
x_labels = AxisLabelOptions()
x_labels.style = {"fontSize": "44px", "color": INK_SOFT}
x_labels.formatter = x_formatter
x_axis.labels = x_labels
x_axis.tick_positions = ln_time_ticks
x_axis.min = float(np.log(800))
x_axis.max = float(np.log(20000))
x_axis.grid_line_width = 1
x_axis.grid_line_color = GRID
x_axis.grid_line_dash_style = "Dot"
x_axis.line_width = 0
x_axis.tick_width = 0
# Vertical reference line at η (characteristic life) — plotLine avoids a redundant legend entry
x_axis.plot_lines = [
    {
        "value": ln_eta,
        "color": IMPRINT_PALETTE[4],
        "width": 2,
        "dashStyle": "ShortDot",
        "label": {
            "text": f"η = {eta:.0f}h",
            "style": {"fontSize": "36px", "color": INK_SOFT, "fontWeight": "400"},
            "align": "right",
            "rotation": 270,
            "x": -8,
            "y": 90,
        },
        "zIndex": 3,
    }
]
chart.options.x_axis = x_axis

# Y-axis (Weibull linearized cumulative probability scale)
y_axis = YAxis()
y_axis.title = {
    "text": "Cumulative Failure Probability",
    "style": {"fontSize": "56px", "color": INK, "fontWeight": "500"},
    "margin": 24,
}
y_labels = AxisLabelOptions()
y_labels.style = {"fontSize": "44px", "color": INK_SOFT}
y_labels.formatter = y_formatter
y_axis.labels = y_labels
y_axis.tick_positions = weibull_ticks
y_axis.grid_line_width = 1
y_axis.grid_line_color = GRID
y_axis.grid_line_dash_style = "Dot"
y_axis.line_width = 0
y_axis.tick_width = 0
# Horizontal reference line at 63.2% (characteristic life threshold)
y_axis.plot_lines = [
    {
        "value": y_632,
        "color": IMPRINT_PALETTE[4],
        "width": 3,
        "dashStyle": "LongDash",
        "label": {
            "text": "63.2% — Characteristic Life",
            "style": {"fontSize": "36px", "color": IMPRINT_PALETTE[4], "fontWeight": "500"},
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
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "itemStyle": {"fontSize": "44px", "fontWeight": "400", "color": INK_SOFT},
    "padding": 16,
    "symbolRadius": 6,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:34px;color:{point.color}">●</span> '
        '<span style="font-size:36px">'
        "Time: <b>{point.x:.2f}</b> (ln hours)<br/>"
        "Weibull Y: <b>{point.y:.3f}</b></span>"
    ),
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 10,
    "borderWidth": 1,
    "style": {"fontSize": "36px"},
}

# Failure data points — Imprint position 1 (#009E73), always first series
failures = ScatterSeries()
failures.data = [[x, y] for x, y in zip(failure_plot_x, failure_plot_y, strict=True)]
failures.name = "Failures"
failures.color = IMPRINT_PALETTE[0]
failures.marker = {
    "radius": 12,
    "symbol": "circle",
    "lineWidth": 2,
    "lineColor": PAGE_BG,
    "fillColor": IMPRINT_PALETTE[0],
    "states": {"hover": {"radiusPlus": 3, "lineWidthPlus": 1}},
}
failures.z_index = 3

# Censored data points (hollow markers) — Imprint position 2 (#C475FD)
censored = ScatterSeries()
censored.data = [[x, y] for x, y in zip(censored_plot_x, censored_plot_y, strict=True)]
censored.name = "Censored (suspended)"
censored.color = IMPRINT_PALETTE[1]
censored.marker = {
    "radius": 12,
    "symbol": "circle",
    "lineWidth": 3,
    "lineColor": IMPRINT_PALETTE[1],
    "fillColor": PAGE_BG,
    "states": {"hover": {"radiusPlus": 3}},
}
censored.z_index = 3

# Fitted Weibull line — Imprint position 3 (#4467A3)
fit_line = SplineSeries()
fit_line.data = [[float(x_range[0]), float(y_fit[0])], [float(x_range[1]), float(y_fit[1])]]
fit_line.name = f"Weibull Fit (β={beta:.2f}, η={eta:.0f}h)"
fit_line.color = IMPRINT_PALETTE[2]
fit_line.line_width = 4
fit_line.dash_style = "Solid"
fit_line.marker = {"enabled": False}
fit_line.enable_mouse_tracking = False
fit_line.z_index = 2

chart.add_series(failures)
chart.add_series(censored)
chart.add_series(fit_line)

# Download Highcharts JS (must be inline — headless Chrome blocks CDN from file://)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact for the interactive site view
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for the PNG artifact
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative — --window-size alone loses ~139 px to Chrome chrome in headless mode
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dimensions (guards against sub-pixel rounding)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
