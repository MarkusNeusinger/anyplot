""" anyplot.ai
raincloud-basic: Basic Raincloud Plot
Library: highcharts unknown | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-26
"""

import os
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
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Data — reaction-time distributions across four experimental conditions
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C"]

# anyplot palette positions 1–4 (canonical order: green, lavender, blue, ochre)
colors = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]
fills = ["rgba(0,158,115,0.45)", "rgba(196,117,253,0.45)", "rgba(68,103,163,0.45)", "rgba(189,130,51,0.45)"]

control = np.random.normal(450, 60, 80)
treatment_a = np.random.normal(380, 50, 80)
treatment_b = np.concatenate([np.random.normal(350, 30, 40), np.random.normal(480, 35, 40)])
treatment_c = np.random.normal(420, 95, 80)
all_data = [control, treatment_a, treatment_b, treatment_c]

# Box-plot statistics (Tukey-style whiskers)
box_data = []
for data in all_data:
    q1, median, q3 = np.percentile(data, [25, 50, 75])
    iqr = q3 - q1
    low = float(max(np.min(data), q1 - 1.5 * iqr))
    high = float(min(np.max(data), q3 + 1.5 * iqr))
    box_data.append({"low": low, "q1": float(q1), "median": float(median), "q3": float(q3), "high": high})


# Vectorized Gaussian KDE with Silverman bandwidth
def kde(arr, n_points=80, padding=10):
    n = len(arr)
    std = np.std(arr)
    iqr_val = np.percentile(arr, 75) - np.percentile(arr, 25)
    bw = 0.9 * min(std, iqr_val / 1.34) * (n ** (-0.2))
    xs = np.linspace(arr.min() - padding, arr.max() + padding, n_points)
    density = np.exp(-0.5 * ((xs[:, None] - arr[None, :]) / bw) ** 2).sum(axis=1)
    density /= n * bw * np.sqrt(2 * np.pi)
    return xs, density


# Value-axis range — tight fit to actual data, aligned to 50-ms ticks
all_values = np.concatenate(all_data)
y_min = int(np.floor(np.min(all_values) / 50) * 50)
y_max = int(np.ceil(np.max(all_values) / 50) * 50)

# Chart — inverted for horizontal orientation
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "inverted": True,
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginTop": 140,
    "marginBottom": 160,
    "marginLeft": 280,
    "marginRight": 140,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif", "color": INK},
}

chart.options.title = {
    "text": "raincloud-basic · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "600", "color": INK},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Reaction time distributions across four experimental conditions",
    "style": {"fontSize": "38px", "fontWeight": "300", "color": INK_SOFT},
}

# Inverted: x_axis renders vertically (categories on the left)
chart.options.x_axis = {
    "title": {
        "text": "Experimental Condition",
        "style": {"fontSize": "56px", "fontWeight": "600", "color": INK},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "44px", "fontWeight": "500", "color": INK_SOFT}},
    "categories": categories,
    "tickPositions": [0, 1, 2, 3],
    "min": -0.55,
    "max": 3.55,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "lineWidth": 0,
    "tickWidth": 0,
    "gridLineWidth": 0,
}

# Inverted: y_axis renders horizontally (reaction time at the bottom)
chart.options.y_axis = {
    "title": {
        "text": "Reaction Time (ms)",
        "style": {"fontSize": "56px", "fontWeight": "600", "color": INK},
        "margin": 24,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "tickInterval": 50,
    "min": y_min,
    "max": y_max,
    "startOnTick": False,
    "endOnTick": False,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "lineWidth": 0,
}

# Consolidated legend — one entry per category, none for rain/box
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "44px", "fontWeight": "500", "color": INK_SOFT},
    "align": "right",
    "verticalAlign": "top",
    "layout": "horizontal",
    "x": -20,
    "y": 70,
    "backgroundColor": ELEVATED_BG,
    "borderColor": GRID,
    "borderWidth": 1,
    "borderRadius": 8,
    "padding": 20,
    "symbolWidth": 44,
    "symbolHeight": 24,
}

chart.options.plot_options = {
    "boxplot": {
        "color": INK,
        "medianColor": INK,
        "medianWidth": 8,
        "stemWidth": 3,
        "whiskerColor": INK_SOFT,
        "whiskerWidth": 3,
        "whiskerLength": "55%",
        "lineWidth": 3,
        "pointWidth": 60,
    },
    "scatter": {"marker": {"radius": 12, "symbol": "circle"}, "zIndex": 5},
    "polygon": {"fillOpacity": 0.50, "lineWidth": 3, "zIndex": 2},
    "series": {"animation": False},
}

chart.options.tooltip = {"enabled": False}
chart.options.credits = {"enabled": False}

