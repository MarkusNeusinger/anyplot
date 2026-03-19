""" pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: highcharts unknown | Python 3.14.3
Quality: 86/100 | Created: 2026-03-19
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
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

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#f8f9fb",
    "marginBottom": 320,
    "marginLeft": 280,
    "marginRight": 200,
    "marginTop": 240,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

chart.options.title = {
    "text": "Shaft Diameter Process Capability · histogram-capability · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "700", "color": "#1a1a2e"},
    "margin": 30,
}

chart.options.subtitle = {
    "text": (
        f"n = {len(measurements)} measurements  ·  "
        f"Cp = {cp:.2f}  ·  Cpk = {cpk:.2f}  ·  "
        f"Mean = {mean_val:.4f} mm  ·  σ = {sigma:.4f} mm"
    ),
    "style": {"fontSize": "38px", "color": "#555555", "fontWeight": "400"},
}

# X-axis with specification limit lines
chart.options.x_axis = {
    "title": {
        "text": "Shaft Diameter (mm)",
        "style": {"fontSize": "44px", "color": "#333333", "fontWeight": "600"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#444444"}},
    "tickInterval": 0.02,
    "plotLines": [
        {
            "value": lsl,
            "color": "#c0392b",
            "width": 5,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": f"LSL = {lsl}",
                "style": {"fontSize": "34px", "color": "#c0392b", "fontWeight": "700"},
                "align": "left",
                "rotation": 0,
                "x": 15,
                "y": 50,
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
                "style": {"fontSize": "34px", "color": "#c0392b", "fontWeight": "700"},
                "align": "right",
                "rotation": 0,
                "x": -15,
                "y": 50,
            },
        },
        {
            "value": target,
            "color": "#8e44ad",
            "width": 5,
            "dashStyle": "ShortDot",
            "zIndex": 5,
            "label": {
                "text": f"Target = {target}",
                "style": {"fontSize": "34px", "color": "#8e44ad", "fontWeight": "700"},
                "align": "right",
                "rotation": 0,
                "x": -15,
                "y": 50,
            },
        },
        {
            "value": mean_val,
            "color": "#2980b9",
            "width": 4,
            "dashStyle": "LongDash",
            "zIndex": 5,
            "label": {
                "text": f"Mean = {mean_val:.4f}",
                "style": {"fontSize": "30px", "color": "#2980b9", "fontWeight": "700"},
                "align": "left",
                "rotation": 0,
                "x": 15,
                "y": 100,
            },
        },
    ],
}

# Y-axis
chart.options.y_axis = {
    "title": {
        "text": "Frequency",
        "style": {"fontSize": "44px", "color": "#333333", "fontWeight": "600"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "36px", "color": "#444444"}},
    "min": 0,
    "gridLineColor": "#e8e8e8",
    "gridLineWidth": 1,
    "gridLineDashStyle": "ShortDash",
}

# Plot options
chart.options.plot_options = {
    "column": {"pointPadding": 0, "groupPadding": 0, "borderWidth": 1, "borderColor": "#1a4a6e", "opacity": 0.9},
    "spline": {"lineWidth": 5, "marker": {"enabled": False}},
}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "right",
    "verticalAlign": "top",
    "floating": True,
    "itemStyle": {"fontSize": "34px", "fontWeight": "500", "color": "#333333"},
    "symbolWidth": 50,
    "symbolHeight": 24,
    "itemDistance": 60,
    "backgroundColor": "rgba(255,255,255,0.85)",
    "borderColor": "#e0e0e0",
    "borderWidth": 1,
    "borderRadius": 6,
    "padding": 16,
    "x": -40,
    "y": 10,
}

chart.options.credits = {"enabled": False}

# Histogram as column series with explicit bin data
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
normal_series.color = "#e67e22"

chart.add_series(hist_series)
chart.add_series(normal_series)

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
