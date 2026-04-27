""" anyplot.ai
qq-basic: Basic Q-Q Plot
Library: highcharts unknown | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-27
"""

import os
import tempfile
import time
from pathlib import Path
from statistics import NormalDist

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
# Warm accent for tail-deviation bands — Okabe-Ito orange, theme-adaptive opacity
BAND_COLOR = "rgba(213,94,0,0.12)" if THEME == "light" else "rgba(230,159,0,0.22)"

# Data - mixed normal to demonstrate Q-Q characteristics (slight right skew)
np.random.seed(42)
sample = np.concatenate([np.random.randn(80) * 15 + 50, np.random.randn(20) * 10 + 75])
np.random.shuffle(sample)

# Calculate Q-Q values
sample_sorted = np.sort(sample)
n_points = len(sample_sorted)
_nd = NormalDist()
theoretical_quantiles = np.array([_nd.inv_cdf((i + 0.5) / n_points) for i in range(n_points)])
sample_mean = np.mean(sample)
sample_std = np.std(sample)
theoretical_scaled = theoretical_quantiles * sample_std + sample_mean

# Reference line endpoints with padding
line_min = min(theoretical_scaled.min(), sample_sorted.min())
line_max = max(theoretical_scaled.max(), sample_sorted.max())

# Axis bounds and tail thresholds — upper/lower 22% of the axis range
axis_lo = float(line_min - 5)
axis_hi = float(line_max + 5)
axis_range = axis_hi - axis_lo
upper_tail_from = axis_lo + 0.78 * axis_range
lower_tail_to = axis_lo + 0.22 * axis_range

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "spacingBottom": 30,
}

chart.options.title = {
    "text": "qq-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "Exam scores (N=100) vs. theoretical normal — right skew visible in upper tail",
    "style": {"fontSize": "36px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "title": {"text": "Theoretical Quantiles", "style": {"fontSize": "48px", "color": INK}},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dash",
    "min": axis_lo,
    "max": axis_hi,
    "plotBands": [
        {
            "from": upper_tail_from,
            "to": axis_hi,
            "color": BAND_COLOR,
            "label": {
                "text": "Upper-tail deviation",
                "align": "right",
                "x": -10,
                "style": {"color": INK, "fontSize": "30px"},
            },
        },
        {
            "from": axis_lo,
            "to": lower_tail_to,
            "color": BAND_COLOR,
            "label": {
                "text": "Lower-tail deviation",
                "align": "left",
                "x": 10,
                "style": {"color": INK, "fontSize": "30px"},
            },
        },
    ],
}

chart.options.y_axis = {
    "title": {"text": "Sample Quantiles", "style": {"fontSize": "48px", "color": INK}},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dash",
    "min": axis_lo,
    "max": axis_hi,
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
}
chart.options.credits = {"enabled": False}

# Reference line (45-degree, y = x on scaled theoretical quantiles)
line_series = LineSeries()
line_series.data = [[axis_lo, axis_lo], [axis_hi, axis_hi]]
line_series.name = "Reference Line (y=x)"
line_series.color = INK_SOFT
line_series.line_width = 6
line_series.marker = {"enabled": False}
line_series.enable_mouse_tracking = False
line_series.dash_style = "Dash"
chart.add_series(line_series)

# Q-Q scatter points — brand green (Okabe-Ito position 1)
scatter_series = ScatterSeries()
scatter_series.data = [[float(t), float(s)] for t, s in zip(theoretical_scaled, sample_sorted, strict=True)]
scatter_series.name = "Sample Quantiles (N=100)"
scatter_series.color = "rgba(0, 158, 115, 0.75)"
scatter_series.marker = {"radius": 18, "symbol": "circle"}
chart.add_series(scatter_series)

# Load Highcharts JS from local npm package (CDN blocked in CI; install via: npm install highcharts --prefix /tmp/hc-tmp)
highcharts_js = Path("/tmp/hc-tmp/node_modules/highcharts/highcharts.js").read_text(encoding="utf-8")

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

# Save HTML artifact (inline scripts so it works standalone)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and screenshot for PNG artifact
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
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
