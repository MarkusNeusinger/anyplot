""" anyplot.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: highcharts unknown | Python 3.13.13
Quality: 81/100 | Updated: 2026-06-08
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette + theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint categorical palette — position 1 ALWAYS first series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — Water phase diagram, Clausius-Clapeyron approximations
triple_t, triple_p = 273.16, 611.73  # triple point: 273.16 K, 611.73 Pa
critical_t, critical_p = 647.1, 2.2064e7  # critical point: 647.1 K, 22.064 MPa
R = 8.314  # gas constant J/(mol·K)

# Solid-gas (sublimation) boundary
L_sub = 51059  # sublimation enthalpy J/mol
temp_sg = np.linspace(190, triple_t, 80)
pressure_sg = triple_p * np.exp((L_sub / R) * (1 / triple_t - 1 / temp_sg))

# Liquid-gas (vaporization) boundary: triple point to critical point
L_vap = 40660  # vaporization enthalpy J/mol
temp_lg = np.linspace(triple_t, critical_t, 100)
pressure_lg = triple_p * np.exp((L_vap / R) * (1 / triple_t - 1 / temp_lg))

# Solid-liquid (melting) boundary: water's negative dP/dT slope
y_max = 1e9
temp_sl_end = triple_t + (triple_p - y_max) / (-1.3e7)
temp_sl = np.linspace(triple_t, temp_sl_end, 60)
pressure_sl = triple_p + (temp_sl - triple_t) * (-1.3e7)

sg_data = [[float(t), float(p)] for t, p in zip(temp_sg, pressure_sg, strict=True)]
lg_data = [[float(t), float(p)] for t, p in zip(temp_lg, pressure_lg, strict=True)]
sl_data = [[float(t), float(p)] for t, p in zip(temp_sl, pressure_sl, strict=True)]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

title_str = "Water Phase Diagram · phase-diagram-pt · python · highcharts · anyplot.ai"
n = len(title_str)
title_fontsize = f"{max(44, round(66 * 67 / n))}px"

chart.options.chart = {
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
    "marginBottom": 120,
    "spacingLeft": 80,
    "spacingRight": 80,
    "spacingTop": 40,
}

chart.options.title = {
    "text": title_str,
    "style": {"fontSize": title_fontsize, "fontWeight": "600", "color": INK},
    "margin": 30,
}

chart.options.subtitle = {"text": None}

chart.options.x_axis = {
    "title": {"text": "Temperature (K)", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "tickInterval": 50,
    "min": 180,
    "max": 750,
    "gridLineWidth": 0,
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickWidth": 0,
    "plotBands": [
        {"from": 180, "to": triple_t, "color": "rgba(0,158,115,0.06)"},
        {"from": critical_t, "to": 750, "color": "rgba(189,130,51,0.07)"},
    ],
}

chart.options.y_axis = {
    "type": "logarithmic",
    "title": {"text": "Pressure (Pa)", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 10,
    "max": 1e9,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "lineWidth": 2,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "enabled": True,
    "headerFormat": "",
    "pointFormat": "<b>{series.name}</b><br>T: {point.x:.1f} K<br>P: {point.y:.2e} Pa",
    "style": {"fontSize": "36px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
}

# Area fills for phase regions
chart.add_series(
    {
        "type": "area",
        "name": "Gas Region",
        "data": sg_data + lg_data,
        "threshold": 10,
        "fillColor": "rgba(0,158,115,0.07)",
        "lineWidth": 0,
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

chart.add_series(
    {
        "type": "area",
        "name": "Liquid Region",
        "data": lg_data,
        "threshold": 1e9,
        "fillColor": "rgba(68,103,163,0.07)",
        "lineWidth": 0,
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Boundary curves — Imprint positions 1, 2, 3
chart.add_series(
    {
        "type": "line",
        "name": "Sublimation Curve",
        "data": sg_data,
        "color": IMPRINT_PALETTE[0],
        "lineWidth": 6,
        "dashStyle": "ShortDash",
        "marker": {"enabled": False},
        "showInLegend": False,
        "zIndex": 5,
    }
)

chart.add_series(
    {
        "type": "line",
        "name": "Vaporization Curve",
        "data": lg_data,
        "color": IMPRINT_PALETTE[1],
        "lineWidth": 6,
        "dashStyle": "LongDash",
        "marker": {"enabled": False},
        "showInLegend": False,
        "zIndex": 5,
    }
)

chart.add_series(
    {
        "type": "line",
        "name": "Melting Curve",
        "data": sl_data,
        "color": IMPRINT_PALETTE[2],
        "lineWidth": 7,
        "dashStyle": "DashDot",
        "marker": {"enabled": False},
        "showInLegend": False,
        "zIndex": 5,
    }
)

# Triple point marker and annotation
chart.add_series(
    {
        "type": "scatter",
        "name": "Triple Point",
        "data": [[float(triple_t), float(triple_p)]],
        "color": IMPRINT_PALETTE[3],
        "marker": {
            "symbol": "circle",
            "radius": 18,
            "lineColor": PAGE_BG,
            "lineWidth": 4,
            "fillColor": IMPRINT_PALETTE[3],
        },
        "dataLabels": {
            "enabled": True,
            "useHTML": True,
            "format": (
                f'<div style="background:{IMPRINT_PALETTE[3]};color:{PAGE_BG};padding:10px 18px;'
                "border-radius:8px;font-size:28px;font-weight:600;line-height:1.4;"
                'box-shadow:0 3px 12px rgba(0,0,0,0.15);">'
                "Triple Point<br>"
                '<span style="font-weight:400;font-size:24px;">273.16 K, 611.7 Pa</span>'
                "</div>"
            ),
            "align": "left",
            "x": 30,
            "y": -10,
        },
        "showInLegend": False,
        "zIndex": 10,
    }
)

# Critical point marker and annotation
chart.add_series(
    {
        "type": "scatter",
        "name": "Critical Point",
        "data": [[float(critical_t), float(critical_p)]],
        "color": IMPRINT_PALETTE[4],
        "marker": {
            "symbol": "diamond",
            "radius": 18,
            "lineColor": PAGE_BG,
            "lineWidth": 4,
            "fillColor": IMPRINT_PALETTE[4],
        },
        "dataLabels": {
            "enabled": True,
            "useHTML": True,
            "format": (
                f'<div style="background:{IMPRINT_PALETTE[4]};color:{PAGE_BG};padding:10px 18px;'
                "border-radius:8px;font-size:28px;font-weight:600;line-height:1.4;"
                'box-shadow:0 3px 12px rgba(0,0,0,0.15);">'
                "Critical Point<br>"
                '<span style="font-weight:400;font-size:24px;">647.1 K, 22.06 MPa</span>'
                "</div>"
            ),
            "align": "right",
            "x": -30,
            "y": -20,
        },
        "showInLegend": False,
        "zIndex": 10,
    }
)

# Phase region labels — semantic color associations from Imprint palette
phase_labels = [
    ("SOLID", [215, 3e7], IMPRINT_PALETTE[2], "700", "52px"),
    ("LIQUID", [400, 2e7], IMPRINT_PALETTE[2], "700", "52px"),
    ("GAS", [500, 30], IMPRINT_PALETTE[0], "700", "52px"),
    ("SUPERCRITICAL FLUID", [690, 2e8], IMPRINT_PALETTE[3], "600", "40px"),
]

for label_text, pos, color, weight, font_size in phase_labels:
    chart.add_series(
        {
            "type": "scatter",
            "name": label_text,
            "data": [[float(pos[0]), float(pos[1])]],
            "color": "transparent",
            "marker": {"enabled": False},
            "dataLabels": {
                "enabled": True,
                "format": label_text,
                "style": {
                    "fontSize": font_size,
                    "fontWeight": weight,
                    "color": color,
                    "textOutline": f"2px {PAGE_BG}",
                    "letterSpacing": "3px",
                },
                "align": "center",
                "verticalAlign": "middle",
            },
            "enableMouseTracking": False,
            "showInLegend": False,
        }
    )

# Curve legend (HTML annotation, lower-right)
c0, c1, c2 = IMPRINT_PALETTE[0], IMPRINT_PALETTE[1], IMPRINT_PALETTE[2]
chart.add_series(
    {
        "type": "scatter",
        "name": "Legend",
        "data": [[680, 600]],
        "color": "transparent",
        "marker": {"enabled": False},
        "dataLabels": {
            "enabled": True,
            "useHTML": True,
            "format": (
                f'<div style="font-size:26px;line-height:2.2;color:{INK_SOFT};'
                f"background:{ELEVATED_BG};padding:12px 20px;border-radius:8px;"
                f'border:1px solid {INK_SOFT};">'
                f'<span style="color:{c0};font-weight:700;">── ──</span> Sublimation<br>'
                f'<span style="color:{c1};font-weight:700;">─ ─ ─</span> Vaporization<br>'
                f'<span style="color:{c2};font-weight:700;">─·─·─</span> Melting'
                "</div>"
            ),
            "align": "left",
        },
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

chart.options.plot_options = {
    "series": {"animation": False},
    "line": {"marker": {"enabled": False}},
    "area": {"marker": {"enabled": False}},
}

# Download Highcharts JS for inline embedding (CDN blocked from file:// URLs)
req = urllib.request.Request(
    "https://code.highcharts.com/highcharts.js",
    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"},
)
with urllib.request.urlopen(req, timeout=30) as response:
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

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# PNG export via Selenium headless Chrome
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
# CDP override makes viewport authoritative — --window-size alone is not reliable
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Normalize to exact 3200×1800 — guards against ±1–2 px rounding from CDP
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
