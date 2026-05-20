""" anyplot.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-20
"""

import os
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_MED = "rgba(26,26,23,0.35)" if THEME == "light" else "rgba(240,239,232,0.35)"
GRID_FAINT = "rgba(26,26,23,0.22)" if THEME == "light" else "rgba(240,239,232,0.22)"
ANNOTATION_BG = "rgba(255,253,246,0.92)" if THEME == "light" else "rgba(36,36,32,0.92)"

# Data: antenna impedance sweep 1–6 GHz, resonance near 3.5 GHz
Z0 = 50.0
np.random.seed(42)
n_points = 50
frequencies = np.linspace(1e9, 6e9, n_points)

f_res = 3.5e9
Q = 5.0
f_norm = (frequencies - f_res) / (f_res / Q)
z_real = Z0 * (1 + 0.3 * np.exp(-(f_norm**2)))
z_imag = Z0 * 0.8 * np.tanh(f_norm) * (1 + 0.2 * np.sin(2 * np.pi * frequencies / 1e9))

z_normalized = (z_real + 1j * z_imag) / Z0
gamma = (z_normalized - 1) / (z_normalized + 1)
gamma_x = gamma.real
gamma_y = gamma.imag

# Chart setup
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 2400,
    "height": 2600,
    "backgroundColor": PAGE_BG,
    "marginTop": 200,
    "marginBottom": 330,
    "marginLeft": 250,
    "marginRight": 80,
}

