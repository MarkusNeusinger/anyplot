""" pyplots.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: highcharts unknown | Python 3.14.3
Quality: 90/100 | Created: 2026-02-17
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries
from highcharts_core.options.series.spline import SplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data
p = np.linspace(0, 1, 200)

# Gini impurity: 2 * p * (1 - p)
gini = 2 * p * (1 - p)

# Entropy: -p * log2(p) - (1-p) * log2(1-p), normalized to [0, 1]
# Handle edge cases at p=0 and p=1
with np.errstate(divide="ignore", invalid="ignore"):
    entropy_raw = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
entropy_raw = np.nan_to_num(entropy_raw, nan=0.0)
entropy = entropy_raw  # max of entropy is 1.0 at p=0.5, already in [0, 1]

# Prepare data for Highcharts (list of [x, y] pairs)
gini_data = [[round(float(p[i]), 4), round(float(gini[i]), 6)] for i in range(len(p))]
entropy_data = [[round(float(p[i]), 4), round(float(entropy[i]), 6)] for i in range(len(p))]

# Area range data: [x, low (gini), high (entropy)] to fill between curves
area_range_data = [
    [round(float(p[i]), 4), round(float(gini[i]), 6), round(float(entropy[i]), 6)] for i in range(len(p))
]

# Colors
color_gini = "#306998"  # Python Blue
color_entropy = "#E8793A"  # Warm orange complement
color_fill = "rgba(232, 121, 58, 0.08)"  # Very subtle fill between curves

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "spline",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafafa",
    "marginLeft": 220,
    "marginRight": 160,
    "marginBottom": 280,
    "marginTop": 200,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "line-impurity-comparison \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold", "color": "#1a1a2e"},
}

chart.options.subtitle = {
    "text": "Gini Impurity vs Entropy as Decision Tree Splitting Criteria",
    "style": {"fontSize": "36px", "color": "#555555", "fontWeight": "300"},
}

chart.options.x_axis = {
    "title": {"text": "Probability (p)", "style": {"fontSize": "40px", "color": "#333333"}, "margin": 25},
    "labels": {"style": {"fontSize": "32px", "color": "#444444"}, "y": 40},
    "min": 0,
    "max": 1,
    "tickInterval": 0.1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "gridLineDashStyle": "Dot",
    "lineWidth": 0,
    "tickWidth": 0,
    "crosshair": {"width": 2, "color": "rgba(0, 0, 0, 0.15)", "dashStyle": "Dash"},
}

chart.options.y_axis = {
    "title": {"text": "Impurity Measure", "style": {"fontSize": "40px", "color": "#333333"}},
    "labels": {"style": {"fontSize": "32px", "color": "#444444"}},
    "min": 0,
    "max": 1.1,
    "endOnTick": False,
    "tickInterval": 0.2,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "gridLineDashStyle": "Dot",
    "lineWidth": 0,
    "plotLines": [
        {
            "value": 0.5,
            "color": "rgba(48, 105, 152, 0.25)",
            "width": 2,
            "dashStyle": "LongDash",
            "label": {
                "text": "Gini max = 0.5",
                "align": "right",
                "x": -15,
                "style": {"fontSize": "26px", "color": "#306998", "fontWeight": "bold"},
            },
            "zIndex": 3,
        },
        {
            "value": 1.0,
            "color": "rgba(232, 121, 58, 0.25)",
            "width": 2,
            "dashStyle": "LongDash",
            "label": {
                "text": "Entropy max = 1.0",
                "align": "right",
                "x": -15,
                "style": {"fontSize": "26px", "color": "#E8793A", "fontWeight": "bold"},
            },
            "zIndex": 3,
        },
    ],
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 60,
    "itemStyle": {"fontSize": "34px", "fontWeight": "normal", "color": "#333333"},
    "itemMarginBottom": 15,
    "backgroundColor": "rgba(255, 255, 255, 0.85)",
    "borderRadius": 10,
    "borderWidth": 1,
    "borderColor": "rgba(0, 0, 0, 0.08)",
    "padding": 24,
    "shadow": {"enabled": True, "color": "rgba(0, 0, 0, 0.04)", "offsetX": 2, "offsetY": 2, "width": 8},
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "shared": True,
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderRadius": 8,
    "borderWidth": 1,
    "borderColor": "#cccccc",
    "shadow": {"color": "rgba(0, 0, 0, 0.08)", "offsetX": 2, "offsetY": 2, "width": 6},
    "style": {"fontSize": "28px"},
    "headerFormat": '<span style="font-size: 28px; font-weight: bold;">p = {point.key:.2f}</span><br/>',
    "pointFormat": '<span style="color:{series.color}">\u25cf</span> {series.name}: <b>{point.y:.4f}</b><br/>',
    "valueDecimals": 4,
}

chart.options.plot_options = {
    "series": {"animation": False},
    "spline": {"lineWidth": 6, "marker": {"enabled": False}},
    "arearange": {"lineWidth": 0, "marker": {"enabled": False}, "enableMouseTracking": False},
}

# Annotation at p=0.5 highlighting both maxima
chart.options.annotations = [
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": "rgba(255, 255, 255, 0.92)",
            "borderColor": "#444444",
            "borderRadius": 8,
            "borderWidth": 2,
            "style": {"fontSize": "28px", "color": "#1a1a2e"},
            "padding": 14,
            "shadow": {"color": "rgba(0, 0, 0, 0.06)", "offsetX": 2, "offsetY": 2, "width": 6},
        },
        "labels": [
            {
                "point": {"x": 0.5, "y": 1.0, "xAxis": 0, "yAxis": 0},
                "text": "Both peak at p = 0.5<br/>Entropy = 1.0 \u2502 Gini = 0.5",
                "y": -40,
            }
        ],
    }
]

# Area range series (fill between curves) — distinctive Highcharts feature
fill_series = AreaRangeSeries()
fill_series.data = area_range_data
fill_series.name = "Difference"
fill_series.color = color_fill
fill_series.fill_opacity = 0.08
fill_series.show_in_legend = False
chart.add_series(fill_series)

# Gini series (SplineSeries for smooth interpolation — distinctive Highcharts feature)
gini_series = SplineSeries()
gini_series.data = gini_data
gini_series.name = "Gini Impurity: 2p(1\u2212p)"
gini_series.color = color_gini
chart.add_series(gini_series)

# Entropy series
entropy_series = SplineSeries()
entropy_series.data = entropy_data
entropy_series.name = "Entropy: \u2212p log\u2082p \u2212 (1\u2212p) log\u2082(1\u2212p)"
entropy_series.color = color_entropy
chart.add_series(entropy_series)

# Download Highcharts JS and annotations module
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

annotations_url = "https://code.highcharts.com/modules/annotations.js"
with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    portable_html = (
        """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>"""
        + html_str
        + """</script>
</body>
</html>"""
    )
    f.write(portable_html)

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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