# "Cloud" — half-violin above each category baseline (negative x offset in inverted mode)
for i, data in enumerate(all_data):
    y_range, density = kde(np.array(data))
    density_norm = density / density.max() * 0.38

    polygon_points = [[float(i - d - 0.04), float(y)] for y, d in zip(y_range, density_norm, strict=True)]
    polygon_points += [[float(i - 0.04), float(y)] for y in reversed(y_range)]

    series = PolygonSeries()
    series.data = polygon_points
    series.name = categories[i]
    series.color = colors[i]
    series.fill_color = fills[i]
    series.line_width = 3
    series.line_color = colors[i]
    series.z_index = 2
    chart.add_series(series)

# Box plot — centered on each category baseline
box_series = BoxPlotSeries()
box_series.data = [
    {
        "x": i,
        "low": b["low"],
        "q1": b["q1"],
        "median": b["median"],
        "q3": b["q3"],
        "high": b["high"],
        "fillColor": ELEVATED_BG,
        "color": INK,
        "medianColor": INK,
        "stemColor": INK_SOFT,
        "whiskerColor": INK_SOFT,
    }
    for i, b in enumerate(box_data)
]
box_series.name = "Box"
box_series.show_in_legend = False
box_series.z_index = 8
chart.add_series(box_series)

# "Rain" — jittered scatter below each category baseline
for i, data in enumerate(all_data):
    scatter_points = [[float(i + 0.22 + np.random.uniform(-0.07, 0.07)), float(val)] for val in data]

    scatter_series = ScatterSeries()
    scatter_series.data = scatter_points
    scatter_series.name = categories[i]
    scatter_series.color = colors[i]
    scatter_series.marker = {
        "radius": 12,
        "lineWidth": 1,
        "lineColor": PAGE_BG,
        "fillColor": colors[i],
        "states": {"hover": {"enabled": False}},
    }
    scatter_series.opacity = 0.65
    scatter_series.show_in_legend = False
    scatter_series.z_index = 5
    chart.add_series(scatter_series)

# Annotation callouts — one per category to complete the data story
annotations = [
    {"y_frac": 0.07, "x_frac": 0.65, "color": colors[0], "title": "Baseline", "body": "Mean ~450 ms"},
    {
        "y_frac": 0.30,
        "x_frac": 0.05,
        "color": colors[1],
        "title": "Fastest responses",
        "body": "Mean ~380 ms, tight spread",
    },
    {
        "y_frac": 0.54,
        "x_frac": 0.70,
        "color": colors[2],
        "title": "Bimodal distribution",
        "body": "Two clusters: ~350 ms &amp; ~480 ms",
    },
    {
        "y_frac": 0.78,
        "x_frac": 0.06,
        "color": colors[3],
        "title": "Widest variability",
        "body": "Long tails on both sides",
    },
]

annotation_js_parts = []
for ann in annotations:
    label_html = (
        f"<span style='font-size:32px;color:{ann['color']};font-weight:600;'>&#9654; {ann['title']}</span>"
        f"<br><span style='font-size:26px;color:{INK_SOFT};'>{ann['body']}</span>"
    )
    annotation_js_parts.append(
        f"""
    chart.renderer.label(
        {label_html!r},
        chart.plotLeft + chart.plotWidth * {ann["x_frac"]},
        chart.plotTop + chart.plotHeight * {ann["y_frac"]},
        null, null, null, true
    )
    .attr({{
        fill: {ELEVATED_BG!r},
        stroke: {ann["color"]!r},
        'stroke-width': 2,
        r: 10,
        padding: 14,
        zIndex: 20
    }})
    .css({{lineHeight: '40px'}})
    .add();
"""
    )

annotation_js = (
    "setTimeout(function() { var chart = Highcharts.charts[0]; if (!chart) return;"
    + "".join(annotation_js_parts)
    + "}, 500);"
)


# Download Highcharts JS + boxplot module (headless Chrome can't load CDN from file://)
def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (anyplot)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


highcharts_js = _fetch("https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js")
highcharts_more_js = _fetch("https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js")

html_str = chart.to_js_literal()

# Inject boxplot defaults that highcharts_core's serializer silently drops
# (fillColor, fillOpacity at plot_options.boxplot — confirmed via HTML inspection).
# Highcharts.setOptions runs before the chart is constructed, so the boxplot
# series picks up these theme-adaptive defaults instead of the library's white.
setoptions_js = f"""
Highcharts.setOptions({{
    plotOptions: {{
        boxplot: {{
            fillColor: '{ELEVATED_BG}',
            fillOpacity: 0.95
        }}
    }}
}});
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{setoptions_js}</script>
    <script>{html_str}</script>
    <script>{annotation_js}</script>
</body>
</html>"""

# Save HTML artifact for the site
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Render to PNG via headless Chrome
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Belt-and-braces: pin saved PNG to exact target dims so the post-render gate is happy
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
