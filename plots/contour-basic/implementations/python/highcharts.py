""" anyplot.ai
contour-basic: Basic Contour Plot
Library: highcharts unknown | Python 3.14.4
Quality: 90/100 | Updated: 2026-04-24
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data — simulated topographic elevation map over a 10 km × 10 km mountain region
np.random.seed(42)
grid_n = 80
x_km = np.linspace(0, 10, grid_n)
y_km = np.linspace(0, 10, grid_n)
X, Y = np.meshgrid(x_km, y_km)

elevation = (
    850 * np.exp(-((X - 7) ** 2 + (Y - 7) ** 2) / 4.0)
    + 550 * np.exp(-((X - 2.5) ** 2 + (Y - 3) ** 2) / 3.0)
    - 180 * np.exp(-((X - 5) ** 2 + (Y - 5) ** 2) / 8.0)
    + 12 * X
    + 350
)
el_min = float(elevation.min())
el_max = float(elevation.max())

# Heatmap cells use integer grid indices (Highcharts Python wrapper requires
# integer colsize/rowsize, so we work in index-space and label the axis in km)
heatmap_data = [[int(i), int(j), round(float(elevation[j, i]), 1)] for j in range(grid_n) for i in range(grid_n)]

# Sparse km labels at even km positions along each axis
km_labels_x = [""] * grid_n
km_labels_y = [""] * grid_n
for km in range(0, 11, 2):
    idx = round(km * (grid_n - 1) / 10)
    km_labels_x[idx] = str(km)
    km_labels_y[idx] = str(km)

# Contour extraction via marching squares (pure numpy, inline — no helpers)
# Corner indices: top-left=0, top-right=1, bottom-right=2, bottom-left=3
# Edge indices:   top=0, right=1, bottom=2, left=3
ms_edges = {
    0: [],
    1: [(3, 2)],
    2: [(1, 2)],
    3: [(3, 1)],
    4: [(0, 1)],
    5: [(0, 3), (1, 2)],
    6: [(0, 2)],
    7: [(0, 3)],
    8: [(0, 3)],
    9: [(0, 2)],
    10: [(0, 1), (2, 3)],
    11: [(0, 1)],
    12: [(1, 3)],
    13: [(1, 2)],
    14: [(2, 3)],
    15: [],
}

contour_levels = [400, 500, 600, 700, 800, 900, 1000, 1100]
contour_series = []

for level in contour_levels:
    # Collect every cell-crossing as a segment in (i, j) index space
    segments = []
    for j in range(grid_n - 1):
        for i in range(grid_n - 1):
            tl = elevation[j, i]
            tr = elevation[j, i + 1]
            br = elevation[j + 1, i + 1]
            bl = elevation[j + 1, i]
            config = (
                (8 if tl >= level else 0)
                | (4 if tr >= level else 0)
                | (2 if br >= level else 0)
                | (1 if bl >= level else 0)
            )
            edges = ms_edges[config]
            if not edges:
                continue
            pts = {}
            if tl != tr:
                t = (level - tl) / (tr - tl)
                if 0 <= t <= 1:
                    pts[0] = (i + t, j)
            if tr != br:
                t = (level - tr) / (br - tr)
                if 0 <= t <= 1:
                    pts[1] = (i + 1, j + t)
            if bl != br:
                t = (level - bl) / (br - bl)
                if 0 <= t <= 1:
                    pts[2] = (i + t, j + 1)
            if tl != bl:
                t = (level - tl) / (bl - tl)
                if 0 <= t <= 1:
                    pts[3] = (i, j + t)
            for a, b in edges:
                if a in pts and b in pts:
                    segments.append((pts[a], pts[b]))

    # Chain adjacent segments into continuous polylines
    remaining = list(segments)
    tol = 0.05
    paths = []
    while remaining:
        seg = remaining.pop()
        path = [seg[0], seg[1]]
        extended = True
        while extended:
            extended = False
            for k in range(len(remaining) - 1, -1, -1):
                a, b = remaining[k]
                if abs(a[0] - path[-1][0]) < tol and abs(a[1] - path[-1][1]) < tol:
                    path.append(b)
                    remaining.pop(k)
                    extended = True
                    break
                if abs(b[0] - path[-1][0]) < tol and abs(b[1] - path[-1][1]) < tol:
                    path.append(a)
                    remaining.pop(k)
                    extended = True
                    break
                if abs(b[0] - path[0][0]) < tol and abs(b[1] - path[0][1]) < tol:
                    path.insert(0, a)
                    remaining.pop(k)
                    extended = True
                    break
                if abs(a[0] - path[0][0]) < tol and abs(a[1] - path[0][1]) < tol:
                    path.insert(0, b)
                    remaining.pop(k)
                    extended = True
                    break
        if len(path) >= 4:
            paths.append(path)

    # Emit null-separated polylines as a single line series per level
    data = []
    for path in paths:
        data.extend([[round(p[0], 3), round(p[1], 3)] for p in path])
        data.append([None, None])
    contour_series.append(
        {
            "type": "line",
            "name": f"{level} m",
            "data": data,
            "color": "rgba(255,255,255,0.85)",
            "lineWidth": 3,
            "marker": {"enabled": False},
            "enableMouseTracking": False,
            "showInLegend": False,
            "zIndex": 5,
            "clip": True,
        }
    )

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "plotBackgroundColor": PAGE_BG,
    "style": {"fontFamily": "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif", "color": INK},
    "spacingTop": 80,
    "spacingRight": 120,
    "spacingBottom": 80,
    "spacingLeft": 80,
}

chart.options.title = {
    "text": "Mountain Terrain · contour-basic · highcharts · anyplot.ai",
    "align": "left",
    "x": 40,
    "style": {"fontSize": "68px", "fontWeight": "600", "color": INK, "letterSpacing": "-0.5px"},
    "margin": 20,
}
chart.options.subtitle = {
    "text": "Simulated elevation across a 10 km × 10 km region, 100 m contour intervals",
    "align": "left",
    "x": 40,
    "style": {"fontSize": "32px", "fontWeight": "400", "color": INK_MUTED},
}

chart.options.x_axis = {
    "categories": km_labels_x,
    "title": {
        "text": "Distance East (km)",
        "style": {"fontSize": "40px", "fontWeight": "500", "color": INK},
        "margin": 28,
    },
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}, "y": 36},
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickColor": INK_SOFT,
    "tickLength": 0,
    "gridLineWidth": 0,
    "min": 0,
    "max": grid_n - 1,
    "startOnTick": False,
    "endOnTick": False,
}
chart.options.y_axis = {
    "categories": km_labels_y,
    "title": {
        "text": "Distance North (km)",
        "style": {"fontSize": "40px", "fontWeight": "500", "color": INK},
        "margin": 28,
    },
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}, "x": -16},
    "lineColor": INK_SOFT,
    "lineWidth": 0,
    "tickColor": INK_SOFT,
    "tickLength": 0,
    "gridLineWidth": 0,
    "min": 0,
    "max": grid_n - 1,
    "startOnTick": False,
    "endOnTick": False,
}

# Viridis continuous colormap for the elevation surface
chart.options.color_axis = {
    "min": round(el_min),
    "max": round(el_max),
    "stops": [[0.0, "#440154"], [0.25, "#3b528b"], [0.5, "#21918c"], [0.75, "#5ec962"], [1.0, "#fde725"]],
    "labels": {"style": {"fontSize": "26px", "color": INK_SOFT}, "format": "{value} m"},
    "tickInterval": 200,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": PAGE_BG,
}

chart.options.legend = {
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "symbolHeight": 1800,
    "symbolWidth": 48,
    "x": -20,
    "title": {"text": "Elevation", "style": {"fontSize": "30px", "color": INK, "fontWeight": "500"}},
    "itemStyle": {"color": INK_SOFT, "fontSize": "26px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 0,
    "padding": 18,
}

chart.options.credits = {"enabled": False}
chart.options.tooltip = {"enabled": False}

chart.options.plot_options = {
    "heatmap": {"borderWidth": 0, "nullColor": PAGE_BG, "enableMouseTracking": False},
    "series": {"animation": False, "states": {"inactive": {"opacity": 1}}},
}

chart.options.series = [
    {"type": "heatmap", "name": "Elevation", "data": heatmap_data, "showInLegend": False, "zIndex": 1},
    *contour_series,
]

# Download Highcharts + heatmap module (headless Chrome can't load CDN from file://)
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts.js"
heatmap_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/modules/heatmap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

chart_js = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)
container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
