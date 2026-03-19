""" pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: highcharts unknown | Python 3.14.3
Quality: 88/100 | Created: 2026-03-19
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSplineSeries
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.options.series.spline import SplineSeries
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data — shaft diameter measurements (mm) for process capability analysis
np.random.seed(42)
lsl = 9.95
usl = 10.05
target = 10.00
measurements = np.random.normal(loc=10.002, scale=0.012, size=200)

# Calculate capability indices
mean_val = float(np.mean(measurements))
sigma = float(np.std(measurements, ddof=1))
cp = (usl - lsl) / (6 * sigma)
cpk = min((usl - mean_val) / (3 * sigma), (mean_val - lsl) / (3 * sigma))

# Compute histogram bins manually
n_bins = 20
counts, bin_edges = np.histogram(measurements, bins=n_bins)
bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(len(counts))]
bin_width = float(bin_edges[1] - bin_edges[0])

# Fitted normal distribution curve scaled to histogram
x_curve = np.linspace(float(bin_edges[0]) - 2 * sigma, float(bin_edges[-1]) + 2 * sigma, 150)
y_curve = stats.norm.pdf(x_curve, mean_val, sigma) * len(measurements) * bin_width

# Capability zone bands (in-spec vs out-of-spec shading via plotBands)
plot_bands = [{"from": lsl, "to": usl, "color": "rgba(46, 204, 113, 0.07)", "zIndex": 0}]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfd",
    "marginBottom": 280,
    "marginLeft": 260,
    "marginRight": 180,
    "marginTop": 260,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

chart.options.title = {
    "text": "Shaft Diameter Process Capability · histogram-capability · highcharts · pyplots.ai",
    "style": {"fontSize": "54px", "fontWeight": "700", "color": "#1a1a2e", "letterSpacing": "0.3px"},
    "margin": 20,
}

chart.options.subtitle = {
    "text": (
        f"n = {len(measurements)}  ·  "
        f"Cp = {cp:.2f}  ·  Cpk = {cpk:.2f}  ·  "
        f"Mean = {mean_val:.4f} mm  ·  σ = {sigma:.4f} mm"
    ),
    "style": {"fontSize": "36px", "color": "#666666", "fontWeight": "400"},
}

# X-axis — combine Target & Mean into one label to avoid crowding
target_mean_label = f"Target = {target} · Mean = {mean_val:.4f}"

chart.options.x_axis = {
    "title": {
        "text": "Shaft Diameter (mm)",
        "style": {"fontSize": "42px", "color": "#444444", "fontWeight": "600"},
        "margin": 24,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#555555"}},
    "tickInterval": 0.01,
    "lineColor": "#cccccc",
    "lineWidth": 1,
    "tickColor": "#cccccc",
    "plotBands": plot_bands,
    "plotLines": [
        {
            "value": lsl,
            "color": "#c0392b",
            "width": 5,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": f"LSL = {lsl}",
                "style": {"fontSize": "32px", "color": "#c0392b", "fontWeight": "700"},
                "align": "left",
                "rotation": 0,
                "x": 18,
                "y": 55,
            },
        },
        {
            "value": usl,
            "color": "#c0392b",
            "width": 5,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": f"USL = {usl}",
                "style": {"fontSize": "32px", "color": "#c0392b", "fontWeight": "700"},
                "align": "right",
                "rotation": 0,
                "x": -18,
                "y": 55,
            },
        },
        {
            "value": target,
            "color": "#8e44ad",
            "width": 4,
            "dashStyle": "ShortDot",
            "zIndex": 5,
            "label": {
                "text": target_mean_label,
                "style": {"fontSize": "28px", "color": "#8e44ad", "fontWeight": "600"},
                "align": "center",
                "rotation": 0,
                "y": 90,
            },
        },
        {"value": mean_val, "color": "#2980b9", "width": 4, "dashStyle": "LongDash", "zIndex": 5},
    ],
}

# Y-axis — use tickInterval to reduce clutter, remove right spine
chart.options.y_axis = {
    "title": {
        "text": "Frequency",
        "style": {"fontSize": "42px", "color": "#444444", "fontWeight": "600"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#555555"}},
    "min": 0,
    "tickInterval": 5,
    "gridLineColor": "#e6e6e6",
    "gridLineWidth": 1,
    "gridLineDashStyle": "Dot",
    "lineColor": "#cccccc",
    "lineWidth": 1,
    "opposite": False,
}

# Plot options — softer borders, rounded columns for polish
chart.options.plot_options = {
    "column": {
        "pointPadding": 0,
        "groupPadding": 0,
        "borderWidth": 1,
        "borderColor": "rgba(26, 74, 110, 0.4)",
        "borderRadius": 2,
    },
    "spline": {"lineWidth": 5, "marker": {"enabled": False}},
    "areaspline": {"lineWidth": 0, "marker": {"enabled": False}, "fillOpacity": 0.12},
}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "right",
    "verticalAlign": "top",
    "floating": True,
    "itemStyle": {"fontSize": "32px", "fontWeight": "500", "color": "#444444"},
    "symbolWidth": 48,
    "symbolHeight": 20,
    "itemDistance": 50,
    "backgroundColor": "rgba(255,255,255,0.9)",
    "borderColor": "#e0e0e0",
    "borderWidth": 1,
    "borderRadius": 8,
    "padding": 18,
    "shadow": {"enabled": True, "color": "rgba(0,0,0,0.04)", "offsetX": 1, "offsetY": 2, "width": 4},
    "x": -30,
    "y": 5,
}

chart.options.credits = {"enabled": False}

# Tooltip with Highcharts crosshair for interactive HTML version
chart.options.tooltip = {"shared": True, "borderRadius": 8, "style": {"fontSize": "28px"}}

# Histogram as column series
hist_data = [{"x": round(float(bin_centers[i]), 5), "y": int(counts[i])} for i in range(len(counts))]

hist_series = ColumnSeries()
hist_series.name = "Measurement Distribution"
hist_series.data = hist_data
hist_series.color = "#306998"
hist_series.point_width = int(4800 * 0.6 / n_bins)

# Normal curve as spline series
curve_data = [[round(float(x), 5), round(float(y), 2)] for x, y in zip(x_curve, y_curve, strict=False)]

normal_series = SplineSeries()
normal_series.name = "Fitted Normal Curve"
normal_series.data = curve_data
normal_series.color = "#d35400"

# Area fill under the normal curve for visual depth
area_series = AreaSplineSeries()
area_series.name = "Distribution Envelope"
area_series.data = curve_data
area_series.color = "#d35400"
area_series.show_in_legend = False
area_series.enable_mouse_tracking = False

chart.add_series(hist_series)
chart.add_series(normal_series)
chart.add_series(area_series)

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
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML for interactive version
Path("plot.html").write_text(html_content, encoding="utf-8")

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
