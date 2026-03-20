""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: highcharts unknown | Python 3.14.3
Quality: 77/100 | Created: 2026-03-20
"""

import colorsys
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


def gradient_colors(h_start, h_end, s, lightness, n):
    """Generate n hex colors along a hue gradient in HSL space."""
    colors = []
    for i in range(n):
        frac = i / max(n - 1, 1)
        h = h_start + (h_end - h_start) * frac
        r, g, b = colorsys.hls_to_rgb(h % 1.0, lightness + (0.15 * frac), s - (0.1 * frac))
        colors.append(f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}")
    return colors


# Data - parametric curves
t_lissajous = np.linspace(0, 2 * np.pi, 500)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

t_spiral = np.linspace(0, 4 * np.pi, 600)
x_spiral = t_spiral * np.cos(t_spiral) / (4 * np.pi)
y_spiral = t_spiral * np.sin(t_spiral) / (4 * np.pi)

# Generate gradient palettes programmatically (cool-to-warm)
n_segments = 30
lissajous_colors = gradient_colors(0.6, 0.07, 0.85, 0.3, n_segments)  # blue to orange
spiral_colors = gradient_colors(0.78, 0.95, 0.75, 0.35, n_segments)  # purple to pink


def build_segments(x, y, colors, n_seg):
    """Split curve into colored segments for gradient effect."""
    segments = []
    pts_per_seg = len(x) // n_seg
    for i in range(n_seg):
        start = i * pts_per_seg
        end = start + pts_per_seg + 1 if i < n_seg - 1 else len(x)
        color_idx = int(i * (len(colors) - 1) / (n_seg - 1))
        data = [[float(x[j]), float(y[j])] for j in range(start, end)]
        segments.append({"data": data, "color": colors[color_idx]})
    return segments


lissajous_segments = build_segments(x_lissajous, y_lissajous, lissajous_colors, n_segments)
spiral_segments = build_segments(x_spiral, y_spiral, spiral_colors, n_segments)

# Create chart - square canvas for equal aspect ratio
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#fafafa",
    "spacingTop": 80,
    "spacingBottom": 160,
    "spacingLeft": 80,
    "spacingRight": 80,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

chart.options.title = {
    "text": "line-parametric \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold", "color": "#222222"},
}

chart.options.subtitle = {
    "text": "Lissajous figure x=sin(3t), y=sin(2t)  |  Archimedean spiral x=t\u00b7cos(t), y=t\u00b7sin(t)",
    "style": {"fontSize": "36px", "color": "#555555"},
}

chart.options.x_axis = {
    "title": {
        "text": "x(t) \u2014 horizontal position",
        "style": {"fontSize": "40px", "color": "#333333"},
        "margin": 24,
    },
    "labels": {"style": {"fontSize": "30px", "color": "#444444"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.06)",
    "gridLineDashStyle": "Dot",
    "lineWidth": 2,
    "lineColor": "#999999",
    "tickWidth": 0,
    "tickInterval": 0.5,
    "min": -1.3,
    "max": 1.3,
}

chart.options.y_axis = {
    "title": {"text": "y(t) \u2014 vertical position", "style": {"fontSize": "40px", "color": "#333333"}, "margin": 24},
    "labels": {"style": {"fontSize": "30px", "color": "#444444"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.06)",
    "gridLineDashStyle": "Dot",
    "lineWidth": 2,
    "lineColor": "#999999",
    "tickInterval": 0.5,
    "min": -1.3,
    "max": 1.3,
}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "floating": False,
    "itemStyle": {"fontSize": "34px", "fontWeight": "normal", "color": "#333333"},
    "symbolWidth": 50,
    "symbolHeight": 18,
    "itemDistance": 60,
    "margin": 30,
    "padding": 20,
    "backgroundColor": "rgba(255,255,255,0.85)",
    "borderRadius": 8,
    "borderWidth": 1,
    "borderColor": "#dddddd",
}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>{series.name}</b><br/>x: {point.x:.3f}, y: {point.y:.3f}",
    "style": {"fontSize": "28px"},
}

chart.options.credits = {"enabled": False}

chart.options.plot_options = {
    "scatter": {"lineWidth": 5, "states": {"hover": {"lineWidthPlus": 0}}, "marker": {"enabled": False}},
    "series": {"animation": False, "turboThreshold": 0},
}

# Add Lissajous segments
for i, seg in enumerate(lissajous_segments):
    s = ScatterSeries()
    s.data = seg["data"]
    s.color = seg["color"]
    s.name = "Lissajous: sin(3t), sin(2t)"
    s.line_width = 5
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
    s.name = "Spiral: t\u00b7cos(t), t\u00b7sin(t)"
    s.line_width = 5
    s.marker = {"enabled": False}
    s.show_in_legend = i == 0
    s.linked_to = ":previous" if i > 0 else None
    s.enable_mouse_tracking = i == 0
    chart.add_series(s)

# Lissajous is a closed curve (start=end at origin), mark with single "Lissajous t=0/2π" label
# Spiral starts at origin, ends at outer edge
marker_data = [
    (x_lissajous[0], y_lissajous[0], "Lissajous t=0,2\u03c0", lissajous_colors[0], "circle", True, -40, "right"),
    (x_spiral[0], y_spiral[0], "Spiral start", spiral_colors[0], "circle", False, 30, "left"),
    (x_spiral[-1], y_spiral[-1], "Spiral end", spiral_colors[-1], "diamond", True, -35, "center"),
]

for x, y, name, color, symbol, show_legend, y_offset, align in marker_data:
    s = ScatterSeries()
    s.data = [{"x": float(x), "y": float(y), "name": name}]
    s.name = name
    s.color = color
    s.marker = {"enabled": True, "radius": 20, "symbol": symbol, "lineWidth": 4, "lineColor": "#ffffff"}
    s.data_labels = {
        "enabled": True,
        "format": "{point.name}",
        "style": {"fontSize": "26px", "fontWeight": "bold", "color": "#333333", "textOutline": "3px #ffffff"},
        "y": y_offset,
        "align": align,
    }
    s.show_in_legend = show_legend
    chart.add_series(s)

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
<body style="margin:0; background:#fafafa;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
