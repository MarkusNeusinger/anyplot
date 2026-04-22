""" pyplots.ai
campbell-basic: Campbell Diagram
Library: highcharts unknown | Python 3.14.3
Quality: 93/100 | Created: 2026-02-15
"""

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


# Data — rotordynamic natural frequencies vs rotational speed
np.random.seed(42)
speed_rpm = np.linspace(0, 6000, 80)
speed_hz = speed_rpm / 60

# Natural frequency modes (Hz) — pronounced gyroscopic effects for visual interest
# 1st Bending: rises with speed (forward whirl gyroscopic stiffening)
mode_1_bending = 18 + 0.004 * speed_rpm + 2e-7 * speed_rpm**2 + np.random.normal(0, 0.15, len(speed_rpm))
# 2nd Bending: decreases with speed (backward whirl softening)
mode_2_bending = 48 - 0.003 * speed_rpm + np.random.normal(0, 0.2, len(speed_rpm))
# 1st Torsional: mild rise with centrifugal stiffening
mode_1_torsional = 55 + 0.002 * speed_rpm + np.random.normal(0, 0.15, len(speed_rpm))
# Axial: slight decrease due to thermal growth at speed
mode_axial = 82 - 0.0015 * speed_rpm + np.random.normal(0, 0.18, len(speed_rpm))
# 2nd Torsional: nearly constant at higher frequency
mode_2_torsional = 95 + 0.0005 * speed_rpm + np.random.normal(0, 0.2, len(speed_rpm))

modes = {
    "1st Bending": mode_1_bending,
    "2nd Bending": mode_2_bending,
    "1st Torsional": mode_1_torsional,
    "Axial": mode_axial,
    "2nd Torsional": mode_2_torsional,
}

# Engine order lines: frequency = order * speed_rpm / 60
orders = [1, 2, 3]

# Find critical speed intersections (engine order line crosses natural frequency curve)
critical_speeds = []
for order in orders:
    eo_freq = order * speed_hz
    for _, mode_freq in modes.items():
        diff = eo_freq - mode_freq
        sign_changes = np.where(np.diff(np.sign(diff)))[0]
        for idx in sign_changes:
            frac = abs(diff[idx]) / (abs(diff[idx]) + abs(diff[idx + 1]))
            rpm_val = speed_rpm[idx] + frac * (speed_rpm[idx + 1] - speed_rpm[idx])
            freq_val = order * rpm_val / 60
            critical_speeds.append((float(rpm_val), float(freq_val)))

# Vertical plotLines at critical speeds
crit_rpm_values = sorted({round(rpm, 0) for rpm, _ in critical_speeds})
crit_plot_lines = [
    {"value": rpm, "color": "rgba(231, 76, 60, 0.15)", "width": 2, "dashStyle": "ShortDot", "zIndex": 0}
    for rpm in crit_rpm_values[:6]
]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "spacing": [60, 80, 80, 60],
}

chart.options.title = {
    "text": "campbell-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "600", "color": "#1a1a2e", "letterSpacing": "1px"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Natural Frequencies vs Rotational Speed \u2014 Turbine Rotor",
    "style": {"fontSize": "38px", "color": "#6c757d", "fontWeight": "400"},
}

