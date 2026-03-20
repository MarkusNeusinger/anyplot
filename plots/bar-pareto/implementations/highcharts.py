""" pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: highcharts unknown | Python 3.14.3
Quality: 90/100 | Created: 2026-03-20
"""

import re
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.annotations import Annotation
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Manufacturing defect types sorted descending by frequency
categories = [
    "Scratches",
    "Dents",
    "Misalignment",
    "Cracks",
    "Discoloration",
    "Burrs",
    "Warping",
    "Contamination",
    "Missing Parts",
    "Oversize",
]
counts = np.array([187, 128, 93, 71, 54, 38, 27, 19, 12, 6])

# Cumulative percentage
cumulative = np.cumsum(counts) / counts.sum() * 100
cumulative_data = [round(float(v), 1) for v in cumulative]

# Find index where cumulative crosses 80%
threshold_idx = int(np.searchsorted(cumulative, 80))

# Build chart using highcharts-core Python API
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 300,
    "marginTop": 160,
    "marginLeft": 260,
    "marginRight": 420,
    "alignTicks": False,
    "style": {"fontFamily": "Arial, Helvetica, sans-serif"},
}

# Title
chart.options.title = {
    "text": "Manufacturing Defect Analysis \u00b7 bar-pareto \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": "#2c3e50"},
    "margin": 50,
}

# Subtitle for storytelling
chart.options.subtitle = {
    "text": "Top 4 defect types account for 75% of all quality issues \u2014 focus here first",
    "style": {"fontSize": "30px", "color": "#7f8c8d", "fontWeight": "normal"},
}

# X-axis
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Defect Type", "style": {"fontSize": "34px", "color": "#555555"}, "margin": 20},
    "labels": {"style": {"fontSize": "28px", "color": "#555555"}},
    "lineColor": "#cccccc",
    "crosshair": {"width": 2, "color": "rgba(48, 105, 152, 0.15)", "dashStyle": "Solid"},
}

# Dual Y-axes
chart.options.y_axis = [
    {
        "title": {"text": "Defect Count", "style": {"fontSize": "34px", "color": "#306998"}, "margin": 20},
        "labels": {"style": {"fontSize": "26px", "color": "#555555"}, "format": "{value}"},
        "gridLineColor": "#e8e8e8",
        "gridLineWidth": 1,
        "gridLineDashStyle": "Dot",
        "min": 0,
    },
    {
        "title": {"text": "Cumulative %", "style": {"fontSize": "30px", "color": "#e67e22"}, "margin": 20},
        "labels": {"style": {"fontSize": "26px", "color": "#555555"}, "format": "{value}%"},
        "min": 0,
        "max": 100,
        "tickInterval": 20,
        "opposite": True,
        "gridLineWidth": 0,
        "plotLines": [
            {
                "value": 80,
                "color": "#c0392b",
                "width": 3,
                "dashStyle": "LongDash",
                "zIndex": 5,
                "label": {
                    "text": "80% threshold",
                    "align": "right",
                    "x": -20,
                    "y": -14,
                    "style": {"fontSize": "26px", "color": "#c0392b", "fontWeight": "bold", "fontStyle": "italic"},
                },
            }
        ],
    },
]

# Tooltip
chart.options.tooltip = {
    "shared": True,
    "backgroundColor": "rgba(255, 255, 255, 0.96)",
    "borderColor": "#306998",
    "borderRadius": 8,
    "borderWidth": 2,
    "shadow": {"color": "rgba(0,0,0,0.1)", "offsetX": 1, "offsetY": 2, "width": 3},
    "style": {"fontSize": "22px"},
}

# Plot options with shadows and rounded corners
chart.options.plot_options = {
    "column": {
        "pointPadding": 0.08,
        "borderWidth": 0,
        "groupPadding": 0.05,
        "borderRadius": 6,
        "shadow": {"color": "rgba(0,0,0,0.08)", "offsetX": 2, "offsetY": 3, "width": 5},
    }
}

# Bar data: highlight "vital few" (above 80% threshold) with darker shade
bar_data = []
for i, c in enumerate(counts):
    if i <= threshold_idx:
        bar_data.append({"y": int(c), "color": "#1a4971"})
    else:
        bar_data.append({"y": int(c), "color": "#306998"})

# Create bar series using ColumnSeries
bar_series = ColumnSeries.from_dict(
    {
        "data": bar_data,
        "name": "Defect Count",
        "type": "column",
        "yAxis": 0,
        "dataLabels": {
            "enabled": True,
            "format": "{y}",
            "style": {"fontSize": "24px", "fontWeight": "bold", "color": "#2c3e50", "textOutline": "2px white"},
            "y": -8,
        },
    }
)
chart.add_series(bar_series)

# Cumulative line series using LineSeries (spline type)
line_series = LineSeries.from_dict(
    {
        "data": cumulative_data,
        "name": "Cumulative %",
        "type": "spline",
        "yAxis": 1,
        "color": "#e67e22",
        "lineWidth": 4,
        "marker": {
            "enabled": True,
            "radius": 8,
            "fillColor": "#e67e22",
            "lineWidth": 3,
            "lineColor": "#ffffff",
            "symbol": "circle",
        },
        "dataLabels": {
            "enabled": True,
            "format": "{y:.1f}%",
            "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#e67e22", "textOutline": "3px white"},
            "y": -28,
            "x": 10,
        },
        "shadow": {"color": "rgba(230, 126, 34, 0.2)", "offsetX": 0, "offsetY": 3, "width": 6},
    }
)
chart.add_series(line_series)

# Annotation callout on the "vital few" boundary
chart.options.annotations = [
    Annotation.from_dict(
        {
            "labels": [
                {
                    "point": {"x": threshold_idx, "y": cumulative_data[threshold_idx], "xAxis": 0, "yAxis": 1},
                    "text": f"Vital Few \u2190 {threshold_idx + 1} types = {cumulative_data[threshold_idx]}%",
                    "y": -55,
                    "x": 30,
                    "style": {"fontSize": "24px", "fontWeight": "bold", "color": "#c0392b"},
                }
            ],
            "labelOptions": {
                "backgroundColor": "rgba(255, 255, 255, 0.92)",
                "borderColor": "#c0392b",
                "borderWidth": 2,
                "borderRadius": 8,
                "padding": 12,
                "shape": "callout",
            },
            "draggable": "",
        }
    )
]

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px", "fontWeight": "normal", "color": "#555555"},
    "symbolRadius": 4,
    "symbolHeight": 18,
    "symbolWidth": 18,
    "itemDistance": 40,
}

chart.options.credits = {"enabled": False}

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
annotations_url = "https://code.highcharts.com/modules/annotations.js"
cdn_fallback = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
annotations_fallback = "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js"

highcharts_js = None
for url in [highcharts_url, cdn_fallback]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts JS")

annotations_js = None
for url in [annotations_url, annotations_fallback]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            annotations_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if not annotations_js:
    raise RuntimeError("Failed to download Highcharts annotations module")

# Generate HTML using Chart.to_js_literal()
chart_js = chart.to_js_literal()
# Fix format strings: highcharts-core omits quotes around Highcharts format templates
chart_js = re.sub(r"format: (\{[^}]+\})", r"format: '\1'", chart_js)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
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
