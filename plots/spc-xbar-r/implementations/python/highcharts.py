""" pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: highcharts unknown | Python 3.14.3
Quality: 84/100 | Created: 2026-03-19
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Generate SPC data for CNC shaft diameter measurements
np.random.seed(42)

n_samples = 30
subgroup_size = 5
target_diameter = 25.000  # mm
process_std = 0.010  # mm

# Control chart constants for n=5
A2 = 0.577
D3 = 0.0
D4 = 2.114

# Generate subgroup measurements
measurements = np.random.normal(target_diameter, process_std, (n_samples, subgroup_size))

# Inject out-of-control points
measurements[7] += 0.025  # Shift up - sample 8
measurements[18] -= 0.030  # Shift down - sample 19
measurements[24] += 0.028  # Shift up - sample 25

# Calculate sample means and ranges
sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

# Calculate control limits
x_bar_bar = sample_means.mean()
r_bar = sample_ranges.mean()

xbar_ucl = x_bar_bar + A2 * r_bar
xbar_lcl = x_bar_bar - A2 * r_bar
xbar_uwl = x_bar_bar + (2 / 3) * A2 * r_bar
xbar_lwl = x_bar_bar - (2 / 3) * A2 * r_bar

r_ucl = D4 * r_bar
r_lcl = D3 * r_bar
r_uwl = r_bar + (2 / 3) * (r_ucl - r_bar)

# Separate out-of-control and normal points
xbar_ooc = []
xbar_all = []
for i in range(n_samples):
    val = round(float(sample_means[i]), 4)
    xbar_all.append([i + 1, val])
    if sample_means[i] > xbar_ucl or sample_means[i] < xbar_lcl:
        xbar_ooc.append([i + 1, val])

r_ooc = []
r_all = []
for i in range(n_samples):
    val = round(float(sample_ranges[i]), 4)
    r_all.append([i + 1, val])
    if sample_ranges[i] > r_ucl or sample_ranges[i] < r_lcl:
        r_ooc.append([i + 1, val])

sample_cats = [str(i + 1) for i in range(n_samples)]

# Colors - refined palette with better accessibility
BLUE = "#2563EB"
RED = "#DC2626"
AMBER = "#D97706"
TEAL = "#0D9488"
DARK = "#1E293B"
GRID = "rgba(148, 163, 184, 0.12)"

# Build series using highcharts_core Python API
xbar_line = LineSeries()
xbar_line.data = xbar_all
xbar_line.name = "X\u0304 (Sample Mean)"
xbar_line.x_axis = 0
xbar_line.y_axis = 0
xbar_line.color = BLUE
xbar_line.marker = {"fillColor": BLUE, "lineColor": "#ffffff", "lineWidth": 2, "radius": 7}
xbar_line.show_in_legend = True

xbar_scatter = ScatterSeries()
xbar_scatter.data = xbar_ooc
xbar_scatter.name = "Out of Control"
xbar_scatter.x_axis = 0
xbar_scatter.y_axis = 0
xbar_scatter.color = RED
xbar_scatter.marker = {"radius": 13, "symbol": "diamond", "fillColor": RED, "lineColor": "#ffffff", "lineWidth": 3}
xbar_scatter.show_in_legend = True

r_line = LineSeries()
r_line.data = r_all
r_line.name = "R (Sample Range)"
r_line.x_axis = 1
r_line.y_axis = 1
r_line.color = BLUE
r_line.marker = {"fillColor": BLUE, "lineColor": "#ffffff", "lineWidth": 2, "radius": 7}
r_line.show_in_legend = True

# Build chart with Python API and extract series config
chart = Chart(container="container")
chart.options = HighchartsOptions()
chart.add_series(xbar_line)
chart.add_series(xbar_scatter)
chart.add_series(r_line)
if r_ooc:
    r_scatter = ScatterSeries()
    r_scatter.data = r_ooc
    r_scatter.name = "Out of Control (R)"
    r_scatter.x_axis = 1
    r_scatter.y_axis = 1
    r_scatter.color = RED
    r_scatter.marker = {"radius": 13, "symbol": "diamond", "fillColor": RED, "lineColor": "#ffffff", "lineWidth": 3}
    r_scatter.show_in_legend = False
    chart.add_series(r_scatter)

# Extract series from Python API as dicts
series_dicts = []
for s in chart.options.series:
    series_dicts.append(s.to_dict())


# Plot lines helper
def make_plot_line(value, color, label_text, width=3, dash=None, align="right", y_off=-8):
    pl = {
        "value": round(float(value), 4),
        "color": color,
        "width": width,
        "zIndex": 3,
        "label": {
            "text": label_text,
            "align": align,
            "style": {"fontSize": "20px", "fontWeight": "bold", "color": color},
            "x": -15 if align == "right" else 12,
            "y": y_off,
        },
    }
    if dash:
        pl["dashStyle"] = dash
    return pl


# Full chart config dict with proper JSON serialization
chart_config = {
    "chart": {
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#FAFBFC",
        "spacing": [30, 200, 180, 80],
        "style": {"fontFamily": "Segoe UI, Helvetica Neue, Arial, sans-serif"},
    },
    "title": {
        "text": "CNC Shaft Diameter Monitoring \u00b7 spc-xbar-r \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "42px", "fontWeight": "600", "color": DARK},
        "margin": 30,
    },
    "credits": {"enabled": False},
    "legend": {
        "enabled": True,
        "itemStyle": {"fontSize": "22px", "fontWeight": "normal", "color": DARK},
        "symbolRadius": 6,
        "symbolWidth": 20,
        "verticalAlign": "top",
        "y": 55,
        "itemDistance": 40,
    },
    "xAxis": [
        {"categories": sample_cats, "visible": False, "lineWidth": 0, "min": 0, "max": n_samples - 1},
        {
            "categories": sample_cats,
            "title": {
                "text": "Sample Number",
                "style": {"fontSize": "26px", "fontWeight": "600", "color": DARK},
                "y": 20,
            },
            "labels": {"style": {"fontSize": "22px", "color": "#475569"}, "y": 28, "step": 1},
            "lineWidth": 2,
            "lineColor": DARK,
            "tickWidth": 2,
            "tickColor": DARK,
            "min": 0,
            "max": n_samples - 1,
        },
    ],
    "yAxis": [
        {
            "title": {
                "text": "X\u0304 (Sample Mean, mm)",
                "style": {"fontSize": "26px", "fontWeight": "600", "color": DARK},
            },
            "labels": {"style": {"fontSize": "20px", "color": "#475569"}, "format": "{value:.3f}"},
            "height": "36%",
            "top": "6%",
            "offset": 0,
            "lineWidth": 2,
            "lineColor": DARK,
            "gridLineWidth": 1,
            "gridLineColor": GRID,
            "plotLines": [
                make_plot_line(x_bar_bar, TEAL, f"CL = {x_bar_bar:.4f}"),
                make_plot_line(xbar_ucl, RED, f"UCL = {xbar_ucl:.4f}", dash="Dash"),
                make_plot_line(xbar_lcl, RED, f"LCL = {xbar_lcl:.4f}", dash="Dash", y_off=22),
                make_plot_line(xbar_uwl, AMBER, "UWL", width=2, dash="ShortDot", align="left", y_off=-6),
                make_plot_line(xbar_lwl, AMBER, "LWL", width=2, dash="ShortDot", align="left", y_off=-6),
            ],
        },
        {
            "title": {
                "text": "R (Sample Range, mm)",
                "style": {"fontSize": "26px", "fontWeight": "600", "color": DARK},
            },
            "labels": {"style": {"fontSize": "20px", "color": "#475569"}, "format": "{value:.3f}"},
            "height": "36%",
            "top": "50%",
            "offset": 0,
            "lineWidth": 2,
            "lineColor": DARK,
            "gridLineWidth": 1,
            "gridLineColor": GRID,
            "min": 0,
            "max": round(float(r_ucl * 1.15), 4),
            "plotLines": [
                make_plot_line(r_bar, TEAL, f"CL = {r_bar:.4f}"),
                make_plot_line(r_ucl, RED, f"UCL = {r_ucl:.4f}", dash="Dash"),
                make_plot_line(r_uwl, AMBER, "UWL", width=2, dash="ShortDot", align="left", y_off=-6),
            ],
        },
    ],
    "tooltip": {
        "shared": False,
        "style": {"fontSize": "20px"},
        "valueDecimals": 4,
        "valueSuffix": " mm",
        "backgroundColor": "rgba(255,255,255,0.96)",
        "borderColor": "#CBD5E1",
        "borderRadius": 8,
    },
    "plotOptions": {
        "line": {
            "lineWidth": 3,
            "marker": {"enabled": True, "radius": 7, "symbol": "circle"},
            "states": {"hover": {"lineWidthPlus": 1}},
        },
        "scatter": {
            "marker": {"radius": 13, "symbol": "diamond", "lineWidth": 3, "lineColor": "#ffffff"},
            "zIndex": 10,
        },
    },
    "series": series_dicts,
}

chart_json = json.dumps(chart_config)

# Download Highcharts JS
cdn_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
highcharts_js = None
for url in cdn_urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts JS from all CDN sources")

# Build HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:#FAFBFC;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        Highcharts.chart('container', {chart_json});
    }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot using Selenium
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

# Clean up temp file
Path(temp_path).unlink()
