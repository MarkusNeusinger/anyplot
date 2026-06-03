""" anyplot.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-03
"""

import math
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.axes.labels import AxisLabelOptions
from highcharts_core.options.axes.title import AxisTitle, YAxisTitle
from highcharts_core.options.axes.x_axis import XAxis
from highcharts_core.options.axes.y_axis import YAxis
from highcharts_core.options.chart import ChartOptions
from highcharts_core.options.credits import Credits
from highcharts_core.options.legend import Legend
from highcharts_core.options.plot_options import PlotOptions
from highcharts_core.options.plot_options.series import SeriesOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
from highcharts_core.options.subtitle import Subtitle
from highcharts_core.options.title import Title
from highcharts_core.options.tooltips import Tooltip
from highcharts_core.utility_classes.markers import Marker
from highcharts_core.utility_classes.states import HoverState, States
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — particle types in canonical order
fermion_color = "#009E73"  # Imprint position 1 (brand green) — fermions
photon_color = "#C475FD"  # Imprint position 2 (lavender)   — photon / EM
gluon_color = "#4467A3"  # Imprint position 3 (blue)        — gluon / strong force
boson_color = "#BD8233"  # Imprint position 4 (ochre)       — scalar boson

# Text outline adapts to theme so outlines work on both warm-cream and near-black surfaces
text_outline = f"3px {PAGE_BG}"

# Data: electron-positron annihilation  e⁻e⁺ → γ → μ⁻μ⁺
v1 = (3.0, 4.0)
v2 = (7.0, 4.0)

fermion_lines = [
    {"start": (0.3, 6.4), "end": v1, "label": "e⁻", "side": "above", "dir": "forward"},
    {"start": (0.3, 1.6), "end": v1, "label": "e⁺", "side": "below", "dir": "backward"},
    {"start": v2, "end": (9.7, 6.4), "label": "μ⁻", "side": "above", "dir": "forward"},
    {"start": v2, "end": (9.7, 1.6), "label": "μ⁺", "side": "below", "dir": "backward"},
]

# Photon propagator (wavy/sinusoidal line between vertices)
n_wave = 200
photon_data = []
for i in range(n_wave + 1):
    t = i / n_wave
    px = v1[0] + (v2[0] - v1[0]) * t
    py = v1[1] + 0.35 * math.sin(2 * math.pi * 7 * t)
    photon_data.append({"x": round(px, 4), "y": round(py, 4), "marker": {"enabled": False}})

series_list = []

# Arrowhead geometry
arrow_len = 0.45
arrow_spread = 0.22

for fl in fermion_lines:
    sx, sy = fl["start"]
    ex, ey = fl["end"]
    mx, my = (sx + ex) / 2, (sy + ey) / 2
    dx, dy = ex - sx, ey - sy
    length = math.sqrt(dx * dx + dy * dy)
    ux, uy = dx / length, dy / length
    perpx, perpy = -uy, ux
    sign = 1.0 if fl["dir"] == "forward" else -1.0

    # Place labels at 35%/65% along the line to avoid arrowhead collision
    label_t = 0.35 if fl["side"] == "above" else 0.65
    lx = sx + (ex - sx) * label_t
    ly = sy + (ey - sy) * label_t
    y_off = -60 if fl["side"] == "above" else 65

    label_pt = {
        "x": round(lx, 4),
        "y": round(ly, 4),
        "marker": {"enabled": False},
        "dataLabels": {
            "enabled": True,
            "format": fl["label"],
            "y": y_off,
            "style": {
                "fontSize": "72px",
                "fontWeight": "bold",
                "color": fermion_color,
                "textOutline": text_outline,
                "fontStyle": "italic",
            },
        },
    }

    fermion_series = LineSeries()
    fermion_series.data = [{"x": sx, "y": sy}, label_pt, {"x": ex, "y": ey}]
    fermion_series.color = fermion_color
    fermion_series.line_width = 8
    fermion_series.show_in_legend = False
    fermion_series.enable_mouse_tracking = False
    fermion_series.marker = Marker(enabled=False)
    series_list.append(fermion_series)

    # V-shaped arrowhead
    arrow_series = LineSeries()
    arrow_series.data = [
        {
            "x": round(mx - sign * arrow_len * ux + arrow_spread * perpx, 4),
            "y": round(my - sign * arrow_len * uy + arrow_spread * perpy, 4),
        },
        {"x": round(mx, 4), "y": round(my, 4)},
        {
            "x": round(mx - sign * arrow_len * ux - arrow_spread * perpx, 4),
            "y": round(my - sign * arrow_len * uy - arrow_spread * perpy, 4),
        },
    ]
    arrow_series.color = fermion_color
    arrow_series.line_width = 7
    arrow_series.show_in_legend = False
    arrow_series.enable_mouse_tracking = False
    arrow_series.marker = Marker(enabled=False)
    series_list.append(arrow_series)