chart.options.title = {
    "text": "smith-chart-basic · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "Antenna Impedance Sweep 1–6 GHz (Z₀ = 50 Ω)",
    "style": {"fontSize": "44px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "title": {"text": "Re(Γ)", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": -1.2,
    "max": 1.2,
    "tickInterval": 0.5,
    "gridLineWidth": 0,
    "lineWidth": 1,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.y_axis = {
    "title": {"text": "Im(Γ)", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": -1.2,
    "max": 1.2,
    "tickInterval": 0.5,
    "gridLineWidth": 0,
    "lineWidth": 1,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.legend = {
    "enabled": True,
    "layout": "vertical",
    "align": "left",
    "verticalAlign": "top",
    "floating": True,
    "x": 270,
    "y": 210,
    "itemStyle": {"color": INK_SOFT, "fontSize": "36px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 12,
    "itemMarginBottom": 6,
}

# Unit circle — |Γ| = 1 boundary
theta_uc = np.linspace(0, 2 * np.pi, 300)
unit_circle_series = ScatterSeries()
unit_circle_series.data = [[float(np.cos(t)), float(np.sin(t))] for t in theta_uc]
unit_circle_series.name = "Unit Circle"
unit_circle_series.marker = {"enabled": False}
unit_circle_series.line_width = 3
unit_circle_series.color = INK
unit_circle_series.enable_mouse_tracking = False
unit_circle_series.show_in_legend = False
chart.add_series(unit_circle_series)

# Resistance circles (constant R — Smith chart grid)
for r in [0.2, 0.5, 1, 2, 5]:
    rc_center_x = r / (r + 1)
    rc_radius = 1 / (r + 1)
    theta_r = np.linspace(0, 2 * np.pi, 300)
    rx = rc_center_x + rc_radius * np.cos(theta_r)
    ry = rc_radius * np.sin(theta_r)
    inside = rx**2 + ry**2 <= 1.001
    rx[~inside] = np.nan
    ry[~inside] = np.nan
    mask_r = ~np.isnan(rx) & ~np.isnan(ry)
    if mask_r.sum() > 1:
        r_series = ScatterSeries()
        r_series.data = [[float(x), float(y)] for x, y in zip(rx[mask_r], ry[mask_r], strict=True)]
        r_series.marker = {"enabled": False}
        r_series.line_width = 1.5
        r_series.color = GRID_MED
        r_series.dash_style = "Dot"
        r_series.enable_mouse_tracking = False
        r_series.show_in_legend = False
        chart.add_series(r_series)

# Reactance arcs (constant X — Smith chart grid)
for x_val in [0.2, 0.5, 1, 2, -0.2, -0.5, -1, -2]:
    xc_center_y = 1.0 / x_val
    xc_radius = abs(1.0 / x_val)
    theta_x = np.linspace(0, 2 * np.pi, 300)
    xa = 1.0 + xc_radius * np.cos(theta_x)
    ya = xc_center_y + xc_radius * np.sin(theta_x)
    inside_x = xa**2 + ya**2 <= 1.001
    xa[~inside_x] = np.nan
    ya[~inside_x] = np.nan
    mask_x = ~np.isnan(xa) & ~np.isnan(ya)
    if mask_x.sum() > 1:
        x_series = ScatterSeries()
        x_series.data = [[float(x), float(y)] for x, y in zip(xa[mask_x], ya[mask_x], strict=True)]
        x_series.marker = {"enabled": False}
        x_series.line_width = 1.5
        x_series.color = GRID_FAINT
        x_series.dash_style = "Dot"
        x_series.enable_mouse_tracking = False
        x_series.show_in_legend = False
        chart.add_series(x_series)

# Horizontal real axis line
h_axis_series = ScatterSeries()
h_axis_series.data = [[-1.0, 0.0], [1.0, 0.0]]
h_axis_series.marker = {"enabled": False}
h_axis_series.line_width = 1.5
h_axis_series.color = GRID_MED
h_axis_series.enable_mouse_tracking = False
h_axis_series.show_in_legend = False
chart.add_series(h_axis_series)

# VSWR circles — Okabe-Ito positions 2, 3, 4
vswr_values = [1.5, 2.0, 3.0]
vswr_colors = ["#D55E00", "#0072B2", "#CC79A7"]
for i, vswr in enumerate(vswr_values):
    gm = (vswr - 1) / (vswr + 1)
    v_theta = np.linspace(0, 2 * np.pi, 200)
    vswr_series = ScatterSeries()
    vswr_series.data = [[float(gm * np.cos(t)), float(gm * np.sin(t))] for t in v_theta]
    vswr_series.name = f"VSWR {vswr:.1f}"
    vswr_series.marker = {"enabled": False}
    vswr_series.line_width = 2.5
    vswr_series.color = vswr_colors[i]
    vswr_series.dash_style = "ShortDash"
    vswr_series.enable_mouse_tracking = False
    vswr_series.show_in_legend = True
    chart.add_series(vswr_series)

# Matched point marker at center (Z = Z₀)
match_series = ScatterSeries()
match_series.data = [[0.0, 0.0]]
match_series.name = "Matched (Z = Z₀)"
match_series.marker = {
    "enabled": True,
    "radius": 16,
    "symbol": "diamond",
    "fillColor": "#E69F00",
    "lineColor": INK,
    "lineWidth": 2,
}
match_series.show_in_legend = True
chart.add_series(match_series)

# Impedance locus — primary data, Okabe-Ito position 1
impedance_series = ScatterSeries()
impedance_series.data = [[float(x), float(y)] for x, y in zip(gamma_x, gamma_y, strict=True)]
impedance_series.name = "Impedance Locus (1–6 GHz)"
impedance_series.marker = {"enabled": True, "radius": 8, "symbol": "circle"}
impedance_series.line_width = 4
impedance_series.color = "#009E73"
impedance_series.show_in_legend = True
chart.add_series(impedance_series)

# Frequency labels at 3 well-spaced points: 1 GHz, ~3.5 GHz, 6 GHz
freq_indices = [0, n_points // 2, n_points - 1]
freq_offsets = [(30, -40), (40, -50), (30, 40)]
freq_annotations = []
for idx, (ox, oy) in zip(freq_indices, freq_offsets, strict=True):
    freq_ghz = frequencies[idx] / 1e9
    freq_annotations.append(
        {
            "point": {"x": float(gamma_x[idx]), "y": float(gamma_y[idx]), "xAxis": 0, "yAxis": 0},
            "text": f"{freq_ghz:.1f} GHz",
            "x": ox,
            "y": oy,
            "style": {"fontSize": "36px", "fontWeight": "bold", "color": INK},
            "backgroundColor": ANNOTATION_BG,
            "borderWidth": 1,
            "borderColor": INK_SOFT,
            "padding": 8,
        }
    )

chart.options.annotations = [{"labels": freq_annotations, "labelOptions": {"shape": "rect"}}]

# Download Highcharts JS inline (CDN cannot load in headless file:// context;
# requires browser-like headers to avoid 403 from code.highcharts.com)
_ua = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.highcharts.com/",
}
_js_assets = {}
for _url in [
    "https://code.highcharts.com/highcharts.js",
    "https://code.highcharts.com/highcharts-more.js",
    "https://code.highcharts.com/modules/annotations.js",
]:
    _req = urllib.request.Request(_url, headers=_ua)
    with urllib.request.urlopen(_req, timeout=30) as _r:
        _js_assets[_url] = _r.read().decode("utf-8")

highcharts_js = _js_assets["https://code.highcharts.com/highcharts.js"]
highcharts_more_js = _js_assets["https://code.highcharts.com/highcharts-more.js"]
annotations_js = _js_assets["https://code.highcharts.com/modules/annotations.js"]

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 2400px; height: 2600px;"></div>
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
chrome_options.add_argument("--window-size=2400,2600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