# Highcharts-specific: plotBands for operating zones + plotLines at critical speeds
chart.options.x_axis = {
    "title": {
        "text": "Rotational Speed (RPM)",
        "style": {"fontSize": "44px", "color": "#2d3436", "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "34px", "color": "#6c757d"}, "format": "{value}"},
    "min": 0,
    "max": 6000,
    "tickInterval": 1000,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.05)",
    "gridLineDashStyle": "Dot",
    "lineWidth": 0,
    "tickWidth": 0,
    "plotBands": [
        {
            "from": 0,
            "to": 800,
            "color": "rgba(46, 204, 113, 0.07)",
            "label": {
                "text": "Idle",
                "style": {"fontSize": "28px", "color": "#6c757d", "fontWeight": "400"},
                "verticalAlign": "bottom",
                "y": -15,
            },
        },
        {
            "from": 2800,
            "to": 4200,
            "color": "rgba(52, 152, 219, 0.06)",
            "label": {
                "text": "Normal Operating Range",
                "style": {"fontSize": "28px", "color": "#6c757d", "fontWeight": "400"},
                "verticalAlign": "bottom",
                "y": -15,
            },
        },
    ],
    "plotLines": crit_plot_lines,
}

chart.options.y_axis = {
    "title": {
        "text": "Frequency (Hz)",
        "style": {"fontSize": "44px", "color": "#2d3436", "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "34px", "color": "#6c757d"}},
    "min": 0,
    "max": 120,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.05)",
    "gridLineDashStyle": "Dot",
    "lineWidth": 0,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -30,
    "y": 60,
    "floating": True,
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderWidth": 1,
    "borderColor": "#dee2e6",
    "borderRadius": 10,
    "shadow": {"color": "rgba(0,0,0,0.06)", "offsetX": 2, "offsetY": 2, "width": 8},
    "itemStyle": {"fontSize": "30px", "fontWeight": "400", "color": "#2d3436"},
    "padding": 20,
    "itemMarginTop": 6,
    "itemMarginBottom": 6,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:24px;color:{series.color}">\u25cf</span> '
        '<span style="font-size:26px">'
        "{series.name}<br/>"
        "Speed: <b>{point.x:.0f} RPM</b><br/>"
        "Frequency: <b>{point.y:.1f} Hz</b></span>"
    ),
    "backgroundColor": "rgba(255, 255, 255, 0.96)",
    "borderRadius": 10,
    "borderWidth": 1,
    "shadow": {"color": "rgba(0,0,0,0.08)", "offsetX": 1, "offsetY": 1, "width": 4},
    "style": {"fontSize": "26px"},
}

# Mode colors — refined palette starting with Python Blue
mode_colors = ["#306998", "#27ae60", "#8e44ad", "#d35400", "#2980b9"]

# Natural frequency mode series
for i, (mode_name, mode_freq) in enumerate(modes.items()):
    series = LineSeries()
    series.data = [[float(r), float(f)] for r, f in zip(speed_rpm, mode_freq, strict=False)]
    series.name = mode_name
    series.color = mode_colors[i]
    series.line_width = 5
    series.marker = {"enabled": False}
    series.z_index = 3
    chart.add_series(series)

# Engine order lines — darker color, on-chart labels via Highcharts dataLabels filter
eo_color = "#5a6c7d"
for order in orders:
    eo_freq = order * speed_hz
    mask = eo_freq <= 120
    eo_data = [[float(r), float(f)] for r, f in zip(speed_rpm[mask], eo_freq[mask], strict=False)]
    series = LineSeries()
    series.data = eo_data
    series.name = f"{order}x EO"
    series.color = eo_color
    series.line_width = 3
    series.dash_style = "LongDash"
    series.marker = {"enabled": False}
    series.enable_mouse_tracking = False
    series.z_index = 1
    # Highcharts-specific: dataLabels with filter to label only the last point on-chart
    series.data_labels = {
        "enabled": True,
        "format": f"{order}x",
        "style": {"fontSize": "30px", "fontWeight": "600", "color": "#5a6c7d", "textOutline": "3px white"},
        "align": "left",
        "x": 10,
        "y": -5,
        "filter": {"property": "x", "operator": ">", "value": float(speed_rpm[mask][-2])},
    }
    chart.add_series(series)

# Critical speed intersection markers
if critical_speeds:
    crit_series = ScatterSeries()
    crit_series.data = [[rpm, freq] for rpm, freq in critical_speeds]
    crit_series.name = "Critical Speeds"
    crit_series.color = "#e74c3c"
    crit_series.marker = {
        "radius": 16,
        "symbol": "diamond",
        "lineWidth": 3,
        "lineColor": "#c0392b",
        "fillColor": "#e74c3c",
        "states": {"hover": {"radiusPlus": 5, "lineWidthPlus": 2}},
    }
    crit_series.z_index = 5
    chart.add_series(crit_series)

# Download Highcharts JS and annotations module
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

annotations_url = "https://code.highcharts.com/modules/annotations.js"
with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()

# Save interactive HTML (CDN scripts)
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>""")

# PNG via headless Chrome (inline scripts)
png_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(png_html)
    temp_path = f.name

chrome_options = Options()
for arg in ["--headless", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--window-size=4800,2700"]:
    chrome_options.add_argument(arg)

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
