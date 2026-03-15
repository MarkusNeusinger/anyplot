"""pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: highcharts unknown | Python 3.14.3
Quality: 87/100 | Created: 2026-03-15
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Alpine hiking trail elevation profile (~120 km)
np.random.seed(42)
n_points = 200
distance = np.linspace(0, 120, n_points)

# Build realistic terrain with multiple peaks and valleys
base = 1200
terrain = np.zeros(n_points)
peaks = [
    (15, 2450, 8),  # First summit
    (35, 1850, 10),  # Ridge
    (55, 2680, 7),  # Main summit
    (75, 1600, 12),  # Valley/pass
    (95, 2320, 9),  # Second summit
    (110, 1400, 10),  # Descent
]
for center, height, width in peaks:
    terrain += (height - base) * np.exp(-0.5 * ((distance - center) / width) ** 2)

terrain += base
noise = np.random.normal(0, 30, n_points)
terrain += noise
terrain = np.clip(terrain, 800, 3000)
elevation = terrain

# Landmarks along the trail
landmarks = [
    (0, elevation[0], "Grindelwald (Start)"),
    (15, elevation[np.argmin(np.abs(distance - 15))], "Faulhorn Summit"),
    (35, elevation[np.argmin(np.abs(distance - 35))], "Schynige Platte"),
    (55, elevation[np.argmin(np.abs(distance - 55))], "Jungfraujoch Pass"),
    (75, elevation[np.argmin(np.abs(distance - 75))], "Kleine Scheidegg"),
    (95, elevation[np.argmin(np.abs(distance - 95))], "Männlichen Peak"),
    (120, elevation[-1], "Lauterbrunnen (End)"),
]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 230,
    "marginLeft": 250,
    "marginRight": 250,
    "marginTop": 300,
}

chart.options.title = {
    "text": "area-elevation-profile · highcharts · pyplots.ai",
    "style": {"fontSize": "60px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": "Alpine Trail Bernese Oberland — 120 km Hiking Route · Grindelwald to Lauterbrunnen · Vertical Exaggeration ~10×",
    "style": {"fontSize": "38px", "color": "#666666"},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Distance (km)", "style": {"fontSize": "44px"}, "margin": 25},
    "labels": {"style": {"fontSize": "34px"}, "format": "{value} km"},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "tickInterval": 10,
    "min": 0,
    "max": 120,
    "crosshair": {"width": 2, "color": "rgba(48, 105, 152, 0.3)", "dashStyle": "Dash"},
    "plotLines": [
        {
            "value": lm[0],
            "color": "rgba(100, 100, 100, 0.35)",
            "width": 2,
            "dashStyle": "Dot",
            "zIndex": 4,
            "label": {
                "text": f"{lm[2]}<br/>({lm[1]:.0f} m)",
                "rotation": 0,
                "verticalAlign": "bottom",
                "y": -25,
                "x": 0,
                "textAlign": "center",
                "useHTML": True,
                "style": {"fontSize": "28px", "color": "#333333", "fontWeight": "bold", "textAlign": "center"},
            },
        }
        for lm in landmarks
    ],
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Elevation (m)", "style": {"fontSize": "44px"}},
    "labels": {"style": {"fontSize": "34px"}, "format": "{value} m"},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "min": 1000,
    "max": 3200,
    "startOnTick": False,
    "endOnTick": False,
    "plotBands": [
        {
            "from": 1000,
            "to": 1500,
            "color": "rgba(139, 195, 74, 0.08)",
            "label": {
                "text": "Valley",
                "align": "left",
                "x": 15,
                "style": {"fontSize": "28px", "color": "rgba(100, 130, 60, 0.5)", "fontStyle": "italic"},
            },
        },
        {
            "from": 1500,
            "to": 2500,
            "color": "rgba(255, 193, 7, 0.06)",
            "label": {
                "text": "Alpine",
                "align": "left",
                "x": 15,
                "style": {"fontSize": "28px", "color": "rgba(180, 140, 20, 0.5)", "fontStyle": "italic"},
            },
        },
        {
            "from": 2500,
            "to": 3200,
            "color": "rgba(156, 204, 232, 0.08)",
            "label": {
                "text": "High Alpine",
                "align": "left",
                "x": 15,
                "style": {"fontSize": "28px", "color": "rgba(80, 130, 170, 0.5)", "fontStyle": "italic"},
            },
        },
    ],
}

# Plot options
chart.options.plot_options = {
    "area": {
        "fillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [
                [0, "rgba(48, 105, 152, 0.55)"],
                [0.5, "rgba(48, 105, 152, 0.25)"],
                [1, "rgba(48, 105, 152, 0.03)"],
            ],
        },
        "lineWidth": 5,
        "color": "#306998",
        "marker": {"enabled": False},
        "tooltip": {"headerFormat": "", "pointFormat": "<b>{point.x:.1f} km</b> — Elevation: <b>{point.y:.0f} m</b>"},
        "states": {"hover": {"lineWidthPlus": 1}},
        "threshold": 1000,
    }
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "style": {"fontSize": "28px"},
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#306998",
    "borderRadius": 8,
}

# Elevation profile series
area_series = AreaSeries()
area_series.data = [[round(float(d), 2), round(float(e), 1)] for d, e in zip(distance, elevation, strict=True)]
area_series.name = "Elevation"
chart.add_series(area_series)

# Load Highcharts JS for inline embedding
html_str = chart.to_js_literal()

highcharts_js_path = Path(__file__).resolve().parents[3] / "node_modules" / "highcharts" / "highcharts.js"
if highcharts_js_path.exists():
    highcharts_js = highcharts_js_path.read_text(encoding="utf-8")
else:
    highcharts_url = "https://code.highcharts.com/highcharts.js"
    req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")

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

# Screenshot with headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
