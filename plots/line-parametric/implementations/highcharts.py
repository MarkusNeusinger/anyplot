"""pyplots.ai
line-parametric: Parametric Curve Plot
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - parametric curves
t_lissajous = np.linspace(0, 2 * np.pi, 500)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

t_spiral = np.linspace(0, 4 * np.pi, 600)
x_spiral = t_spiral * np.cos(t_spiral) / (4 * np.pi)
y_spiral = t_spiral * np.sin(t_spiral) / (4 * np.pi)

# Color palettes for gradient segments (cool to warm)
lissajous_colors = [
    "#1a3a5c",
    "#1e4d7a",
    "#226099",
    "#2974b8",
    "#3088d0",
    "#3d9be0",
    "#4faeeb",
    "#6abfef",
    "#85cfef",
    "#a0ddef",
    "#bee8e0",
    "#d6efc0",
    "#e8f3a0",
    "#f0e880",
    "#f5d860",
    "#f5c440",
    "#f0a828",
    "#e88c18",
    "#dd7010",
    "#cc5500",
]

spiral_colors = [
    "#2d1b69",
    "#3a1f8a",
    "#4725a6",
    "#542bbe",
    "#6233d4",
    "#713de6",
    "#8049f0",
    "#9058f5",
    "#a06af7",
    "#b07ef8",
    "#be93f7",
    "#cca8f5",
    "#d6bcf0",
    "#ddd0ea",
    "#e0d8e0",
    "#e8c8d0",
    "#ebb8c0",
    "#eda8b0",
    "#ee98a0",
    "#ee8890",
]

n_segments = 40

# Build segment data for both curves
lissajous_segments = []
pts_per_seg = len(x_lissajous) // n_segments
for i in range(n_segments):
    start = i * pts_per_seg
    end = start + pts_per_seg + 1 if i < n_segments - 1 else len(x_lissajous)
    color_idx = int(i * (len(lissajous_colors) - 1) / (n_segments - 1))
    data = [[float(x_lissajous[j]), float(y_lissajous[j])] for j in range(start, end)]
    lissajous_segments.append({"data": data, "color": lissajous_colors[color_idx]})

spiral_segments = []
pts_per_seg = len(x_spiral) // n_segments
for i in range(n_segments):
    start = i * pts_per_seg
    end = start + pts_per_seg + 1 if i < n_segments - 1 else len(x_spiral)
    color_idx = int(i * (len(spiral_colors) - 1) / (n_segments - 1))
    data = [[float(x_spiral[j]), float(y_spiral[j])] for j in range(start, end)]
    spiral_segments.append({"data": data, "color": spiral_colors[color_idx]})

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingTop": 80,
    "spacingBottom": 80,
    "spacingLeft": 60,
    "spacingRight": 60,
}

chart.options.title = {
    "text": "line-parametric · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": "Lissajous figure x=sin(3t), y=sin(2t) and Archimedean spiral x=t·cos(t), y=t·sin(t)",
    "style": {"fontSize": "36px", "color": "#666666"},
}

chart.options.x_axis = {
    "title": {"text": "x(t)", "style": {"fontSize": "44px"}, "margin": 20},
    "labels": {"style": {"fontSize": "32px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.08)",
    "lineWidth": 2,
    "tickWidth": 0,
    "min": -1.3,
    "max": 1.3,
}

chart.options.y_axis = {
    "title": {"text": "y(t)", "style": {"fontSize": "44px"}, "margin": 20},
    "labels": {"style": {"fontSize": "32px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.08)",
    "lineWidth": 2,
    "min": -1.3,
    "max": 1.3,
}

chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "36px"}, "symbolWidth": 40}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>{series.name}</b><br/>x: {point.x:.3f}, y: {point.y:.3f}",
    "style": {"fontSize": "28px"},
}

chart.options.credits = {"enabled": False}

# Plot options
chart.options.plot_options = {
    "scatter": {"lineWidth": 6, "states": {"hover": {"lineWidthPlus": 0}}, "marker": {"enabled": False}},
    "series": {"animation": False, "turboThreshold": 0},
}

# Add Lissajous segments
for i, seg in enumerate(lissajous_segments):
    s = ScatterSeries()
    s.data = seg["data"]
    s.color = seg["color"]
    s.name = "Lissajous: sin(3t), sin(2t)"
    s.line_width = 6
    s.marker = {"enabled": False}
    s.show_in_legend = i == 0
    s.linked_to = ":previous" if i > 0 else None
    s.enable_mouse_tracking = i == 0
    chart.add_series(s)

# Add spiral segments
for i, seg in enumerate(spiral_segments):
    s = ScatterSeries()
    s.data = seg["data"]
    s.color = seg["color"]
    s.name = "Spiral: t·cos(t), t·sin(t)"
    s.line_width = 6
    s.marker = {"enabled": False}
    s.show_in_legend = i == 0
    s.linked_to = ":previous" if i > 0 else None
    s.enable_mouse_tracking = i == 0
    chart.add_series(s)

# Mark start and end points for Lissajous
start_liss = ScatterSeries()
start_liss.data = [[float(x_lissajous[0]), float(y_lissajous[0])]]
start_liss.name = "Start (t=0)"
start_liss.color = "#1a3a5c"
start_liss.marker = {"enabled": True, "radius": 18, "symbol": "circle", "lineWidth": 4, "lineColor": "#ffffff"}
start_liss.show_in_legend = True
chart.add_series(start_liss)

end_liss = ScatterSeries()
end_liss.data = [[float(x_lissajous[-1]), float(y_lissajous[-1])]]
end_liss.name = "End (t=2\u03c0)"
end_liss.color = "#cc5500"
end_liss.marker = {"enabled": True, "radius": 18, "symbol": "diamond", "lineWidth": 4, "lineColor": "#ffffff"}
end_liss.show_in_legend = True
chart.add_series(end_liss)

# Mark start and end points for spiral
start_spiral = ScatterSeries()
start_spiral.data = [[float(x_spiral[0]), float(y_spiral[0])]]
start_spiral.name = "Spiral start"
start_spiral.color = "#2d1b69"
start_spiral.marker = {"enabled": True, "radius": 18, "symbol": "circle", "lineWidth": 4, "lineColor": "#ffffff"}
start_spiral.show_in_legend = False
chart.add_series(start_spiral)

end_spiral = ScatterSeries()
end_spiral.data = [[float(x_spiral[-1]), float(y_spiral[-1])]]
end_spiral.name = "Spiral end"
end_spiral.color = "#ee8890"
end_spiral.marker = {"enabled": True, "radius": 18, "symbol": "diamond", "lineWidth": 4, "lineColor": "#ffffff"}
end_spiral.show_in_legend = False
chart.add_series(end_spiral)

# Download Highcharts JS for inline embedding
highcharts_js = None
for url in ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts JS")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
