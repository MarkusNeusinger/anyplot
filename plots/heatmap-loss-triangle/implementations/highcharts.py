""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: highcharts unknown | Python 3.14.3
Quality: 91/100 | Created: 2026-03-09
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from highcharts_core.utility_classes.javascript_functions import CallbackFunction
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Cumulative paid claims triangle (10 accident years x 10 development periods)
np.random.seed(42)

accident_years = list(range(2015, 2025))
development_periods = list(range(1, 11))
n_years = len(accident_years)
n_periods = len(development_periods)

# Base initial claims for each accident year (increasing over time)
base_claims = np.array([3200, 3500, 3800, 4100, 4500, 4900, 5300, 5700, 6100, 6500])

# Development factors (decreasing as claims mature)
dev_factors = np.array([1.0, 2.15, 1.45, 1.22, 1.12, 1.07, 1.04, 1.025, 1.015, 1.008])

# Build cumulative triangle
cumulative = np.zeros((n_years, n_periods))
for i in range(n_years):
    cumulative[i, 0] = base_claims[i] + np.random.normal(0, 200)
    for j in range(1, n_periods):
        noise = 1 + np.random.normal(0, 0.02)
        cumulative[i, j] = cumulative[i, j - 1] * dev_factors[j] * noise

cumulative = np.round(cumulative, 0)

# Determine actual vs projected: actual if accident_year_index + dev_period_index < n_years
is_actual = np.zeros((n_years, n_periods), dtype=bool)
for i in range(n_years):
    for j in range(n_periods):
        if i + j < n_years:
            is_actual[i, j] = True

# Age-to-age development factors (column averages from actual data)
age_to_age = []
for j in range(1, n_periods):
    factors = []
    for i in range(n_years):
        if is_actual[i, j] and is_actual[i, j - 1]:
            factors.append(cumulative[i, j] / cumulative[i, j - 1])
    age_to_age.append(round(np.mean(factors), 3) if factors else dev_factors[j])

# Prepare heatmap data with per-point styling
actual_data = []
projected_data = []
all_values = cumulative.flatten()
val_min = float(np.min(all_values))
val_max = float(np.max(all_values))

for i in range(n_years):
    for j in range(n_periods):
        val = float(cumulative[i, j])
        point = {"x": j, "y": i, "value": val}
        if is_actual[i, j]:
            actual_data.append(point)
        else:
            projected_data.append(point)

# JavaScript callback functions
threshold = int((val_min + val_max) / 2)

datalabel_fn = CallbackFunction.from_js_literal(
    f"""function() {{
    var val = Highcharts.numberFormat(this.point.value, 0, '.', ',');
    var isProjected = (this.series.name === 'Projected (IBNR)');
    var color = this.point.value > {threshold} ? '#ffffff' : '#1a1a2e';
    if (isProjected) {{
        return '<span style="color:' + color + ';font-size:28px;font-style:italic;letter-spacing:0.3px">' + val + '</span>';
    }}
    return '<span style="color:' + color + ';font-size:28px;font-weight:700;letter-spacing:0.3px">' + val + '</span>';
}}"""
)

tooltip_fn = CallbackFunction.from_js_literal(
    """function() {
    var year = this.series.yAxis.categories[this.point.y];
    var period = this.series.xAxis.categories[this.point.x];
    var val = Highcharts.numberFormat(this.point.value, 0, '.', ',');
    return '<b>Accident Year: ' + year + '</b><br>' +
           'Development Period: <b>' + period + '</b><br>' +
           'Cumulative Claims: <b>$' + val + 'K</b><br>' +
           'Type: <b>' + this.series.name + '</b>';
}"""
)

coloraxis_fn = CallbackFunction.from_js_literal(
    """function() {
    return Highcharts.numberFormat(this.value, 0, '.', ',');
}"""
)

# Build age-to-age factor rendering JS
factor_labels = [
    f"{development_periods[k]}\u2192{development_periods[k + 1]}: {f:.3f}" for k, f in enumerate(age_to_age)
]
factor_box_js = []
for idx, (k, f) in enumerate(enumerate(age_to_age)):
    label = f"{development_periods[k]}\u2192{development_periods[k + 1]}"
    value = f"{f:.3f}"
    col_x = f"x + {idx} * spacing"
    factor_box_js.append(
        f"chart.renderer.rect({col_x}, fy, boxW, 56, 6)"
        f".attr({{fill: '#e8eef4', stroke: '#c0cdd8', 'stroke-width': 1}}).add();"
        f"chart.renderer.text('{label}', {col_x} + boxW/2, fy + 22)"
        f".attr({{align: 'center'}})"
        f".css({{fontSize: '20px', color: '#667788', fontWeight: '500'}}).add();"
        f"chart.renderer.text('{value}', {col_x} + boxW/2, fy + 46)"
        f".attr({{align: 'center'}})"
        f".css({{fontSize: '24px', color: '#1a1a2e', fontWeight: '700'}}).add();"
    )
factors_render = "\n    ".join(factor_box_js)

