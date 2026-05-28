""" anyplot.ai
facet-grid: Faceted Grid Plot
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-13
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette for soil types
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data
np.random.seed(42)

# Create faceted data: Plant growth by soil type (rows) and light condition (columns)
soil_types = ["Sandy", "Loamy", "Clay"]
light_conditions = ["Low", "Medium", "High"]
n_per_group = 25

data = []
for soil in soil_types:
    for light in light_conditions:
        # Base growth varies by light condition
        base_growth = {"Low": 8, "Medium": 15, "High": 22}[light]
        # Soil type affects growth rate
        soil_factor = {"Sandy": 0.9, "Loamy": 1.2, "Clay": 1.0}[soil]

        for _ in range(n_per_group):
            water = np.random.uniform(20, 100)
            # Growth depends on water, with more noise for wider spread
            growth = base_growth * soil_factor + water * 0.18 * soil_factor + np.random.normal(0, 3.5)
            data.append({"soil": soil, "light": light, "water": water, "growth": max(0, growth)})

# Build subplot configurations
n_rows = len(soil_types)
n_cols = len(light_conditions)

# Calculate subplot dimensions with margins
chart_width = 4800
chart_height = 2700
margin_top = 240
margin_bottom = 180
margin_left = 240
margin_right = 200
spacing = 100

plot_area_width = chart_width - margin_left - margin_right
plot_area_height = chart_height - margin_top - margin_bottom
subplot_width = (plot_area_width - spacing * (n_cols - 1)) / n_cols
subplot_height = (plot_area_height - spacing * (n_rows - 1)) / n_rows

# Build series data for each facet
series_list = []
x_axes = []
y_axes = []

for row_idx, soil in enumerate(soil_types):
    for col_idx, light in enumerate(light_conditions):
        # Filter data for this facet
        facet_data = [d for d in data if d["soil"] == soil and d["light"] == light]
        points = [[d["water"], d["growth"]] for d in facet_data]

        # Calculate position
        left = margin_left + col_idx * (subplot_width + spacing)
        top = margin_top + row_idx * (subplot_height + spacing)

        # Create x-axis for this subplot
        x_axis_id = f"x{row_idx * n_cols + col_idx}"
        x_axes.append(
            {
                "id": x_axis_id,
                "left": left,
                "top": top + subplot_height,
                "width": subplot_width,
                "height": 0,
                "min": 15,
                "max": 105,
                "lineWidth": 3,
                "lineColor": INK_SOFT,
                "tickWidth": 3,
                "tickLength": 12,
                "labels": {"style": {"fontSize": "22px", "color": INK_SOFT}, "y": 40},
                "title": {
                    "text": "Water (mm)" if row_idx == n_rows - 1 else None,
                    "style": {"fontSize": "26px", "color": INK},
                    "y": 70,
                },
                "gridLineWidth": 2,
                "gridLineColor": GRID,
                "offset": 0,
            }
        )

        # Create y-axis for this subplot - fix for consistent label display
        y_axis_id = f"y{row_idx * n_cols + col_idx}"
        y_axes.append(
            {
                "id": y_axis_id,
                "left": left,
                "top": top,
                "width": 0,
                "height": subplot_height,
                "min": 0,
                "max": 50,
                "lineWidth": 3,
                "lineColor": INK_SOFT,
                "tickWidth": 3,
                "tickLength": 12,
                "labels": {"style": {"fontSize": "22px", "color": INK_SOFT}, "x": -20},
                "title": {
                    "text": "Growth (cm)" if col_idx == 0 else None,
                    "style": {"fontSize": "26px", "color": INK},
                    "rotation": 270,
                    "x": -60,
                },
                "gridLineWidth": 2,
                "gridLineColor": GRID,
                "offset": 0,
            }
        )

        # Create series for this facet
        series_list.append(
            {
                "type": "scatter",
                "name": f"{soil} / {light}",
                "data": points,
                "xAxis": row_idx * n_cols + col_idx,
                "yAxis": row_idx * n_cols + col_idx,
                "marker": {
                    "radius": 12,
                    "symbol": "circle",
                    "fillColor": IMPRINT[row_idx % len(IMPRINT)],
                    "lineWidth": 2,
                    "lineColor": PAGE_BG,
                },
                "showInLegend": False,
            }
        )

# Build annotations for facet labels
annotations = []

# Column headers (light conditions)
for col_idx, light in enumerate(light_conditions):
    left = margin_left + col_idx * (subplot_width + spacing) + subplot_width / 2
    annotations.append(
        {
            "labels": [
                {
                    "point": {"x": left, "y": margin_top - 100, "xAxis": None, "yAxis": None},
                    "text": f"Light: {light}",
                    "backgroundColor": "transparent",
                    "borderWidth": 0,
                    "style": {"fontSize": "30px", "fontWeight": "bold", "color": INK},
                }
            ],
            "labelOptions": {"useHTML": True},
        }
    )

# Row labels (soil types)
for row_idx, soil in enumerate(soil_types):
    top = margin_top + row_idx * (subplot_height + spacing) + subplot_height / 2
    annotations.append(
        {
            "labels": [
                {
                    "point": {"x": chart_width - margin_right + 100, "y": top, "xAxis": None, "yAxis": None},
                    "text": f"Soil: {soil}",
                    "backgroundColor": "transparent",
                    "borderWidth": 0,
                    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
                    "rotation": 90,
                }
            ],
            "labelOptions": {"useHTML": True},
        }
    )

# Create chart using highcharts-core
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Set chart options
chart.options.chart = {
    "type": "scatter",
    "width": chart_width,
    "height": chart_height,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    "marginTop": margin_top,
    "marginBottom": margin_bottom,
    "marginLeft": margin_left,
    "marginRight": margin_right,
}

chart.options.title = {
    "text": "facet-grid · highcharts · anyplot.ai",
    "style": {"fontSize": "34px", "fontWeight": "bold", "color": INK},
    "y": 60,
}

chart.options.subtitle = {
    "text": "Plant Growth by Soil Type (rows) and Light Condition (columns)",
    "style": {"fontSize": "24px", "color": INK_SOFT},
    "y": 120,
}

chart.options.credits = {"enabled": False}
chart.options.legend = {"enabled": False}
chart.options.x_axis = x_axes
chart.options.y_axis = y_axes
chart.options.series = series_list
chart.options.annotations = annotations

chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 12, "states": {"hover": {"enabled": True}}},
        "states": {"inactive": {"opacity": 1}},
    }
}

chart.options.tooltip = {
    "headerFormat": "<b>{series.name}</b><br>",
    "pointFormat": "Water: {point.x:.1f} mm<br>Growth: {point.y:.1f} cm",
    "style": {"fontSize": "18px"},
}

# Generate JavaScript
html_str = chart.to_js_literal()

# Download Highcharts JS with fallback
highcharts_js = None
for url in ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
            break
    except Exception:
        continue

if highcharts_js is None:
    local_paths = [
        Path(__file__).resolve().parent.parent.parent.parent / "node_modules" / "highcharts" / "highcharts.js",
        Path("node_modules/highcharts/highcharts.js"),
    ]
    for p in local_paths:
        if p.exists():
            highcharts_js = p.read_text(encoding="utf-8")
            break

if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS from CDN or find local copy")

# Download annotations module with fallback
annotations_js = None
for url in [
    "https://code.highcharts.com/modules/annotations.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js",
]:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            annotations_js = response.read().decode("utf-8")
            break
    except Exception:
        continue

if annotations_js is None:
    local_paths = [
        Path(__file__).resolve().parent.parent.parent.parent
        / "node_modules"
        / "highcharts"
        / "modules"
        / "annotations.js",
        Path("node_modules/highcharts/modules/annotations.js"),
    ]
    for p in local_paths:
        if p.exists():
            annotations_js = p.read_text(encoding="utf-8")
            break

if annotations_js is None:
    raise RuntimeError("Failed to download annotations module from CDN or find local copy")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: {chart_width}px; height: {chart_height}px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML with theme-suffixed filename
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Create screenshot with Selenium
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
