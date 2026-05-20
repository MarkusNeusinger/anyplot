"""anyplot.ai
maze-circular: Circular Maze Puzzle
Library: highcharts | Python 3.13
Quality: 91/100 | Updated: 2026-05-20
"""

import math
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Maze parameters
np.random.seed(42)
num_rings = 7
sectors_per_ring = [1, 6, 12, 18, 24, 30, 36, 42]
center_radius = 0.08
ring_width = (0.45 - center_radius) / num_rings

# Create cells with walls
cells = {}
for ring in range(num_rings):
    for sector in range(sectors_per_ring[ring]):
        cells[(ring, sector)] = {"walls": {"inner": True, "outer": True, "cw": True, "ccw": True}}

# Build adjacency list for maze generation
adjacency = {}
for ring in range(num_rings):
    for sector in range(sectors_per_ring[ring]):
        cell = (ring, sector)
        adjacency[cell] = []
        cw_sector = (sector + 1) % sectors_per_ring[ring]
        adjacency[cell].append(((ring, cw_sector), "cw", "ccw"))
        if ring > 0:
            inner_sectors = sectors_per_ring[ring - 1]
            inner_sector = int(sector * inner_sectors / sectors_per_ring[ring])
            adjacency[cell].append(((ring - 1, inner_sector), "inner", "outer"))

# Generate maze using Prim's algorithm (start from center)
visited = set()
walls_list = []
start_cell = (0, 0)
visited.add(start_cell)

for cell_info in adjacency[start_cell]:
    walls_list.append((start_cell, cell_info[0], cell_info[1], cell_info[2]))

while walls_list:
    idx = np.random.randint(len(walls_list))
    cell1, cell2, dir1, dir2 = walls_list.pop(idx)
    if cell2 in visited:
        continue
    visited.add(cell2)
    cells[cell1]["walls"][dir1] = False
    cells[cell2]["walls"][dir2] = False
    for neighbor_info in adjacency[cell2]:
        neighbor = neighbor_info[0]
        if neighbor not in visited:
            walls_list.append((cell2, neighbor, neighbor_info[1], neighbor_info[2]))

# Create entry at outer ring (bottom position)
entry_sector = sectors_per_ring[num_rings - 1] // 2
cells[(num_rings - 1, entry_sector)]["walls"]["outer"] = False

# Center coordinates and scale — keep x/y symmetric so maze is circular not elliptical
cx, cy = 0.5, 0.5
wall_paths = []

# Generate wall paths for concentric rings
for ring in range(num_rings):
    inner_r = center_radius + ring * ring_width
    outer_r = inner_r + ring_width
    num_sectors = sectors_per_ring[ring]
    sector_angle = 2 * math.pi / num_sectors

    for sector in range(num_sectors):
        start_angle = sector * sector_angle - math.pi / 2
        end_angle = start_angle + sector_angle

        # Inner wall arc
        if cells[(ring, sector)]["walls"]["inner"] and ring > 0:
            angles = np.linspace(start_angle, end_angle, 15)
            points = [[cx + inner_r * math.cos(a), cy + inner_r * math.sin(a)] for a in angles]
            wall_paths.append(points)

        # Outer wall arc (outermost ring only)
        if ring == num_rings - 1 and cells[(ring, sector)]["walls"]["outer"]:
            angles = np.linspace(start_angle, end_angle, 15)
            points = [[cx + outer_r * math.cos(a), cy + outer_r * math.sin(a)] for a in angles]
            wall_paths.append(points)

        # Radial wall (clockwise side of sector)
        if cells[(ring, sector)]["walls"]["cw"]:
            cw_angle = end_angle
            wall_paths.append(
                [
                    [cx + inner_r * math.cos(cw_angle), cy + inner_r * math.sin(cw_angle)],
                    [cx + outer_r * math.cos(cw_angle), cy + outer_r * math.sin(cw_angle)],
                ]
            )

# Outer boundary circle
outer_boundary_r = center_radius + num_rings * ring_width
angles = np.linspace(0, 2 * math.pi, 200)
boundary_points = [[cx + outer_boundary_r * math.cos(a), cy + outer_boundary_r * math.sin(a)] for a in angles]
boundary_points.append(boundary_points[0])

# Center goal circle
goal_angles = np.linspace(0, 2 * math.pi, 50)
goal_r = center_radius * 0.6
goal_points = [[cx + goal_r * math.cos(a), cy + goal_r * math.sin(a)] for a in goal_angles]
goal_points.append(goal_points[0])

