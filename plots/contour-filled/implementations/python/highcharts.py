""" anyplot.ai
contour-filled: Filled Contour Plot
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-11
"""

import base64
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


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - create a 2D scalar field with multiple Gaussian peaks
np.random.seed(42)
grid_size = 80  # 80x80 grid for smooth color transitions

x = np.linspace(-4, 4, grid_size)
y = np.linspace(-4, 4, grid_size)
X, Y = np.meshgrid(x, y)

# Create an interesting surface: combination of Gaussian peaks
Z = (
    1.0 * np.exp(-((X - 1.5) ** 2 + (Y - 1.5) ** 2) / 1.5)
    + 0.9 * np.exp(-((X + 1.5) ** 2 + (Y + 1.5) ** 2) / 1.8)
    + 0.7 * np.exp(-((X - 1) ** 2 + (Y + 1.5) ** 2) / 2.0)
    - 0.6 * np.exp(-((X + 0.5) ** 2 + (Y - 0.5) ** 2) / 0.8)
)

# Normalize Z to 0-100 range for better color mapping
Z_min, Z_max = Z.min(), Z.max()
Z_normalized = (Z - Z_min) / (Z_max - Z_min) * 100

# Create heatmap data in Highcharts format: [x_index, y_index, value]
heatmap_data = []
for y_idx in range(grid_size):
    for x_idx in range(grid_size):
        heatmap_data.append([x_idx, y_idx, round(Z_normalized[y_idx, x_idx], 1)])

# Marching squares lookup table for contour extraction
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

# Extract contour lines at 15 levels
contour_levels = [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80, 85, 90, 95]
contour_series = []
label_positions = []

for level in contour_levels:
    # Extract contour segments using marching squares
    segments = []
    for i in range(grid_size - 1):
        for j in range(grid_size - 1):
            tl, tr = Z_normalized[i, j], Z_normalized[i, j + 1]
            br, bl = Z_normalized[i + 1, j + 1], Z_normalized[i + 1, j]

            config = 0
            if tl >= level:
                config |= 8
            if tr >= level:
                config |= 4
            if br >= level:
                config |= 2
            if bl >= level:
                config |= 1

            edges = ms_table[config]
            if not edges:
                continue

            edge_points = {}

            if tl != tr:
                t = (level - tl) / (tr - tl)
                if 0 <= t <= 1:
                    edge_points[0] = (j + t, i)

            if tr != br:
                t = (level - tr) / (br - tr)
                if 0 <= t <= 1:
                    edge_points[1] = (j + 1, i + t)

            if bl != br:
                t = (level - bl) / (br - bl)
                if 0 <= t <= 1:
                    edge_points[2] = (j + t, i + 1)

            if tl != bl:
                t = (level - tl) / (bl - tl)
                if 0 <= t <= 1:
                    edge_points[3] = (j, i + t)

            for e1, e2 in edges:
                if e1 in edge_points and e2 in edge_points:
                    segments.append((edge_points[e1], edge_points[e2]))

    # Connect line segments into continuous paths
    if segments:
        paths = []
        remaining = list(segments)

        while remaining:
            seg = remaining.pop(0)
            path = [seg[0], seg[1]]

            changed = True
            while changed:
                changed = False
                for i, seg in enumerate(remaining):
                    if np.allclose(seg[0], path[-1], atol=0.01):
                        path.append(seg[1])
                        remaining.pop(i)
                        changed = True
                        break
                    elif np.allclose(seg[1], path[-1], atol=0.01):
                        path.append(seg[0])
                        remaining.pop(i)
                        changed = True
                        break
                    elif np.allclose(seg[1], path[0], atol=0.01):
                        path.insert(0, seg[0])
                        remaining.pop(i)
                        changed = True
                        break
                    elif np.allclose(seg[0], path[0], atol=0.01):
                        path.insert(0, seg[1])
                        remaining.pop(i)
                        changed = True
                        break

            if len(path) >= 5:
                paths.append(path)

        # Add contour lines as series
        for path in paths:
            step = max(1, len(path) // 120)
            subsampled = path[::step]
            if len(path) > step:
                subsampled.append(path[-1])

            line_data = [[round(pt[0], 2), round(pt[1], 2)] for pt in subsampled]

            # Shadow line for visibility
            contour_series.append(
                {
                    "type": "line",
                    "name": f"Level {level}% shadow",
                    "data": line_data,
                    "color": "#000000",
                    "lineWidth": 5,
                    "marker": {"enabled": False},
                    "enableMouseTracking": False,
                    "showInLegend": False,
                    "zIndex": 9,
                }
            )

            # Main contour line
            contour_series.append(
                {
                    "type": "line",
                    "name": f"Level {level}%",
                    "data": line_data,
                    "color": "#ffffff",
                    "lineWidth": 2.5,
                    "marker": {"enabled": False},
                    "enableMouseTracking": False,
                    "showInLegend": False,
                    "zIndex": 10,
                }
            )

            # Store label position for key levels
            key_levels = [10, 30, 50, 70, 90]
            if level in key_levels and len(path) > 10 and not any(lp["level"] == level for lp in label_positions):
                mid_idx = len(path) // 2
                label_positions.append({"x": path[mid_idx][0], "y": path[mid_idx][1], "level": level})

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "heatmap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 160,
    "marginRight": 260,
    "marginLeft": 200,
    "marginTop": 100,
}

