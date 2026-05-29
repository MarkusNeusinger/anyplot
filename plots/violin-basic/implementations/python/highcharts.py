""" anyplot.ai
violin-basic: Basic Violin Plot
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-29
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.polygon import PolygonSeries
from PIL import Image
from scipy.stats import gaussian_kde
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette + adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette positions 1–4 for the four categories
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]
IMPRINT_RGB = ["0,158,115", "196,117,253", "68,103,163", "189,130,51"]

# Data — test scores across 4 study groups with distinct distribution shapes
np.random.seed(42)
categories = ["Control", "Tutorial", "Self-Study", "Intensive"]

raw_data = {
    "Control": np.random.normal(50, 12, 200),
    "Tutorial": np.concatenate([np.random.normal(40, 8, 100), np.random.normal(65, 8, 100)]),
    "Self-Study": np.random.normal(60, 10, 200),
    "Intensive": np.clip(np.random.exponential(15, 200) + 30, 0, 100),
}

all_scores = np.concatenate(list(raw_data.values()))
overall_mean = float(np.mean(all_scores))

# KDE + statistics per category
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
            "color": IMPRINT_PALETTE[i],
            "rgb": IMPRINT_RGB[i],
        }
    )

# Chart — 3200×1800 landscape canvas
title = "violin-basic · python · highcharts · anyplot.ai"

chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "plotBorderWidth": 0,
    "marginBottom": 180,
    "marginLeft": 240,
    "marginRight": 80,
    "marginTop": 200,
}

chart.options.title = {"text": title, "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK}}

chart.options.subtitle = {
    "text": "Distribution of scores across 200 students per study group",
    "style": {"fontSize": "44px", "fontWeight": "normal", "color": INK_SOFT},
}

chart.options.x_axis = {
    "title": {"text": "Study Group", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": -0.5,
    "max": 3.5,
    "tickPositions": [0, 1, 2, 3],
    "categories": categories,
    "lineWidth": 0,
    "tickLength": 0,
}

chart.options.y_axis = {
    "title": {"text": "Test Score (points)", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineWidth": 0,
    "min": 0,
    "max": 105,
    "tickInterval": 10,
    "plotLines": [
        {
            "value": overall_mean,
            "color": INK_SOFT,
            "dashStyle": "LongDash",
            "width": 3,
            "zIndex": 3,
            "label": {
                "text": f"Overall Mean ({overall_mean:.0f})",
                "style": {"fontSize": "36px", "color": INK_SOFT, "fontStyle": "italic"},
                "align": "right",
                "x": -15,
                "y": -10,
            },
        }
    ],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "44px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
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
    "style": {"fontSize": "32px"},
    "headerFormat": "",
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
}

chart.options.plot_options = {
    "polygon": {"lineWidth": 2, "fillOpacity": 1.0, "enableMouseTracking": True},
    "scatter": {"marker": {"radius": 18, "symbol": "circle"}, "zIndex": 10, "enableMouseTracking": True},
}

# Violin shapes as PolygonSeries with gradient fills
for v in violin_data:
    polygon_points = []
    for y_val, dens in zip(v["y_grid"], v["density"], strict=True):
        polygon_points.append([float(v["index"] + dens), float(y_val)])
    for j in range(len(v["y_grid"]) - 1, -1, -1):
        polygon_points.append([float(v["index"] - v["density"][j]), float(v["y_grid"][j])])

    series = PolygonSeries()
    series.data = polygon_points
    series.name = v["category"]
    series.color = v["color"]
    series.fill_color = {
        "linearGradient": {"x1": 0, "y1": 0, "x2": 1, "y2": 0},
        "stops": [[0, f"rgba({v['rgb']},0.12)"], [0.5, f"rgba({v['rgb']},0.65)"], [1, f"rgba({v['rgb']},0.12)"]],
    }
    series.fill_opacity = 1.0
    series.line_width = 2
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

# Median lines — PAGE_BG color so they contrast against the filled violin body
for v in violin_data:
    kde_func = gaussian_kde(raw_data[v["category"]])
    med_density = kde_func(v["median"])[0]
    max_density = float(max(kde_func(v["y_grid"])))
    line_half_width = (med_density / max_density) * violin_width * 0.85

    med_line = PolygonSeries()
    med_line.data = [
        [float(v["index"] - line_half_width), float(v["median"])],
        [float(v["index"] + line_half_width), float(v["median"])],
    ]
    med_line.name = "Median" if v["index"] == 0 else f"Median {v['category']}"
    med_line.show_in_legend = v["index"] == 0
    med_line.color = PAGE_BG
    med_line.line_width = 8
    med_line.fill_opacity = 0
    med_line.z_index = 15
    med_line.enable_mouse_tracking = False
    med_line.marker = {"enabled": False}
    chart.add_series(med_line)

# IQR boxes — category-coloured border over semi-transparent category fill
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
    box_series.color = v["color"]
    box_series.fill_color = f"rgba({v['rgb']},0.85)"
    box_series.fill_opacity = 1.0
    box_series.line_width = 3
    box_series.z_index = 12
    box_series.enable_mouse_tracking = False
    chart.add_series(box_series)

# Export — download Highcharts JS for inline embedding (headless Chrome blocks CDN)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
# CDP override makes the viewport authoritative (--window-size alone is eaten by Chrome chrome)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dims — safety net for ±1–2 px Chrome rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
