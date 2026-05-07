""" anyplot.ai
spiral-timeseries: Spiral Time Series Chart
Library: highcharts unknown | Python 3.13.13
Quality: 84/100 | Created: 2026-05-07
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data: 5 years of daily average temperatures (northern hemisphere)
np.random.seed(42)
N_YEARS = 5
DAYS_PER_YEAR = 365
n_points = N_YEARS * DAYS_PER_YEAR

day_indices = np.arange(n_points)
year_index = day_indices // DAYS_PER_YEAR
day_of_year = day_indices % DAYS_PER_YEAR

# Seasonal temperature model: 0–24°C range, peak mid-summer + slight warming trend + noise
seasonal = 12 - 12 * np.cos(2 * np.pi * day_of_year / DAYS_PER_YEAR)
trend = year_index * 0.15
noise = np.random.normal(0, 1.5, n_points)
temperatures = seasonal + trend + noise

# Normalize temperatures for viridis colormap
t_min, t_max = temperatures.min(), temperatures.max()
t_norm = (temperatures - t_min) / (t_max - t_min)

# Viridis color stops → per-point hex colors (vectorized, no function definitions)
viridis_t_stops = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
viridis_r_stops = np.array([68.0, 59.0, 33.0, 94.0, 253.0])
viridis_g_stops = np.array([1.0, 82.0, 145.0, 201.0, 231.0])
viridis_b_stops = np.array([84.0, 139.0, 140.0, 98.0, 37.0])

r_ch = np.interp(t_norm, viridis_t_stops, viridis_r_stops).astype(int)
g_ch = np.interp(t_norm, viridis_t_stops, viridis_g_stops).astype(int)
b_ch = np.interp(t_norm, viridis_t_stops, viridis_b_stops).astype(int)
point_colors = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in zip(r_ch, g_ch, b_ch, strict=True)]

# Archimedean spiral: r = start_r + spacing * (total_angle / 2π)
# Phase offset: 12-o'clock start (Jan 1 at top)
START_R = 200.0
SPACING = 250.0
PHASE = -np.pi / 2

total_angles = 2 * np.pi * day_of_year / DAYS_PER_YEAR + 2 * np.pi * year_index
radii = START_R + SPACING * total_angles / (2 * np.pi)

x_coords = radii * np.cos(total_angles + PHASE)
y_coords = radii * np.sin(total_angles + PHASE)

# Scatter data with per-point viridis colors
scatter_data = [
    {"x": round(float(x_coords[i]), 1), "y": round(float(y_coords[i]), 1), "color": point_colors[i]}
    for i in range(n_points)
]

# Spiral outer boundary for grid lines and label placement
outer_r = START_R + SPACING * (N_YEARS + 0.15)

# Month boundary angles (start-of-month day in 365-day year)
month_starts = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Build chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 2700,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "animation": False,
    "margin": [100, 80, 130, 80],
}

chart.options.title = {
    "text": "5-Year Daily Temperatures · spiral-timeseries · highcharts · anyplot.ai",
    "style": {"fontSize": "30px", "color": INK, "fontWeight": "500"},
    "margin": 22,
}

chart.options.subtitle = {
    "text": (
        f"Color encodes temperature: {t_min:.1f}°C (cold, purple) → {t_max:.1f}°C (warm, yellow)  "
        "·  Each ring = one year (2020–2024, innermost to outermost)"
    ),
    "style": {"fontSize": "19px", "color": INK_SOFT},
}

# Hide both axes — all coordinates are manual spiral-space values
chart.options.x_axis = {"visible": False, "min": -(outer_r + 180), "max": outer_r + 180}
chart.options.y_axis = {"visible": False, "min": -(outer_r + 200), "max": outer_r + 200, "title": {"text": None}}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.plot_options = {"series": {"animation": False}}

# Radial grid lines: one per month boundary, from center to outer edge
for ms, mname in zip(month_starts, month_names, strict=True):
    theta = 2 * np.pi * ms / DAYS_PER_YEAR + PHASE
    gx = round(float(outer_r * np.cos(theta)), 1)
    gy = round(float(outer_r * np.sin(theta)), 1)
    grid_line = LineSeries()
    grid_line.data = [{"x": 0.0, "y": 0.0}, {"x": gx, "y": gy}]
    grid_line.color = GRID
    grid_line.line_width = 1
    grid_line.name = mname
    grid_line.show_in_legend = False
    grid_line.enable_mouse_tracking = False
    grid_line.marker = {"enabled": False}
    chart.add_series(grid_line)

# Spiral scatter series (main data — colored by temperature)
scatter_series = ScatterSeries()
scatter_series.data = scatter_data
scatter_series.name = "Temperature"
scatter_series.marker = {"radius": 5, "symbol": "circle", "lineWidth": 0}
scatter_series.show_in_legend = False
scatter_series.enable_mouse_tracking = False
chart.add_series(scatter_series)

# Year labels at the top of each revolution (Jan 1 position, just inside spiral)
for y in range(N_YEARS):
    yr = START_R + SPACING * y - 30
    lx = round(float(yr * np.cos(PHASE)), 1)
    ly = round(float(yr * np.sin(PHASE)), 1)
    yr_series = LineSeries()
    yr_series.data = [{"x": lx, "y": ly}]
    yr_series.name = f"{2020 + y}"
    yr_series.line_width = 0
    yr_series.marker = {"enabled": False}
    yr_series.data_labels = {
        "enabled": True,
        "format": f"{2020 + y}",
        "style": {"fontSize": "24px", "color": INK, "fontWeight": "600", "textOutline": "none"},
        "verticalAlign": "bottom",
        "align": "center",
        "y": -6,
    }
    yr_series.show_in_legend = False
    yr_series.enable_mouse_tracking = False
    chart.add_series(yr_series)

# Month labels at outer edge
for ms, mname in zip(month_starts, month_names, strict=True):
    theta = 2 * np.pi * ms / DAYS_PER_YEAR + PHASE
    label_r = outer_r + 80
    mx = round(float(label_r * np.cos(theta)), 1)
    my = round(float(label_r * np.sin(theta)), 1)
    month_series = LineSeries()
    month_series.data = [{"x": mx, "y": my}]
    month_series.name = mname
    month_series.line_width = 0
    month_series.marker = {"enabled": False}
    month_series.data_labels = {
        "enabled": True,
        "format": mname,
        "style": {"fontSize": "20px", "color": INK_SOFT, "fontWeight": "400", "textOutline": "none"},
        "align": "center",
        "verticalAlign": "middle",
        "padding": 0,
    }
    month_series.show_in_legend = False
    month_series.enable_mouse_tracking = False
    chart.add_series(month_series)

# Export
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 2700px; height: 2700px;"></div>
    <script>{html_str}</script>
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
chrome_options.add_argument("--window-size=2700,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