# Title
chart.options.title = {
    "text": "contour-filled · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "normal"},
}

# Create sparse category labels
x_labels_sparse = ["" for _ in range(grid_size)]
y_labels_sparse = ["" for _ in range(grid_size)]
label_interval = grid_size // 8
for i in range(0, grid_size, label_interval):
    x_labels_sparse[i] = f"{x[i]:.1f}"
    y_labels_sparse[i] = f"{y[i]:.1f}"
x_labels_sparse[-1] = f"{x[-1]:.1f}"
y_labels_sparse[-1] = f"{y[-1]:.1f}"

# X-axis
chart.options.x_axis = {
    "categories": x_labels_sparse,
    "title": {"text": "X Position (units)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "rotation": 0, "y": 35, "overflow": "allow"},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "lineWidth": 2,
    "tickLength": 10,
    "gridLineWidth": 0,
}

# Y-axis
chart.options.y_axis = {
    "categories": y_labels_sparse,
    "title": {"text": "Y Position (units)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "reversed": False,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "lineWidth": 2,
    "tickLength": 10,
    "gridLineWidth": 0,
}

# Color axis with viridis-like gradient (colorblind-safe)
chart.options.color_axis = {
    "min": 0,
    "max": 100,
    "stops": [
        [0, "#440154"],
        [0.15, "#482878"],
        [0.3, "#3e4989"],
        [0.45, "#31688e"],
        [0.6, "#26828e"],
        [0.7, "#1f9e89"],
        [0.8, "#35b779"],
        [0.9, "#6ece58"],
        [1, "#fde725"],
    ],
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "{value}%"},
}

# Legend configuration (colorbar) - more compact
chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "margin": 40,
    "verticalAlign": "middle",
    "symbolHeight": 600,
    "itemStyle": {"fontSize": "16px", "color": INK_SOFT},
    "title": {"text": "Intensity (%)", "style": {"fontSize": "20px", "color": INK}},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Tooltip
chart.options.tooltip = {
    "style": {"fontSize": "18px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "headerFormat": "",
    "pointFormat": "X: <b>{series.xAxis.categories.(point.x)}</b><br>"
    "Y: <b>{series.yAxis.categories.(point.y)}</b><br>"
    "Intensity: <b>{point.value}%</b>",
}

# Add heatmap series (creates the filled contour effect)
heatmap_series = {
    "name": "Surface Intensity",
    "type": "heatmap",
    "data": heatmap_data,
    "borderWidth": 0,
    "dataLabels": {"enabled": False},
    "zIndex": 1,
}

# Combine all series: heatmap first, then contour lines on top
all_series = [heatmap_series] + contour_series
chart.options.series = all_series

# Add annotations for contour level labels
chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": pos["x"], "y": pos["y"], "xAxis": 0, "yAxis": 0},
                "text": f"{pos['level']}%",
                "backgroundColor": ELEVATED_BG,
                "borderColor": INK_SOFT,
                "borderWidth": 1,
                "style": {"fontSize": "20px", "fontWeight": "bold", "color": INK},
                "padding": 8,
                "borderRadius": 4,
            }
            for pos in label_positions
        ],
        "labelOptions": {"shape": "rect"},
    }
]


# Download Highcharts JS modules from CDN (with fallback options)
def download_js(urls, timeout=30, max_retries=3):
    if not isinstance(urls, list):
        urls = [urls]

    for url in urls:
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    return response.read().decode("utf-8")
            except Exception:
                if attempt == max_retries - 1:
                    continue
                time.sleep(1)

    raise RuntimeError("Failed to download all CDN files from all sources")


# Primary URLs with fallback options
highcharts_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11.4.3/highcharts.js",
    "https://code.highcharts.com/highcharts.js",
]
heatmap_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11.4.3/modules/heatmap.js",
    "https://code.highcharts.com/modules/heatmap.js",
]
annotations_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11.4.3/modules/annotations.js",
    "https://code.highcharts.com/modules/annotations.js",
]

highcharts_js = download_js(highcharts_urls)
heatmap_js = download_js(heatmap_urls)
annotations_js = download_js(annotations_urls)

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive version
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
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Use CDP for full page screenshot
screenshot_config = {"captureBeyondViewport": True, "clip": {"x": 0, "y": 0, "width": 4800, "height": 2700, "scale": 1}}
result = driver.execute_cdp_cmd("Page.captureScreenshot", screenshot_config)
with open(f"plot-{THEME}.png", "wb") as f:
    f.write(base64.b64decode(result["data"]))
driver.quit()

Path(temp_path).unlink()