load_fn = CallbackFunction.from_js_literal(
    f"""function() {{
    var chart = this;
    var x = chart.plotLeft;
    var plotRight = chart.plotLeft + chart.plotWidth;
    var totalW = plotRight - x;

    // Separator line between chart and factors
    var sepY = chart.plotTop + chart.plotHeight + 50;
    chart.renderer.path(['M', x, sepY, 'L', plotRight, sepY])
        .attr({{stroke: '#d0d5dd', 'stroke-width': 1.5, 'stroke-dasharray': '8,4'}}).add();

    // Age-to-Age Development Factors header
    var fy = chart.plotTop + chart.plotHeight + 95;
    chart.renderer.text('Age-to-Age Development Factors', x, fy - 10)
        .css({{fontSize: '26px', color: '#2d2d44', fontWeight: '700'}}).add();

    // Factor boxes
    fy = fy + 10;
    var spacing = Math.floor(totalW / 9);
    var boxW = spacing - 10;
    {factors_render}

    // Actual vs Projected legend
    var ly = fy + 100;
    chart.renderer.rect(x, ly, 40, 28, 4)
        .attr({{fill: '#4a9bbe', stroke: '#ffffff', 'stroke-width': 3}}).add();
    chart.renderer.text('Actual (Observed)', x + 52, ly + 20)
        .css({{fontSize: '24px', color: '#2d2d44', fontWeight: '600'}}).add();

    chart.renderer.rect(x + 340, ly, 40, 28, 4)
        .attr({{fill: '#4a9bbe', stroke: '#c9952e', 'stroke-width': 3}}).add();
    chart.renderer.text('Projected (IBNR Estimate)', x + 392, ly + 20)
        .css({{fontSize: '24px', color: '#2d2d44', fontWeight: '600', fontStyle: 'italic'}}).add();
}}"""
)

# Build chart using highcharts-core Python API
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "marginTop": 180,
    "marginBottom": 440,
    "marginLeft": 220,
    "marginRight": 280,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "events": {"load": load_fn},
}

chart.options.title = {
    "text": "heatmap-loss-triangle \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "44px", "fontWeight": "700", "color": "#1a1a2e"},
    "y": 35,
}

chart.options.subtitle = {
    "text": "Cumulative Paid Claims ($K) \u2014 Actual vs Projected (IBNR)",
    "style": {"fontSize": "28px", "color": "#555566", "fontWeight": "400"},
    "y": 80,
}

chart.options.x_axis = {
    "categories": [str(p) for p in development_periods],
    "title": {
        "text": "Development Period (Years)",
        "style": {"fontSize": "28px", "color": "#2d2d44", "fontWeight": "600"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "24px", "color": "#444455"}},
    "lineColor": "#ccccdd",
    "tickColor": "#ccccdd",
}

chart.options.y_axis = {
    "categories": [str(y) for y in accident_years],
    "title": {"text": "Accident Year", "style": {"fontSize": "28px", "color": "#2d2d44", "fontWeight": "600"}},
    "labels": {"style": {"fontSize": "24px", "color": "#444455"}},
    "reversed": True,
    "lineColor": "#ccccdd",
    "tickColor": "#ccccdd",
}

chart.options.color_axis = {
    "min": val_min,
    "max": val_max,
    "stops": [
        [0, "#e8f4f8"],
        [0.1, "#b8dce8"],
        [0.25, "#7bbcd4"],
        [0.4, "#4a9bbe"],
        [0.55, "#2e7da8"],
        [0.7, "#1a5f8b"],
        [0.85, "#0d4170"],
        [1, "#052c54"],
    ],
    "labels": {"style": {"fontSize": "22px", "color": "#444455"}, "formatter": coloraxis_fn},
}

chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 380,
    "itemStyle": {"fontSize": "22px", "color": "#444455"},
    "title": {
        "text": "Cumulative<br/>Claims ($K)",
        "style": {"fontSize": "22px", "fontWeight": "600", "color": "#2d2d44"},
    },
}

chart.options.tooltip = {"formatter": tooltip_fn, "style": {"fontSize": "22px"}, "useHTML": True}

chart.options.credits = {"enabled": False}

chart.options.plot_options = {"heatmap": {"dataLabels": {"enabled": True, "formatter": datalabel_fn, "useHTML": True}}}

# Add series using HeatmapSeries
actual_series = HeatmapSeries()
actual_series.name = "Actual Claims"
actual_series.data = actual_data
actual_series.border_width = 3
actual_series.border_color = "#ffffff"

projected_series = HeatmapSeries()
projected_series.name = "Projected (IBNR)"
projected_series.data = projected_data
projected_series.border_width = 4
projected_series.border_color = "#c9952e"

chart.add_series(actual_series)
chart.add_series(projected_series)

# Generate JS literal from the Chart object
js_literal = chart.to_js_literal()

# Download Highcharts JS and heatmap module
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/heatmap.js"
headers = {"User-Agent": "Mozilla/5.0"}

req = urllib.request.Request(highcharts_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request(heatmap_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0;background:#fafbfc;">
    <div id="container" style="width:4800px;height:2700px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
