""" anyplot.ai
campbell-basic: Campbell Diagram
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-28
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
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — turbine rotor rotordynamic analysis
np.random.seed(42)
speed_rpm = np.linspace(0, 6000, 80)
speed_hz = speed_rpm / 60

# Natural frequency modes (Hz) — gyroscopic and centrifugal stiffening effects
mode_1_bending = 18 + 0.004 * speed_rpm + 2e-7 * speed_rpm**2 + np.random.normal(0, 0.15, len(speed_rpm))
mode_2_bending = 48 - 0.003 * speed_rpm + np.random.normal(0, 0.2, len(speed_rpm))
mode_1_torsional = 55 + 0.002 * speed_rpm + np.random.normal(0, 0.15, len(speed_rpm))
mode_axial = 82 - 0.0015 * speed_rpm + np.random.normal(0, 0.18, len(speed_rpm))
mode_2_torsional = 95 + 0.0005 * speed_rpm + np.random.normal(0, 0.2, len(speed_rpm))

modes = {
    "1st Bending": mode_1_bending,
    "2nd Bending": mode_2_bending,
    "1st Torsional": mode_1_torsional,
    "Axial": mode_axial,
    "2nd Torsional": mode_2_torsional,
}

orders = [1, 2, 3]

# Critical speed intersections (engine order crosses natural frequency)
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

crit_rpm_values = sorted({round(rpm, 0) for rpm, _ in critical_speeds})
crit_plot_lines = [
    {"value": rpm, "color": "rgba(174, 48, 48, 0.15)", "width": 2, "dashStyle": "ShortDot", "zIndex": 0}
    for rpm in crit_rpm_values[:6]
]

title = "campbell-basic · python · highcharts · anyplot.ai"

# Chart — 3200×1800 landscape
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "Helvetica, Arial, sans-serif", "color": INK},
    "marginRight": 160,
    "marginBottom": 130,
    "spacingTop": 30,
    "spacingLeft": 40,
    "spacingBottom": 40,
}

chart.options.title = {"text": title, "style": {"fontSize": "66px", "fontWeight": "600", "color": INK}, "margin": 20}

chart.options.subtitle = {
    "text": "Natural Frequencies vs Rotational Speed — Turbine Rotor",
    "style": {"fontSize": "40px", "color": INK_MUTED, "fontWeight": "400"},
}

chart.options.x_axis = {
    "title": {
        "text": "Rotational Speed (RPM)",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "500"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "{value}"},
    "min": 0,
    "max": 6000,
    "tickInterval": 1000,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "lineWidth": 1,
    "tickWidth": 1,
    "plotBands": [
        {
            "from": 0,
            "to": 800,
            "color": "rgba(0, 158, 115, 0.06)",
            "label": {
                "text": "Idle",
                "style": {"fontSize": "36px", "color": INK_MUTED},
                "verticalAlign": "top",
                "y": 60,
            },
        },
        {
            "from": 3000,
            "to": 5000,
            "color": "rgba(68, 103, 163, 0.06)",
            "label": {
                "text": "Normal Operating Range",
                "style": {"fontSize": "36px", "color": INK_MUTED},
                "verticalAlign": "top",
                "y": 60,
            },
        },
    ],
    "plotLines": crit_plot_lines,
}

chart.options.y_axis = {
    "title": {"text": "Frequency (Hz)", "style": {"fontSize": "56px", "color": INK, "fontWeight": "500"}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 0,
    "max": 120,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "lineWidth": 1,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -30,
    "y": 80,
    "floating": True,
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "itemStyle": {"fontSize": "36px", "fontWeight": "400", "color": INK_SOFT},
    "padding": 20,
    "itemMarginTop": 6,
    "itemMarginBottom": 6,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:28px;color:{series.color}">●</span> '
        '<span style="font-size:30px">'
        "{series.name}<br/>"
        "Speed: <b>{point.x:.0f} RPM</b><br/>"
        "Frequency: <b>{point.y:.1f} Hz</b></span>"
    ),
    "backgroundColor": ELEVATED_BG,
    "borderRadius": 8,
    "borderWidth": 1,
    "style": {"fontSize": "30px", "color": INK},
}

# Mode colors: anyplot positions 1-4 then position 6 (skipping pos 5 red, reserved for critical speeds)
mode_colors = [
    ANYPLOT_PALETTE[0],  # #009E73 brand green — 1st Bending
    ANYPLOT_PALETTE[1],  # #C475FD lavender    — 2nd Bending
    ANYPLOT_PALETTE[2],  # #4467A3 blue        — 1st Torsional
    ANYPLOT_PALETTE[3],  # #BD8233 ochre       — Axial
    ANYPLOT_PALETTE[5],  # #2ABCCD cyan        — 2nd Torsional
]

for i, (mode_name, mode_freq) in enumerate(modes.items()):
    series = LineSeries()
    series.data = [[float(r), float(f)] for r, f in zip(speed_rpm, mode_freq, strict=False)]
    series.name = mode_name
    series.color = mode_colors[i]
    series.line_width = 5
    series.marker = {"enabled": False}
    series.z_index = 3
    chart.add_series(series)

# Engine order excitation lines — labeled at endpoint, 1x aligned right to avoid right-edge clip
for order in orders:
    eo_freq = order * speed_hz
    mask = eo_freq <= 120
    eo_data = [[float(r), float(f)] for r, f in zip(speed_rpm[mask], eo_freq[mask], strict=False)]
    label_align = "right" if order == 1 else "left"
    label_x = -8 if order == 1 else 8
    series = LineSeries()
    series.data = eo_data
    series.name = f"{order}x EO"
    series.color = INK_MUTED
    series.line_width = 3
    series.dash_style = "LongDash"
    series.marker = {"enabled": False}
    series.enable_mouse_tracking = False
    series.z_index = 1
    series.data_labels = {
        "enabled": True,
        "format": f"{order}x",
        "style": {"fontSize": "36px", "fontWeight": "600", "color": INK_SOFT, "textOutline": f"3px {PAGE_BG}"},
        "align": label_align,
        "x": label_x,
        "y": -5,
        "filter": {"property": "x", "operator": ">", "value": float(speed_rpm[mask][-2])},
    }
    chart.add_series(series)

# Critical speed markers — anyplot matte red (semantic: resonance danger)
if critical_speeds:
    crit_series = ScatterSeries()
    crit_series.data = [[rpm, freq] for rpm, freq in critical_speeds]
    crit_series.name = "Critical Speeds"
    crit_series.color = ANYPLOT_PALETTE[4]  # #AE3030 matte red
    crit_series.marker = {
        "radius": 14,
        "symbol": "diamond",
        "lineWidth": 2,
        "lineColor": ANYPLOT_PALETTE[4],
        "fillColor": ANYPLOT_PALETTE[4],
        "states": {"hover": {"radiusPlus": 4}},
    }
    crit_series.z_index = 5
    chart.add_series(crit_series)

# Download Highcharts JS (must be inline for file:// headless Chrome)
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
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# PNG via headless Chrome — CDP override is authoritative for exact viewport
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
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL safety net — pin to exact 3200×1800 in case of ±1–2 px Chrome rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