# Photon wavy line with γ label at midpoint
photon_data[n_wave // 2]["dataLabels"] = {
    "enabled": True,
    "format": "γ",
    "y": -70,
    "style": {
        "fontSize": "72px",
        "fontWeight": "bold",
        "color": photon_color,
        "textOutline": text_outline,
        "fontStyle": "italic",
    },
}
photon_series = SplineSeries()
photon_series.data = photon_data
photon_series.color = photon_color
photon_series.line_width = 7
photon_series.show_in_legend = False
photon_series.enable_mouse_tracking = False
photon_series.marker = Marker(enabled=False)
series_list.append(photon_series)

# Interaction vertex dots
vertex_series = ScatterSeries()
vertex_series.data = [{"x": v1[0], "y": v1[1]}, {"x": v2[0], "y": v2[1]}]
vertex_series.color = INK
vertex_series.marker = Marker(radius=24, symbol="circle", line_width=4, line_color=PAGE_BG)
vertex_series.show_in_legend = False
vertex_series.enable_mouse_tracking = False
vertex_series.z_index = 10
series_list.append(vertex_series)

# Reference section: demonstrates gluon (curly) and scalar boson (dashed) line styles
ref_y = 0.5

n_gluon = 200
gluon_x_s, gluon_x_e = 2.3, 4.7
gluon_data = []
for i in range(n_gluon + 1):
    t = i / n_gluon
    gx = gluon_x_s + (gluon_x_e - gluon_x_s) * t
    gy = ref_y + 0.28 * abs(math.sin(2 * math.pi * 5 * t))
    gluon_data.append({"x": round(gx, 4), "y": round(gy, 4), "marker": {"enabled": False}})

gluon_data[n_gluon // 2]["dataLabels"] = {
    "enabled": True,
    "format": "g (gluon)",
    "y": -52,
    "style": {"fontSize": "44px", "fontWeight": "600", "color": gluon_color, "textOutline": text_outline},
}
gluon_series = SplineSeries()
gluon_series.data = gluon_data
gluon_series.color = gluon_color
gluon_series.line_width = 6
gluon_series.show_in_legend = False
gluon_series.enable_mouse_tracking = False
gluon_series.marker = Marker(enabled=False)
series_list.append(gluon_series)

boson_x_s, boson_x_e = 5.5, 7.9
boson_mid_x = (boson_x_s + boson_x_e) / 2
boson_series = LineSeries()
boson_series.data = [
    {"x": boson_x_s, "y": ref_y},
    {
        "x": boson_mid_x,
        "y": ref_y,
        "dataLabels": {
            "enabled": True,
            "format": "H (scalar boson)",
            "y": -52,
            "style": {"fontSize": "44px", "fontWeight": "600", "color": boson_color, "textOutline": text_outline},
        },
    },
    {"x": boson_x_e, "y": ref_y},
]
boson_series.color = boson_color
boson_series.line_width = 6
boson_series.dash_style = "Dash"
boson_series.show_in_legend = False
boson_series.enable_mouse_tracking = False
boson_series.marker = Marker(enabled=False)
series_list.append(boson_series)

# "Line Styles:" section header label
ref_header = ScatterSeries()
ref_header.data = [
    {
        "x": 0.3,
        "y": ref_y,
        "dataLabels": {
            "enabled": True,
            "format": "Line Styles:",
            "align": "left",
            "x": 0,
            "y": 12,
            "style": {"fontSize": "42px", "fontWeight": "700", "color": INK_SOFT, "textOutline": "none"},
        },
    }
]
ref_header.color = "transparent"
ref_header.marker = Marker(enabled=False)
ref_header.show_in_legend = False
ref_header.enable_mouse_tracking = False
series_list.append(ref_header)

