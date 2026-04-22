""" pyplots.ai
raincloud-basic: Basic Raincloud Plot
Library: highcharts 1.10.3 | Python 3.14
Quality: 85/100 | Created: 2025-12-25
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.boxplot import BoxPlotSeries
from highcharts_core.options.series.polygon import PolygonSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Reaction times (ms) for different experimental conditions
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C"]
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]
colors_fill = [
    "rgba(48, 105, 152, 0.50)",
    "rgba(255, 212, 59, 0.50)",
    "rgba(148, 103, 189, 0.50)",
    "rgba(23, 190, 207, 0.50)",
]

# Generate realistic reaction time data with different distributions
control = np.random.normal(450, 60, 80)
treatment_a = np.random.normal(380, 50, 80)
treatment_b = np.concatenate([np.random.normal(350, 30, 40), np.random.normal(480, 35, 40)])
treatment_c = np.random.normal(420, 80, 80)

all_data = [control, treatment_a, treatment_b, treatment_c]

# Calculate statistics for box plots
box_data = []
for data in all_data:
    q1, median, q3 = np.percentile(data, [25, 50, 75])
    iqr = q3 - q1
    low = float(max(np.min(data), q1 - 1.5 * iqr))
    high = float(min(np.max(data), q3 + 1.5 * iqr))
    box_data.append({"low": low, "q1": float(q1), "median": float(median), "q3": float(q3), "high": high})


# KDE helper: vectorized Gaussian kernel with Silverman bandwidth
def kde(data_arr, n_points=80, padding=10):
    n = len(data_arr)
    std = np.std(data_arr)
    iqr_val = np.percentile(data_arr, 75) - np.percentile(data_arr, 25)
    bw = 0.9 * min(std, iqr_val / 1.34) * (n ** (-0.2))
    xs = np.linspace(data_arr.min() - padding, data_arr.max() + padding, n_points)
    # Vectorized: compute all kernels at once via broadcasting
    density = np.exp(-0.5 * ((xs[:, None] - data_arr[None, :]) / bw) ** 2).sum(axis=1)
    density /= n * bw * np.sqrt(2 * np.pi)
    return xs, density


# Compute axis range from actual data extent (tight fit to avoid wasted space)
all_values = np.concatenate(all_data)
data_min, data_max = float(np.min(all_values)), float(np.max(all_values))
y_min = int(np.floor(data_min / 50) * 50)  # Align to tick interval of 50
y_max = int(np.ceil(data_max / 50) * 50)

# Create chart — HORIZONTAL orientation using inverted chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "inverted": True,
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafafa",
    "marginBottom": 200,
    "marginLeft": 420,
    "marginRight": 220,
    "marginTop": 200,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

# Title
chart.options.title = {
    "text": "raincloud-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "60px", "fontWeight": "700", "color": "#1a1a2e", "letterSpacing": "0.5px"},
    "margin": 30,
}

# Subtitle
chart.options.subtitle = {
    "text": "Reaction Time Distributions Across Experimental Conditions",
    "style": {"fontSize": "38px", "color": "#636e72", "fontWeight": "300"},
}

# X-axis: categories (displayed vertically on left side due to inverted mode)
chart.options.x_axis = {
    "title": {
        "text": "Experimental Condition",
        "style": {"fontSize": "40px", "color": "#2d3436", "fontWeight": "600"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "36px", "color": "#2d3436", "fontWeight": "500"}},
    "categories": categories,
    "tickPositions": [0, 1, 2, 3],
    "min": -0.6,
    "max": 3.6,
    "lineWidth": 0,
    "tickWidth": 0,
    "gridLineWidth": 0,
}

# Y-axis: values (Reaction Time ms) — tight range matching data
chart.options.y_axis = {
    "title": {
        "text": "Reaction Time (ms)",
        "style": {"fontSize": "40px", "color": "#2d3436", "fontWeight": "600"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "34px", "color": "#636e72"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.05)",
    "gridLineDashStyle": "Dot",
    "tickInterval": 50,
    "min": y_min,
    "max": y_max,
    "startOnTick": False,
    "endOnTick": False,
    "lineWidth": 0,
}

# Legend — show component types for clarity
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px", "fontWeight": "400", "color": "#2d3436"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -40,
    "y": 80,
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderWidth": 0,
    "borderRadius": 12,
    "padding": 24,
    "symbolWidth": 36,
    "symbolHeight": 20,
    "shadow": {"enabled": True, "color": "rgba(0,0,0,0.06)", "offsetX": 0, "offsetY": 2, "width": 8},
    "title": {
        "text": "<span style='font-size:28px;color:#636e72;font-weight:400'>&#9729; Cloud &nbsp; &#9679; Rain &nbsp; &#9744; Box</span>",
        "style": {"fontSize": "28px"},
    },
}

# Plot options — refined box plot styling
chart.options.plot_options = {
    "boxplot": {
        "medianColor": "#1a1a2e",
        "medianWidth": 7,
        "stemColor": "#555",
        "stemWidth": 3,
        "stemDashStyle": "Solid",
        "whiskerColor": "#555",
        "whiskerWidth": 3,
        "whiskerLength": "50%",
        "lineWidth": 2.5,
        "pointWidth": 52,
        "fillOpacity": 0.92,
    },
    "scatter": {"marker": {"radius": 11, "symbol": "circle"}, "zIndex": 5},
    "polygon": {"fillOpacity": 0.50, "lineWidth": 2.5, "zIndex": 2},
    "series": {"animation": False},
}

# Tooltip disabled for static output
chart.options.tooltip = {"enabled": False}

# Credits disabled
chart.options.credits = {"enabled": False}

# Add half-violin "cloud" shapes ABOVE each category baseline
for i, data in enumerate(all_data):
    y_range, density = kde(np.array(data))
    density_norm = density / density.max() * 0.35

    # Cloud polygon: extends upward (negative x offset in inverted mode)
    polygon_points = [[float(i - d - 0.05), float(y)] for y, d in zip(y_range, density_norm, strict=True)]
    polygon_points += [[float(i - 0.05), float(y)] for y in reversed(y_range)]

    series = PolygonSeries()
    series.data = polygon_points
    series.name = categories[i]
    series.color = colors[i]
    series.fill_color = colors_fill[i]
    series.fill_opacity = 0.50
    series.line_width = 2.5
    series.line_color = colors[i]
    series.z_index = 2
    chart.add_series(series)

# Box plot series — white fill with dark outlines for clarity
box_series = BoxPlotSeries()
box_series.data = [
    {"x": i, "low": b["low"], "q1": b["q1"], "median": b["median"], "q3": b["q3"], "high": b["high"]}
    for i, b in enumerate(box_data)
]
box_series.name = "Box Plot"
box_series.color = "#2c3e50"
box_series.fill_color = "rgba(255, 255, 255, 0.92)"
box_series.show_in_legend = False
box_series.z_index = 8
chart.add_series(box_series)

# Jittered scatter "rain" points BELOW each category baseline
for i, data in enumerate(all_data):
    scatter_points = [[float(i + 0.2 + np.random.uniform(-0.06, 0.06)), float(val)] for val in data]

    scatter_series = ScatterSeries()
    scatter_series.data = scatter_points
    scatter_series.name = categories[i]
    scatter_series.color = colors[i]
    scatter_series.marker = {
        "radius": 11,
        "lineWidth": 1,
        "lineColor": "rgba(0,0,0,0.18)",
        "fillColor": colors[i],
        "states": {"hover": {"enabled": False}},
    }
    scatter_series.opacity = 0.6
    scatter_series.show_in_legend = False
    scatter_series.z_index = 5
    chart.add_series(scatter_series)

# Download Highcharts JS and required modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Annotation JS for data storytelling — injected after chart render
# Highlights bimodal Treatment B and the fastest Treatment A
annotation_js = """
setTimeout(function() {
    var chart = Highcharts.charts[0];
    if (!chart) return;

    // Annotation: Control baseline (category 0, ~top of plot)
    chart.renderer.label(
        '<span style="font-size:28px;color:#1e5a8a;font-weight:600;">&#9654; Baseline</span>' +
        '<br><span style="font-size:24px;color:#636e72;">Mean ~450 ms</span>',
        chart.plotLeft + chart.plotWidth * 0.78,
        chart.plotTop + chart.plotHeight * 0.02
    )
    .attr({
        fill: 'rgba(255,255,255,0.93)',
        stroke: '#306998',
        'stroke-width': 2,
        r: 10,
        padding: 16,
        zIndex: 20
    })
    .css({lineHeight: '36px'})
    .add();

    // Annotation: Treatment A fastest (category 1, ~25% down)
    chart.renderer.label(
        '<span style="font-size:28px;color:#b8860b;font-weight:600;">&#9654; Fastest responses</span>' +
        '<br><span style="font-size:24px;color:#636e72;">Mean ~380 ms, tight spread</span>',
        chart.plotLeft + chart.plotWidth * 0.05,
        chart.plotTop + chart.plotHeight * 0.32
    )
    .attr({
        fill: 'rgba(255,255,255,0.93)',
        stroke: '#FFD43B',
        'stroke-width': 2,
        r: 10,
        padding: 16,
        zIndex: 20
    })
    .css({lineHeight: '36px'})
    .add();

    // Annotation: Treatment B bimodal (category 2, ~50% down)
    chart.renderer.label(
        '<span style="font-size:28px;color:#7c3aed;font-weight:600;">&#9654; Bimodal distribution</span>' +
        '<br><span style="font-size:24px;color:#636e72;">Two distinct response clusters<br>at ~350 ms and ~480 ms</span>',
        chart.plotLeft + chart.plotWidth * 0.75,
        chart.plotTop + chart.plotHeight * 0.52
    )
    .attr({
        fill: 'rgba(255,255,255,0.93)',
        stroke: '#9467BD',
        'stroke-width': 2,
        r: 10,
        padding: 16,
        zIndex: 20
    })
    .css({lineHeight: '36px'})
    .add();
}, 500);
"""

# Generate HTML with inline scripts
html_str = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
    <script>{annotation_js}</script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Setup Chrome for screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
