""" anyplot.ai
hexbin-basic: Basic Hexbin Plot
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Created: 2026-05-29
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential colormap: brand green → blue (single-polarity density)
CMAP_LOW = "#009E73"  # Imprint palette position 1
CMAP_HIGH = "#4467A3"  # Imprint palette position 3

# Data - seismic sensor readings: 10,000 measurements across a monitoring grid
np.random.seed(42)
n_points = 10000

# Three activity zones with different intensities
zone_a = np.column_stack([np.random.randn(n_points // 3) * 1.2 + 2, np.random.randn(n_points // 3) * 1.0 + 3])
zone_b = np.column_stack([np.random.randn(n_points // 3) * 1.5 - 1, np.random.randn(n_points // 3) * 1.5 - 1])
zone_c = np.column_stack([np.random.randn(n_points // 3) * 0.8 + 4, np.random.randn(n_points // 3) * 0.9 - 2])
points = np.vstack([zone_a, zone_b, zone_c])

# Hexagonal binning
gridsize = 20
x_min, x_max = points[:, 0].min() - 0.5, points[:, 0].max() + 0.5
y_min, y_max = points[:, 1].min() - 0.5, points[:, 1].max() + 0.5

hex_width = (x_max - x_min) / gridsize
hex_height = hex_width * 2 / np.sqrt(3)
vert_spacing = hex_height * 0.75

hex_bins = {}
for px, py in points:
    row = int((py - y_min) / vert_spacing)
    col_offset = (row % 2) * hex_width * 0.5
    col = int((px - x_min - col_offset) / hex_width)
    hex_bins[(col, row)] = hex_bins.get((col, row), 0) + 1

tilemap_data = [{"x": col, "y": row, "value": count} for (col, row), count in hex_bins.items()]
max_count = max(item["value"] for item in tilemap_data)


# Zone center col/row positions for annotations
def _to_col_row(px, py):
    r = int((py - y_min) / vert_spacing)
    c_off = (r % 2) * hex_width * 0.5
    c = int((px - x_min - c_off) / hex_width)
    return c, r


za_col, za_row = _to_col_row(2.0, 3.0)  # Zone A — upper-center
zb_col, zb_row = _to_col_row(-1.0, -1.0)  # Zone B — lower-left
zc_col, zc_row = _to_col_row(4.0, -2.0)  # Zone C — lower-right (peak density)

# Annotation style (readable on hexbin colors, both themes)
ann_fill = "rgba(26,26,23,0.72)" if THEME == "light" else "rgba(240,239,232,0.18)"
ann_text = "#F0EFE8"

# Title with length-scaled fontsize
title_text = "Seismic Activity Density · hexbin-basic · python · highcharts · anyplot.ai"
title_fs = max(44, round(66 * 67 / len(title_text)))

subtitle_text = (
    f"Three seismic monitoring zones — peak density: {max_count} events/bin"
    f" · 10,000 readings across {len(hex_bins)} hexagonal bins"
)

# Configure chart
chart = Chart(container="container")
chart.options = HighchartsOptions()
chart.options.chart = {
    "type": "tilemap",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginTop": 140,
    "marginBottom": 160,
    "marginLeft": 160,
    "marginRight": 220,
    "animation": False,
}
chart.options.title = {"text": title_text, "style": {"fontSize": f"{title_fs}px", "fontWeight": "500", "color": INK}}
chart.options.subtitle = {"text": subtitle_text, "style": {"fontSize": "44px", "color": INK_SOFT}}
chart.options.x_axis = {
    "title": {"text": "X Position", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 0,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "lineWidth": 1,
}
chart.options.y_axis = {
    "title": {"text": "Y Position", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 0,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "lineWidth": 1,
}
chart.options.color_axis = {
    "type": "logarithmic",
    "min": 1,
    "max": int(max_count),
    "stops": [[0, CMAP_LOW], [1, CMAP_HIGH]],
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
}
chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 280,
    "symbolWidth": 36,
    "title": {"text": "Event Count", "style": {"fontSize": "44px", "fontWeight": "bold", "color": INK}},
    "itemStyle": {"fontSize": "44px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 0,
}
chart.options.tooltip = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.plot_options = {
    "tilemap": {
        "tileShape": "hexagon",
        "colsize": 1,
        "rowsize": 1,
        "animation": False,
        "states": {"hover": {"enabled": False}, "inactive": {"enabled": False}},
    }
}
chart.options.series = [
    {
        "type": "tilemap",
        "name": "Density",
        "data": tilemap_data,
        "tileShape": "hexagon",
        "dataLabels": {"enabled": False},
    }
]
js_literal = chart.to_js_literal()

# Tilemap border (not serialized by highcharts-core SDK — applied via post-render update)
border_color = "rgba(240,239,232,0.25)" if THEME == "dark" else "rgba(26,26,23,0.2)"
border_patch = json.dumps({"borderWidth": 1, "borderColor": border_color})

# Download Highcharts JS modules inline (CDN scripts blocked in headless Chrome file:// context)
module_urls = {
    "highcharts": "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js",
    "heatmap": "https://cdn.jsdelivr.net/npm/highcharts@11/modules/heatmap.js",
    "tilemap": "https://cdn.jsdelivr.net/npm/highcharts@11/modules/tilemap.js",
}
js_modules = {}
for name, url in module_urls.items():
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        js_modules[name] = response.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_modules["highcharts"]}</script>
    <script>{js_modules["heatmap"]}</script>
    <script>{js_modules["tilemap"]}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{js_literal}</script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var chart = Highcharts.charts[0];
            if (chart) {{
                chart.series[0].update({border_patch}, true);
                var zones = [
                    {{x: {za_col}, y: {za_row}, label: 'Zone A'}},
                    {{x: {zb_col}, y: {zb_row}, label: 'Zone B'}},
                    {{x: {zc_col}, y: {zc_row}, label: 'Zone C ★'}}
                ];
                zones.forEach(function(z) {{
                    var px = chart.xAxis[0].toPixels(z.x, false);
                    var py = chart.yAxis[0].toPixels(z.y, false);
                    chart.renderer.label(z.label, px - 55, py - 110)
                        .attr({{padding: 12, r: 4, fill: '{ann_fill}', zIndex: 5}})
                        .css({{color: '{ann_text}', fontSize: '40px', fontWeight: '600'}})
                        .add();
                }});
            }}
        }});
    </script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
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
# CDP override is authoritative: --window-size alone is eaten by Chrome chrome (~139 px)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL safety net: pin to exact 3200×1800 in case of ±1–2 px rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