# Legend entries for all 4 particle types + vertex
legend_fermion = LineSeries(name="Fermion (e⁻, μ⁻, ...)", color=fermion_color, line_width=8)
legend_fermion.data = []
legend_fermion.show_in_legend = True
legend_fermion.marker = Marker(enabled=False)
series_list.append(legend_fermion)

legend_photon = SplineSeries(name="Photon (γ)", color=photon_color, line_width=7)
legend_photon.data = []
legend_photon.show_in_legend = True
legend_photon.marker = Marker(enabled=False)
series_list.append(legend_photon)

legend_gluon = SplineSeries(name="Gluon (g)", color=gluon_color, line_width=6)
legend_gluon.data = []
legend_gluon.show_in_legend = True
legend_gluon.marker = Marker(enabled=False)
series_list.append(legend_gluon)

legend_boson = LineSeries(name="Scalar Boson (H)", color=boson_color, line_width=6)
legend_boson.dash_style = "Dash"
legend_boson.data = []
legend_boson.show_in_legend = True
legend_boson.marker = Marker(enabled=False)
series_list.append(legend_boson)

legend_vertex = ScatterSeries(name="Interaction Vertex", color=INK)
legend_vertex.data = []
legend_vertex.marker = Marker(radius=14, symbol="circle")
legend_vertex.show_in_legend = True
series_list.append(legend_vertex)

# Build chart
title_text = "Electron-Positron Annihilation · feynman-basic · python · highcharts · anyplot.ai"
title_n = len(title_text)
title_fontsize = max(44, round(66 * 67 / title_n))

chart = Chart(container="container")
options = HighchartsOptions()

options.chart = ChartOptions(
    width=3200,
    height=1800,
    background_color=PAGE_BG,
    margin_top=155,
    margin_bottom=175,
    margin_left=60,
    margin_right=60,
    style={"fontFamily": "'Segoe UI', Arial, Helvetica, sans-serif"},
)

options.title = Title(
    text=title_text, style={"fontSize": f"{title_fontsize}px", "fontWeight": "700", "color": INK}, margin=28
)

options.subtitle = Subtitle(
    text="e⁻e⁺ → γ → μ⁻μ⁺  —  Quantum Electrodynamics (QED) Process",
    style={"fontSize": "44px", "fontWeight": "400", "color": INK_SOFT},
)

options.x_axis = XAxis(
    visible=True,
    min=-0.5,
    max=10.5,
    line_width=0,
    grid_line_width=0,
    tick_width=0,
    labels=AxisLabelOptions(enabled=False),
    title=AxisTitle(
        text="Time →",
        align="high",
        offset=0,
        x=0,
        y=-32,
        style={"fontSize": "48px", "fontWeight": "600", "color": INK_SOFT},
    ),
)

options.y_axis = YAxis(
    visible=True,
    min=-0.5,
    max=7.4,
    line_width=0,
    grid_line_width=0,
    tick_width=0,
    labels=AxisLabelOptions(enabled=False),
    title=YAxisTitle(text=None),
)

options.legend = Legend(
    enabled=True,
    layout="horizontal",
    align="center",
    vertical_align="bottom",
    item_style={"fontSize": "44px", "fontWeight": "500", "color": INK_SOFT},
    background_color=ELEVATED_BG,
    border_color=INK_SOFT,
    border_width=1,
    symbol_width=60,
    symbol_height=10,
    item_distance=50,
    y=-10,
)

options.tooltip = Tooltip(enabled=False)

options.plot_options = PlotOptions(
    series=SeriesOptions(animation=False, states=States(hover=HoverState(enabled=False)))
)

options.credits = Credits(enabled=False)

options.series = series_list
chart.options = options

js_literal = chart.to_js_literal()

# Download Highcharts JS for inline embedding (headless Chrome cannot load CDN from file://)
cdn_urls = ["https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js", "https://code.highcharts.com/highcharts.js"]
highcharts_js = None
for url in cdn_urls:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            highcharts_js = resp.read().decode("utf-8")
        break
    except Exception:
        continue
if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts JS from CDN")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome with exact 3200×1800 viewport
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
# CDP override makes the viewport authoritative (--window-size alone loses ~139 px to Chrome chrome)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Belt-and-braces: pad/crop to exact 3200×1800 so the post-render gate passes
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