# Entry marker — clear chevron arrow pointing inward at the bottom opening
entry_angle_center = (
    entry_sector * (2 * math.pi / sectors_per_ring[num_rings - 1])
    - math.pi / 2
    + math.pi / sectors_per_ring[num_rings - 1]
)
arrow_tip_r = outer_boundary_r - 0.012
arrow_base_r = outer_boundary_r + 0.055
perp_offset = 0.032

arrow_tip_x = cx + arrow_tip_r * math.cos(entry_angle_center)
arrow_tip_y = cy + arrow_tip_r * math.sin(entry_angle_center)
arrow_base_x = cx + arrow_base_r * math.cos(entry_angle_center)
arrow_base_y = cy + arrow_base_r * math.sin(entry_angle_center)

perp_angle = entry_angle_center + math.pi / 2
arrow_left_x = arrow_base_x + perp_offset * math.cos(perp_angle)
arrow_left_y = arrow_base_y + perp_offset * math.sin(perp_angle)
arrow_right_x = arrow_base_x - perp_offset * math.cos(perp_angle)
arrow_right_y = arrow_base_y - perp_offset * math.sin(perp_angle)

# Create Highcharts chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 2400,
    "height": 2400,
    "backgroundColor": PAGE_BG,
    "marginTop": 160,
    "marginBottom": 80,
}

chart.options.title = {
    "text": "maze-circular · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
}

# Keep axes symmetric (both 0–1) so the circular maze renders as a circle, not ellipse
chart.options.x_axis = {"visible": False, "min": 0, "max": 1}
chart.options.y_axis = {"visible": False, "min": 0, "max": 1}
chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.plot_options = {
    "series": {"animation": False, "enableMouseTracking": False, "states": {"hover": {"enabled": False}}},
    "line": {"lineWidth": 5, "marker": {"enabled": False}},
}

# Build series data
series_data = []

wall_color = INK

# Wall paths (maze structure)
for path in wall_paths:
    series_data.append(
        {"type": "line", "data": path, "color": wall_color, "lineWidth": 5, "marker": {"enabled": False}}
    )

# Outer boundary
series_data.append(
    {"type": "line", "data": boundary_points, "color": wall_color, "lineWidth": 7, "marker": {"enabled": False}}
)

# Center goal circle (brand green)
series_data.append(
    {"type": "line", "data": goal_points, "color": "#009E73", "lineWidth": 12, "marker": {"enabled": False}}
)

# Entry arrow — filled chevron rendered as two thick lines for visibility
arrow_left_path = [[arrow_left_x, arrow_left_y], [arrow_tip_x, arrow_tip_y]]
arrow_right_path = [[arrow_right_x, arrow_right_y], [arrow_tip_x, arrow_tip_y]]
arrow_stem_path = [[arrow_base_x, arrow_base_y], [arrow_tip_x, arrow_tip_y]]

# Bold yellow arrow with dark outline for contrast on both themes
for path in [arrow_left_path, arrow_right_path, arrow_stem_path]:
    series_data.append(
        {"type": "line", "data": path, "color": "#E69F00", "lineWidth": 22, "marker": {"enabled": False}}
    )
    series_data.append(
        {"type": "line", "data": path, "color": wall_color, "lineWidth": 6, "marker": {"enabled": False}}
    )

chart.options.series = series_data

# GOAL label in center via subtitle
chart.options.subtitle = {
    "text": "GOAL",
    "verticalAlign": "middle",
    "y": 20,
    "style": {"fontSize": "36px", "fontWeight": "bold", "color": "#009E73"},
}

# Download Highcharts JS
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build HTML — START label placed via absolute div near entry opening
entry_label_left_pct = (entry_x := cx + (outer_boundary_r + 0.07) * math.cos(entry_angle_center)) * 100
entry_label_top_pct = (1 - (cy + (outer_boundary_r + 0.07) * math.sin(entry_angle_center))) * 100

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG}; position:relative;">
    <div id="container" style="width: 2400px; height: 2400px;"></div>
    <div style="position:absolute; left:{entry_label_left_pct:.1f}%; top:{entry_label_top_pct:.1f}%;
                transform:translate(-50%,-50%); font-size:40px; font-weight:bold;
                color:{INK}; font-family:sans-serif;">START</div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=2400,2400")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
