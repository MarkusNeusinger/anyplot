""" pyplots.ai
violin-basic: Basic Violin Plot
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 92/100 | Updated: 2026-02-21
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.polygon import PolygonSeries
from scipy.stats import gaussian_kde
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - test scores across 4 study groups with distinct distributions
np.random.seed(42)
categories = ["Control", "Tutorial", "Self-Study", "Intensive"]
colors = ["#306998", "#E5AB00", "#9467BD", "#17BECF"]

raw_data = {
    "Control": np.random.normal(50, 12, 200),
    "Tutorial": np.concatenate([np.random.normal(40, 8, 100), np.random.normal(65, 8, 100)]),
    "Self-Study": np.random.normal(60, 10, 200),
    "Intensive": np.clip(np.random.exponential(15, 200) + 30, 0, 100),
}

# RGB values for gradient fills
colors_rgb = ["48,105,152", "229,171,0", "148,103,189", "23,190,207"]

# Overall mean for reference line
all_scores = np.concatenate(list(raw_data.values()))
overall_mean = float(np.mean(all_scores))

# Calculate KDE and statistics for each category
violin_width = 0.35
violin_data = []

for i, cat in enumerate(categories):
    data = raw_data[cat]
    y_min, y_max = data.min() - 3, data.max() + 3
    y_grid = np.linspace(y_min, y_max, 100)
    kde_func = gaussian_kde(data)
    density = kde_func(y_grid)
    density_norm = density / density.max() * violin_width

    violin_data.append(
        {
            "category": cat,
            "index": i,
            "y_grid": y_grid,
            "density": density_norm,
            "q1": float(np.percentile(data, 25)),
            "median": float(np.percentile(data, 50)),
            "q3": float(np.percentile(data, 75)),
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "n": len(data),
            "color": colors[i],
            "rgb": colors_rgb[i],
        }
    )

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "plotBorderWidth": 0,
    "marginBottom": 180,
    "marginLeft": 240,
    "marginRight": 80,
    "marginTop": 200,
    "animation": {"duration": 1000},
}

chart.options.title = {
    "text": "violin-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold", "color": "#333333"},
}

chart.options.subtitle = {
    "text": "Distribution of scores across 200 students per group",
    "style": {"fontSize": "44px", "fontWeight": "normal", "color": "#777777"},
}

chart.options.x_axis = {
    "title": {"text": "Study Group", "style": {"fontSize": "52px", "color": "#555555"}},
    "labels": {"style": {"fontSize": "44px", "color": "#555555"}},
    "min": -0.5,
    "max": 3.5,
    "tickPositions": [0, 1, 2, 3],
    "categories": categories,
    "lineWidth": 0,
    "tickLength": 0,
    "crosshair": {"width": 2, "color": "rgba(0, 0, 0, 0.15)", "dashStyle": "Dash"},
}

chart.options.y_axis = {
    "title": {"text": "Test Score (points)", "style": {"fontSize": "52px", "color": "#555555"}},
    "labels": {"style": {"fontSize": "44px", "color": "#555555"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.08)",
    "lineWidth": 0,
    "min": 0,
    "max": 105,
    "tickInterval": 10,
    "crosshair": {"width": 1, "color": "rgba(0, 0, 0, 0.12)", "dashStyle": "Dot"},
    "plotLines": [
        {
            "value": overall_mean,
            "color": "rgba(0, 0, 0, 0.22)",
            "dashStyle": "LongDash",
            "width": 3,
            "zIndex": 3,
            "label": {
                "text": f"Overall Mean ({overall_mean:.0f})",
                "style": {"fontSize": "32px", "color": "rgba(0, 0, 0, 0.40)", "fontStyle": "italic"},
                "align": "right",
                "x": -15,
                "y": -10,
            },
        }
    ],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "40px", "color": "#555555"},
    "verticalAlign": "top",
    "align": "right",
    "layout": "vertical",
    "x": -20,
    "y": 80,
    "floating": True,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "enabled": True,
    "shared": False,
    "useHTML": True,
    "style": {"fontSize": "28px"},
    "headerFormat": "",
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#cccccc",
    "borderRadius": 8,
    "shadow": {"color": "rgba(0,0,0,0.15)", "offsetX": 2, "offsetY": 2, "width": 4},
}

chart.options.plot_options = {
    "polygon": {
        "lineWidth": 2,
        "fillOpacity": 1.0,
        "enableMouseTracking": True,
        "animation": True,
        "states": {"hover": {"lineWidth": 3, "brightness": 0.1}, "inactive": {"opacity": 0.4}},
    },
    "scatter": {"marker": {"radius": 18, "symbol": "circle"}, "zIndex": 10, "enableMouseTracking": True},
    "series": {"animation": {"duration": 1200, "easing": "easeOutBounce"}},
}

# Violin shapes as polygon series with tooltip showing statistics
for v in violin_data:
    polygon_points = []
    for y_val, dens in zip(v["y_grid"], v["density"], strict=True):
        polygon_points.append([float(v["index"] + dens), float(y_val)])
    for j in range(len(v["y_grid"]) - 1, -1, -1):
        polygon_points.append([float(v["index"] - v["density"][j]), float(v["y_grid"][j])])

    is_featured = v["category"] == "Tutorial"
    center_alpha = "0.70" if is_featured else "0.55"
    edge_alpha = "0.20" if is_featured else "0.12"

    series = PolygonSeries()
    series.data = polygon_points
    series.name = v["category"]
    series.color = v["color"]
    series.fill_color = {
        "linearGradient": {"x1": 0, "y1": 0, "x2": 1, "y2": 0},
        "stops": [
            [0, f"rgba({v['rgb']},{edge_alpha})"],
            [0.5, f"rgba({v['rgb']},{center_alpha})"],
            [1, f"rgba({v['rgb']},{edge_alpha})"],
        ],
    }
    series.fill_opacity = 1.0
    series.line_width = 3 if is_featured else 2
    series.tooltip = {
        "pointFormat": (
            f'<span style="font-size:32px;font-weight:bold;color:{v["color"]}">'
            f"{v['category']}</span><br/>"
            f"<b>n</b> = {v['n']}<br/>"
            f"<b>Mean</b>: {v['mean']:.1f}<br/>"
            f"<b>Median</b>: {v['median']:.1f}<br/>"
            f"<b>Q1</b>: {v['q1']:.1f} | <b>Q3</b>: {v['q3']:.1f}<br/>"
            f"<b>Std Dev</b>: {v['std']:.1f}"
        )
    }
    chart.add_series(series)

# Median lines (horizontal lines across each violin at the median position)
for v in violin_data:
    # Find density at median to determine line width
    kde_func = gaussian_kde(raw_data[v["category"]])
    med_density = kde_func(v["median"])[0]
    max_density = max(kde_func(v["y_grid"]))
    line_half_width = (med_density / max_density) * violin_width * 0.85

    med_line = PolygonSeries()
    med_line.data = [
        [float(v["index"] - line_half_width), float(v["median"])],
        [float(v["index"] + line_half_width), float(v["median"])],
    ]
    med_line.name = "Median" if v["index"] == 0 else f"Median {v['category']}"
    med_line.show_in_legend = v["index"] == 0
    med_line.color = "#ffffff"
    med_line.line_width = 8
    med_line.fill_opacity = 0
    med_line.z_index = 15
    med_line.enable_mouse_tracking = False
    med_line.marker = {"enabled": False}
    chart.add_series(med_line)

# IQR boxes (thin rectangles for interquartile range)
for v in violin_data:
    box_width = 0.10
    box_points = [
        [float(v["index"] - box_width), float(v["q1"])],
        [float(v["index"] + box_width), float(v["q1"])],
        [float(v["index"] + box_width), float(v["q3"])],
        [float(v["index"] - box_width), float(v["q3"])],
    ]

    box_series = PolygonSeries()
    box_series.data = box_points
    box_series.name = f"{v['category']} IQR"
    box_series.show_in_legend = False
    box_series.color = "#333333"
    box_series.fill_color = "#333333"
    box_series.fill_opacity = 0.85
    box_series.enable_mouse_tracking = False
    chart.add_series(box_series)

# Export
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()

# plot.html for interactive viewing (CDN links for browser)
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(standalone_html)

# Temp HTML for screenshot (inline JS for headless Chrome)
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
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
