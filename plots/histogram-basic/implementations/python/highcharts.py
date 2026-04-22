""" pyplots.ai
histogram-basic: Basic Histogram
Library: highcharts 1.10.3 | Python 3.14.0
Quality: 94/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.annotations import Annotation
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.options.series.histogram import HistogramSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data — university exam scores with bimodal distribution
np.random.seed(42)
main_group = np.random.normal(loc=72, scale=12, size=400)
high_achievers = np.random.normal(loc=88, scale=5, size=100)
exam_scores = np.clip(np.concatenate([main_group, high_achievers]), 0, 100)

mean_score = float(np.mean(exam_scores))
median_score = float(np.median(exam_scores))

# Compute actual bin peak heights for accurate annotation positioning
counts, bin_edges = np.histogram(exam_scores, bins=20)
primary_peak_y = int(max(counts[i] for i in range(len(counts)) if (bin_edges[i] + bin_edges[i + 1]) / 2 < 82))
secondary_peak_y = int(max(counts[i] for i in range(len(counts)) if (bin_edges[i] + bin_edges[i + 1]) / 2 >= 82))

# Create chart using native Highcharts histogram series
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings — increased marginBottom to ensure x-axis title is visible
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "marginBottom": 320,
    "marginLeft": 220,
    "marginRight": 200,
    "marginTop": 220,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

# Title
chart.options.title = {
    "text": "Exam Score Distribution \u00b7 histogram-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "60px", "fontWeight": "700", "color": "#1a1a2e"},
    "margin": 30,
}

# Subtitle with narrative context
chart.options.subtitle = {
    "text": (
        "500 students \u2014 Introduction to Statistics, Fall 2024"
        " \u00a0|\u00a0 Bimodal pattern: main cluster near 72, high-achiever peak near 88"
    ),
    "style": {"fontSize": "36px", "color": "#555555", "fontWeight": "400"},
}

# X-axis with grade range plotBands and mean/median plotLines
# Offset mean and median labels vertically to avoid crowding (they are only ~0.5 apart)
chart.options.x_axis = [
    {
        "title": {
            "text": "Exam Score (points)",
            "style": {"fontSize": "44px", "color": "#333333", "fontWeight": "600"},
            "margin": 30,
        },
        "labels": {"style": {"fontSize": "36px", "color": "#444444"}},
        "tickInterval": 5,
        "alignTicks": False,
        "plotBands": [
            {
                "from": 0,
                "to": 60,
                "color": "rgba(231, 76, 60, 0.06)",
                "label": {
                    "text": "D/F",
                    "style": {"fontSize": "30px", "color": "#c0392b", "fontWeight": "600"},
                    "align": "center",
                    "y": -10,
                },
            },
            {
                "from": 60,
                "to": 70,
                "color": "rgba(243, 156, 18, 0.06)",
                "label": {
                    "text": "C",
                    "style": {"fontSize": "30px", "color": "#d68910", "fontWeight": "600"},
                    "align": "center",
                    "y": -10,
                },
            },
            {
                "from": 70,
                "to": 80,
                "color": "rgba(46, 204, 113, 0.06)",
                "label": {
                    "text": "B",
                    "style": {"fontSize": "30px", "color": "#1e8449", "fontWeight": "600"},
                    "align": "center",
                    "y": -10,
                },
            },
            {
                "from": 80,
                "to": 90,
                "color": "rgba(41, 128, 185, 0.06)",
                "label": {
                    "text": "A",
                    "style": {"fontSize": "30px", "color": "#2471a3", "fontWeight": "600"},
                    "align": "center",
                    "y": -10,
                },
            },
            {
                "from": 90,
                "to": 100,
                "color": "rgba(142, 68, 173, 0.06)",
                "label": {
                    "text": "A+",
                    "style": {"fontSize": "30px", "color": "#7d3c98", "fontWeight": "600"},
                    "align": "center",
                    "y": -10,
                },
            },
        ],
        "plotLines": [
            {
                "value": round(mean_score, 1),
                "color": "#c0392b",
                "width": 4,
                "dashStyle": "Dash",
                "zIndex": 5,
                "label": {
                    "text": f"\u25c6 Mean: {mean_score:.1f}",
                    "style": {"fontSize": "30px", "color": "#c0392b", "fontWeight": "700"},
                    "align": "right",
                    "rotation": 0,
                    "x": -12,
                    "y": 40,
                },
            },
            {
                "value": round(median_score, 1),
                "color": "#2980b9",
                "width": 4,
                "dashStyle": "ShortDot",
                "zIndex": 5,
                "label": {
                    "text": f"\u25cf Median: {median_score:.1f}",
                    "style": {"fontSize": "30px", "color": "#2980b9", "fontWeight": "700"},
                    "align": "left",
                    "rotation": 0,
                    "x": 12,
                    "y": 40,
                },
            },
        ],
    },
    {"title": {"text": ""}, "opposite": True, "visible": False},
]

# Y-axis — subtle dashed gridlines
chart.options.y_axis = [
    {
        "title": {
            "text": "Number of Students",
            "style": {"fontSize": "44px", "color": "#333333", "fontWeight": "600"},
            "margin": 20,
        },
        "labels": {"style": {"fontSize": "36px", "color": "#444444"}},
        "min": 0,
        "tickInterval": 10,
        "gridLineColor": "#dcdcdc",
        "gridLineWidth": 1,
        "gridLineDashStyle": "Dot",
    },
    {"title": {"text": ""}, "opposite": True, "visible": False},
]

# Histogram appearance — refined borders and no gaps
chart.options.plot_options = {
    "histogram": {
        "pointPadding": 0,
        "groupPadding": 0,
        "borderWidth": 1.5,
        "borderColor": "#1a4a6e",
        "binsNumber": 20,
        "shadow": {"color": "rgba(0,0,0,0.08)", "offsetX": 2, "offsetY": 2, "width": 4},
        "tooltip": {
            "headerFormat": "",
            "pointFormat": "<b>{point.x:.0f} \u2013 {point.x2:.0f}</b><br/>Students: {point.y}",
        },
    }
}

# Peak annotations via Highcharts Annotations API (declarative, through chart options)
chart.options.annotations = [
    Annotation(
        crop=False,
        label_options={
            "shape": "connector",
            "backgroundColor": "rgba(255,255,255,0.94)",
            "borderColor": "#306998",
            "borderWidth": 2,
            "borderRadius": 8,
            "padding": 12,
            "allowOverlap": True,
            "style": {"fontSize": "28px", "fontWeight": "700", "color": "#1a4a6e"},
        },
        labels=[
            {
                "point": {"x": 66, "y": primary_peak_y, "xAxis": 0, "yAxis": 0},
                "text": (
                    "Primary peak \u25b2<br/>"
                    '<span style="font-size:24px;color:#555">~72 pts \u2014 main group (80%)</span>'
                ),
                "y": -80,
                "x": -100,
                "overflow": "none",
                "crop": False,
                "allowOverlap": True,
            },
            {
                "point": {"x": 88, "y": secondary_peak_y, "xAxis": 0, "yAxis": 0},
                "text": (
                    "Secondary peak \u25b2<br/>"
                    '<span style="font-size:24px;color:#555">~88 pts \u2014 high achievers (20%)</span>'
                ),
                "y": -80,
                "x": 40,
                "overflow": "none",
                "crop": False,
                "allowOverlap": True,
            },
        ],
    )
]

# Legend (hide for single series)
chart.options.legend = {"enabled": False}

# Credits
chart.options.credits = {"enabled": False}

# Base data series (hidden — provides data for histogram)
base_series = ColumnSeries()
base_series.name = "Raw Scores"
base_series.data = [round(float(v), 1) for v in exam_scores]
base_series.id = "exam-data"
base_series.visible = False
base_series.show_in_legend = False

# Histogram series derived from base data
hist_series = HistogramSeries()
hist_series.name = "Frequency"
hist_series.base_series = "exam-data"
hist_series.color = "#306998"
hist_series.x_axis = 0
hist_series.y_axis = 0
hist_series.bins_number = 20

chart.add_series(base_series)
chart.add_series(hist_series)

# Download Highcharts JS and histogram module
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

histogram_module_url = "https://code.highcharts.com/modules/histogram-bellcurve.js"
with urllib.request.urlopen(histogram_module_url, timeout=30) as response:
    histogram_module_js = response.read().decode("utf-8")

annotations_url = "https://code.highcharts.com/modules/annotations.js"
with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

# Generate HTML with inline scripts — annotations are part of chart options
html_str = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{histogram_module_js}</script>
    <script>{annotations_js}</script>
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
