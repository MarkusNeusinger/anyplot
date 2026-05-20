"""anyplot.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: highcharts | Python 3.13
Quality: 91/100 | Updated: 2026-05-20
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
LAND_COLOR = "#d4e6c5" if THEME == "light" else "#2a3a2a"

# Data — simulated Alpine elevation grid
np.random.seed(42)
lat_min, lat_max = 44.0, 50.0
lon_min, lon_max = 5.0, 15.0
grid_size = 50
lats = np.linspace(lat_min, lat_max, grid_size)
lons = np.linspace(lon_min, lon_max, grid_size)
LON, LAT = np.meshgrid(lons, lats)

alpine_ridge = 2500 * np.exp(-((LAT - 46.5) ** 2) / 0.8 - ((LON - 9.5) ** 2) / 4)
mont_blanc = 3000 * np.exp(-((LAT - 45.8) ** 2) / 0.3 - ((LON - 6.9) ** 2) / 0.3)
matterhorn = 2800 * np.exp(-((LAT - 46.0) ** 2) / 0.4 - ((LON - 7.7) ** 2) / 0.4)
austrian_alps = 2200 * np.exp(-((LAT - 47.2) ** 2) / 0.6 - ((LON - 12.5) ** 2) / 1.5)
dolomites = 2400 * np.exp(-((LAT - 46.4) ** 2) / 0.4 - ((LON - 11.8) ** 2) / 0.6)
elevation = alpine_ridge + mont_blanc + matterhorn + austrian_alps + dolomites
elevation += 200 + 100 * np.random.randn(*elevation.shape)
elevation = np.clip(elevation, 0, 4000)

# Contour extraction via marching squares (inline, no functions)
ms_table = {
    0: [],
    1: [[3, 2]],
    2: [[1, 2]],
    3: [[3, 1]],
    4: [[0, 1]],
    5: [[0, 3], [1, 2]],
    6: [[0, 2]],
    7: [[0, 3]],
    8: [[0, 3]],
    9: [[0, 2]],
    10: [[0, 1], [2, 3]],
    11: [[0, 1]],
    12: [[1, 3]],
    13: [[1, 2]],
    14: [[2, 3]],
    15: [],
}

rows, cols = elevation.shape
contour_levels = [500, 1000, 1500, 2000, 2500, 3000]
level_colors = {500: "#2E7D32", 1000: "#1565C0", 1500: "#306998", 2000: "#7B1FA2", 2500: "#C62828", 3000: "#FF6F00"}

all_features = []
label_points = []

for level in contour_levels:
    # Extract marching-squares segments
    segments = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            tl, tr = elevation[i, j], elevation[i, j + 1]
            br, bl = elevation[i + 1, j + 1], elevation[i + 1, j]
            config = (
                (8 if tl >= level else 0)
                | (4 if tr >= level else 0)
                | (2 if br >= level else 0)
                | (1 if bl >= level else 0)
            )
            edges = ms_table[config]
            if not edges:
                continue
            ep = {}
            if tl != tr:
                t = (level - tl) / (tr - tl)
                if 0 <= t <= 1:
                    ep[0] = (lons[j] + t * (lons[j + 1] - lons[j]), lats[i])
            if tr != br:
                t = (level - tr) / (br - tr)
                if 0 <= t <= 1:
                    ep[1] = (lons[j + 1], lats[i] + t * (lats[i + 1] - lats[i]))
            if bl != br:
                t = (level - bl) / (br - bl)
                if 0 <= t <= 1:
                    ep[2] = (lons[j] + t * (lons[j + 1] - lons[j]), lats[i + 1])
            if tl != bl:
                t = (level - tl) / (bl - tl)
                if 0 <= t <= 1:
                    ep[3] = (lons[j], lats[i] + t * (lats[i + 1] - lats[i]))
            for e1, e2 in edges:
                if e1 in ep and e2 in ep:
                    segments.append((ep[e1], ep[e2]))

    # Connect segments into continuous paths
    paths = []
    remaining = list(segments)
    while remaining:
        seg = remaining.pop(0)
        path = [seg[0], seg[1]]
        changed = True
        while changed:
            changed = False
            for idx in range(len(remaining)):
                s = remaining[idx]
                if np.allclose(s[0], path[-1], atol=0.001):
                    path.append(s[1])
                    remaining.pop(idx)
                    changed = True
                    break
                elif np.allclose(s[1], path[-1], atol=0.001):
                    path.append(s[0])
                    remaining.pop(idx)
                    changed = True
                    break
                elif np.allclose(s[1], path[0], atol=0.001):
                    path.insert(0, s[0])
                    remaining.pop(idx)
                    changed = True
                    break
                elif np.allclose(s[0], path[0], atol=0.001):
                    path.insert(0, s[1])
                    remaining.pop(idx)
                    changed = True
                    break
        if len(path) >= 3:
            paths.append(path)

    color = level_colors[level]
    for path_idx, path in enumerate(paths):
        step = max(1, len(path) // 80)
        subsampled = path[::step]
        if subsampled[-1] != path[-1]:
            subsampled.append(path[-1])
        coordinates = [[round(pt[0], 4), round(pt[1], 4)] for pt in subsampled]
        all_features.append(
            {"level": level, "color": color, "geometry": {"type": "LineString", "coordinates": coordinates}}
        )
        # Label midpoint for major contours (every 1000m)
        if path_idx == 0 and level % 1000 == 0 and len(path) > 5:
            mid = path[len(path) // 2]
            label_points.append({"lon": mid[0], "lat": mid[1], "level": level, "color": color})

# Build Highcharts series list
contour_series = []
legend_seen = set()
for feat in all_features:
    level, color = feat["level"], feat["color"]
    show_in_legend = level not in legend_seen
    if show_in_legend:
        legend_seen.add(level)
    contour_series.append(
        {
            "type": "mapline",
            "name": f"{level}m",
            "data": [{"geometry": feat["geometry"], "color": color}],
            "color": color,
            "lineWidth": 12 if level % 1000 == 0 else 6,
            "enableMouseTracking": True,
            "showInLegend": show_in_legend,
            "zIndex": 10 + (level // 500),
            "states": {"inactive": {"opacity": 1}},
        }
    )

label_series_data = [{"lon": lp["lon"], "lat": lp["lat"], "name": f"{lp['level']}m"} for lp in label_points]

tooltip_format = f'<span style="font-size:32px;color:{INK};">Elevation: <b>{{series.name}}</b></span>'

chart_config = {
    "chart": {"map": None, "width": 3200, "height": 1800, "backgroundColor": PAGE_BG, "spacing": [80, 60, 80, 60]},
    "title": {
        "text": "contour-map-geographic · python · highcharts · anyplot.ai",
        "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
        "y": 50,
    },
    "subtitle": {
        "text": "Terrain elevation contours (meters) · Alpine region",
        "style": {"fontSize": "44px", "color": INK_SOFT},
        "y": 110,
    },
    "mapNavigation": {"enabled": False},
    "legend": {
        "enabled": True,
        "layout": "vertical",
        "align": "right",
        "verticalAlign": "middle",
        "floating": True,
        "x": -40,
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "padding": 20,
        "itemStyle": {"fontSize": "44px", "color": INK_SOFT},
        "title": {"text": "Elevation", "style": {"fontSize": "48px", "fontWeight": "bold", "color": INK}},
        "symbolWidth": 40,
        "symbolHeight": 6,
        "itemMarginBottom": 8,
    },
    "tooltip": {"useHTML": True, "headerFormat": "", "pointFormat": tooltip_format},
    "plotOptions": {
        "mapline": {"states": {"hover": {"lineWidth": 18}}},
        "mappoint": {
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "style": {"fontSize": "36px", "fontWeight": "bold", "color": INK, "textOutline": f"4px {PAGE_BG}"},
                "allowOverlap": False,
            },
            "marker": {"enabled": False},
        },
    },
    "series": [
        {
            "type": "map",
            "name": "Terrain",
            "showInLegend": False,
            "nullColor": LAND_COLOR,
            "borderColor": INK_SOFT,
            "borderWidth": 1,
            "states": {"inactive": {"opacity": 1}},
        }
    ]
    + contour_series
    + (
        [
            {
                "type": "mappoint",
                "name": "Labels",
                "showInLegend": False,
                "enableMouseTracking": False,
                "data": label_series_data,
            }
        ]
        if label_series_data
        else []
    ),
}

chart_json = json.dumps(chart_config)

# Download Highmaps JS and Europe topology (inline for headless Chrome)
_req = urllib.request.Request(
    "https://cdn.jsdelivr.net/npm/highcharts/highmaps.js", headers={"User-Agent": "Mozilla/5.0"}
)
with urllib.request.urlopen(_req, timeout=60) as r:
    highmaps_js = r.read().decode("utf-8")

_req = urllib.request.Request(
    "https://cdn.jsdelivr.net/npm/@highcharts/map-collection/custom/europe.topo.json",
    headers={"User-Agent": "Mozilla/5.0"},
)
with urllib.request.urlopen(_req, timeout=60) as r:
    europe_topo = r.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>
        var topology = {europe_topo};
        var chartConfig = {chart_json};
        chartConfig.chart.map = topology;
        Highcharts.mapChart('container', chartConfig);
    </script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via Selenium with exact viewport control
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
time.sleep(6)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
Path(temp_path).unlink()

# Ensure exact canvas dimensions (post-render safety net)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
