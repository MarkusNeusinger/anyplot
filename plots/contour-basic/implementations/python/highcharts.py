""" pyplots.ai
contour-basic: Basic Contour Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import base64
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - create a 2D scalar field using a mathematical function
np.random.seed(42)
grid_size = 100  # 100x100 grid for smooth appearance

x = np.linspace(-3, 3, grid_size)
y = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x, y)

# Create an interesting surface: combination of Gaussian peaks
# Simulates temperature distribution across a 2D surface
Z = (
    np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))
    + 0.8 * np.exp(-((X + 1) ** 2 + (Y + 1) ** 2))
    - 0.5 * np.exp(-((X) ** 2 + (Y - 1.5) ** 2) / 0.5)
)

# Normalize Z to 0-100 range for better color mapping
Z_min, Z_max = Z.min(), Z.max()
Z_normalized = (Z - Z_min) / (Z_max - Z_min) * 100

# Create heatmap data in Highcharts format: [x_index, y_index, value]
heatmap_data = []
for y_idx in range(grid_size):
    for x_idx in range(grid_size):
        heatmap_data.append([x_idx, y_idx, round(Z_normalized[y_idx, x_idx], 1)])


def marching_squares_contour(Z, level):
    """Extract contour paths using marching squares algorithm with linear interpolation.

    Returns smooth contour lines by interpolating exact crossing points on cell edges.
    """
    rows, cols = Z.shape
    segments = []

    # Marching squares lookup table - maps cell configuration to edge crossings
    # Each cell corner is labeled: top-left=0, top-right=1, bottom-right=2, bottom-left=3
    # Edge indices: top=0, right=1, bottom=2, left=3
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

    # Process each cell
    for i in range(rows - 1):
        for j in range(cols - 1):
            # Get cell corners (clockwise from top-left)
            tl = Z[i, j]
            tr = Z[i, j + 1]
            br = Z[i + 1, j + 1]
            bl = Z[i + 1, j]

            # Compute cell configuration
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

            # Interpolate crossing points on edges
            edge_points = {}

            # Top edge (between tl and tr)
            if tl != tr:
                t = (level - tl) / (tr - tl)
                if 0 <= t <= 1:
                    edge_points[0] = (j + t, i)

            # Right edge (between tr and br)
            if tr != br:
                t = (level - tr) / (br - tr)
                if 0 <= t <= 1:
                    edge_points[1] = (j + 1, i + t)

            # Bottom edge (between bl and br)
            if bl != br:
                t = (level - bl) / (br - bl)
                if 0 <= t <= 1:
                    edge_points[2] = (j + t, i + 1)

            # Left edge (between tl and bl)
            if tl != bl:
                t = (level - tl) / (bl - tl)
                if 0 <= t <= 1:
                    edge_points[3] = (j, i + t)

            # Create segments
            for e1, e2 in edges:
                if e1 in edge_points and e2 in edge_points:
                    segments.append((edge_points[e1], edge_points[e2]))

    return segments


def connect_segments(segments):
    """Connect line segments into continuous paths."""
    if not segments:
        return []

    paths = []
    remaining = list(segments)

    while remaining:
        # Start new path
        seg = remaining.pop(0)
        path = [seg[0], seg[1]]

        # Try to extend path
        changed = True
        while changed:
            changed = False
            for i, seg in enumerate(remaining):
                # Check if segment connects to end of path
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
                # Check if segment connects to start of path
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

    return paths


# Extract contour lines using marching squares algorithm (pure numpy)
contour_levels = [10, 20, 30, 40, 50, 60, 70, 80, 90]

# Consistent white contour lines with black shadow for visibility on viridis colormap
CONTOUR_COLOR = "#ffffff"
CONTOUR_SHADOW = "#000000"

contour_series = []
label_positions = []

for level in contour_levels:
    segments = marching_squares_contour(Z_normalized, level)
    paths = connect_segments(segments)

    for path in paths:
        if len(path) < 5:
            continue

        # Subsample for performance if path is very long
        step = max(1, len(path) // 150)
        subsampled = path[::step]
        if len(path) > step:
            subsampled.append(path[-1])

        line_data = [[round(pt[0], 2), round(pt[1], 2)] for pt in subsampled]

        # Add shadow line for better visibility
        contour_series.append(
            {
                "type": "line",
                "name": f"Level {level}% shadow",
                "data": line_data,
                "color": CONTOUR_SHADOW,
                "lineWidth": 7,
                "dashStyle": "Solid",
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
                "color": CONTOUR_COLOR,
                "lineWidth": 4,
                "dashStyle": "Solid",
                "marker": {"enabled": False},
                "enableMouseTracking": False,
                "showInLegend": False,
                "zIndex": 10,
            }
        )

        # Store position for label (one per level, using first valid path)
        if len(path) > 10 and not any(lp["level"] == level for lp in label_positions):
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
    "backgroundColor": "#ffffff",
    "marginBottom": 180,
    "marginRight": 320,
    "marginLeft": 220,
    "marginTop": 100,
}

# Title
chart.options.title = {
    "text": "contour-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
}

# Create sparse category labels (show at key positions)
x_labels_sparse = ["" for _ in range(grid_size)]
y_labels_sparse = ["" for _ in range(grid_size)]
label_interval = grid_size // 6
for i in range(0, grid_size, label_interval):
    x_labels_sparse[i] = f"{x[i]:.1f}"
    y_labels_sparse[i] = f"{y[i]:.1f}"
x_labels_sparse[-1] = f"{x[-1]:.1f}"
y_labels_sparse[-1] = f"{y[-1]:.1f}"

# X-axis with more visible grid lines
chart.options.x_axis = {
    "categories": x_labels_sparse,
    "title": {"text": "X Position (units)", "style": {"fontSize": "48px"}, "y": 30},
    "labels": {"style": {"fontSize": "36px"}, "rotation": 0, "y": 45},
    "lineWidth": 3,
    "tickLength": 12,
    "gridLineWidth": 3,
    "gridLineColor": "rgba(200, 200, 200, 0.7)",
    "gridLineDashStyle": "Dot",
}

# Y-axis with more visible grid lines
chart.options.y_axis = {
    "categories": y_labels_sparse,
    "title": {"text": "Y Position (units)", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "reversed": False,
    "lineWidth": 3,
    "tickLength": 12,
    "gridLineWidth": 3,
    "gridLineColor": "rgba(200, 200, 200, 0.7)",
    "gridLineDashStyle": "Dot",
}

# Color axis with viridis-like gradient (colorblind-safe)
chart.options.color_axis = {
    "min": 0,
    "max": 100,
    "stops": [[0, "#440154"], [0.25, "#3b528b"], [0.5, "#21918c"], [0.75, "#5ec962"], [1, "#fde725"]],
    "labels": {"style": {"fontSize": "32px"}, "format": "{value}%"},
}

# Legend configuration (colorbar)
chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "margin": 50,
    "verticalAlign": "middle",
    "symbolHeight": 700,
    "itemStyle": {"fontSize": "32px"},
    "title": {"text": "Intensity (%)", "style": {"fontSize": "40px"}},
}

# Tooltip
chart.options.tooltip = {
    "style": {"fontSize": "32px"},
    "headerFormat": "",
    "pointFormat": "X: <b>{series.xAxis.categories.(point.x)}</b><br>"
    "Y: <b>{series.yAxis.categories.(point.y)}</b><br>"
    "Intensity: <b>{point.value}%</b>",
}

# Add heatmap series first (background - filled contour effect)
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

# Add annotations for contour level labels with high visibility
chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": pos["x"], "y": pos["y"], "xAxis": 0, "yAxis": 0},
                "text": f"{pos['level']}%",
                "backgroundColor": "rgba(255, 255, 255, 0.95)",
                "borderColor": "#333333",
                "borderWidth": 3,
                "style": {"fontSize": "36px", "fontWeight": "bold", "color": "#000000"},
                "padding": 12,
                "borderRadius": 8,
            }
            for pos in label_positions
        ],
        "labelOptions": {"shape": "rect"},
    }
]

# Download Highcharts JS modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
heatmap_url = "https://code.highcharts.com/modules/heatmap.js"
annotations_url = "https://code.highcharts.com/modules/annotations.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

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
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/heatmap.js"></script>
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(standalone_html)

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
with open("plot.png", "wb") as f:
    f.write(base64.b64decode(result["data"]))
driver.quit()

Path(temp_path).unlink()
