"""pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: highcharts unknown | Python 3.14.3
Quality: 87/100 | Created: 2026-03-07
"""

import math
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


# Data: Electron-positron annihilation (e⁻e⁺ → γ → μ⁻μ⁺)
v1 = (3.0, 4.0)
v2 = (7.0, 4.0)

# Colors
fermion_color = "#306998"
photon_color = "#D63384"
gluon_color = "#2E8B57"
boson_color = "#E67E22"
vertex_color = "#2c3e50"

# Fermion propagators with arrow direction convention
fermion_lines = [
    {"start": (0.3, 6.8), "end": v1, "label": "e\u207b", "side": "above", "dir": "forward"},
    {"start": (0.3, 1.2), "end": v1, "label": "e\u207a", "side": "below", "dir": "backward"},
    {"start": v2, "end": (9.7, 6.8), "label": "\u03bc\u207b", "side": "above", "dir": "forward"},
    {"start": v2, "end": (9.7, 1.2), "label": "\u03bc\u207a", "side": "below", "dir": "backward"},
]

# Photon propagator (wavy line between vertices)
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

    # Offset labels away from arrowheads to avoid overlap
    # Place labels at 35% or 65% along the line instead of midpoint
    label_t = 0.35 if fl["side"] == "above" else 0.65
    lx, ly = sx + (ex - sx) * label_t, sy + (ey - sy) * label_t
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
                "textOutline": "4px #ffffff",
                "fontStyle": "italic",
            },
        },
    }

    # Fermion line series
    fermion_series = LineSeries()
    fermion_series.data = [{"x": sx, "y": sy}, label_pt, {"x": ex, "y": ey}]
    fermion_series.color = fermion_color
    fermion_series.line_width = 8
    fermion_series.show_in_legend = False
    fermion_series.enable_mouse_tracking = False
    fermion_series.marker = Marker(enabled=False)
    series_list.append(fermion_series)

    # Arrowhead (V shape) series
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

# Photon wavy line with label at midpoint
photon_data[n_wave // 2]["dataLabels"] = {
    "enabled": True,
    "format": "\u03b3",
    "y": -70,
    "style": {
        "fontSize": "72px",
        "fontWeight": "bold",
        "color": photon_color,
        "textOutline": "4px #ffffff",
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

# Vertex dots
vertex_series = ScatterSeries()
vertex_series.data = [{"x": v1[0], "y": v1[1]}, {"x": v2[0], "y": v2[1]}]
vertex_series.color = vertex_color
vertex_series.marker = Marker(radius=24, symbol="circle", line_width=4, line_color="#ffffff")
vertex_series.show_in_legend = False
vertex_series.enable_mouse_tracking = False
vertex_series.z_index = 10
series_list.append(vertex_series)

# --- Reference line styles showing gluon and boson (moved closer to diagram) ---
ref_y = 0.2

ref_label_style = {"fontSize": "44px", "fontWeight": "600", "textOutline": "2px #ffffff"}

# "Line Styles:" label
ref_title_series = ScatterSeries()
ref_title_series.data = [
    {
        "x": 0.2,
        "y": ref_y,
        "dataLabels": {
            "enabled": True,
            "format": "Line Styles:",
            "align": "left",
            "x": 0,
            "y": 10,
            "style": {"fontSize": "40px", "fontWeight": "700", "color": "#2c3e50", "textOutline": "none"},
        },
    }
]
ref_title_series.color = "transparent"
ref_title_series.marker = Marker(enabled=False)
ref_title_series.show_in_legend = False
ref_title_series.enable_mouse_tracking = False
series_list.append(ref_title_series)

# Gluon reference line (curly/looped pattern)
n_gluon = 200
gluon_x_s, gluon_x_e = 2.5, 4.8
gluon_data = []
for i in range(n_gluon + 1):
    t = i / n_gluon
    gx = gluon_x_s + (gluon_x_e - gluon_x_s) * t
    gy = ref_y + 0.28 * abs(math.sin(2 * math.pi * 5 * t))
    gluon_data.append({"x": round(gx, 4), "y": round(gy, 4), "marker": {"enabled": False}})

gluon_data[n_gluon // 2]["dataLabels"] = {
    "enabled": True,
    "format": "g (gluon)",
    "y": -50,
    "style": {**ref_label_style, "color": gluon_color},
}
gluon_series = SplineSeries()
gluon_series.data = gluon_data
gluon_series.color = gluon_color
gluon_series.line_width = 6
gluon_series.show_in_legend = False
gluon_series.enable_mouse_tracking = False
gluon_series.marker = Marker(enabled=False)
series_list.append(gluon_series)

# Boson reference line (dashed)
boson_x_s, boson_x_e = 6.2, 8.5
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
            "y": -50,
            "style": {**ref_label_style, "color": boson_color},
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

# Legend entries for all 4 particle types + vertex
legend_fermion = LineSeries(name="Fermion (e\u207b, \u03bc\u207b, ...)", color=fermion_color, line_width=8)
legend_fermion.data = []
legend_fermion.show_in_legend = True
legend_fermion.marker = Marker(enabled=False)
series_list.append(legend_fermion)

legend_photon = SplineSeries(name="Photon (\u03b3)", color=photon_color, line_width=7)
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

legend_vertex = ScatterSeries(name="Interaction Vertex", color=vertex_color)
legend_vertex.data = []
legend_vertex.marker = Marker(radius=14, symbol="circle")
legend_vertex.show_in_legend = True
series_list.append(legend_vertex)

# Build chart using highcharts-core Python class hierarchy
chart = Chart(container="container")

options = HighchartsOptions()

options.chart = ChartOptions(
    width=4800,
    height=2700,
    background_color="#ffffff",
    margin_top=200,
    margin_bottom=200,
    margin_left=120,
    margin_right=120,
    style={"fontFamily": "'Segoe UI', Arial, Helvetica, sans-serif"},
)

options.title = Title(
    text="Electron-Positron Annihilation \u00b7 feynman-basic \u00b7 highcharts \u00b7 pyplots.ai",
    style={"fontSize": "64px", "fontWeight": "700", "color": "#2c3e50", "letterSpacing": "1px"},
    margin=40,
)

options.subtitle = Subtitle(
    text="e\u207be\u207a \u2192 \u03b3 \u2192 \u03bc\u207b\u03bc\u207a  \u2014  Quantum Electrodynamics (QED) Process",
    style={"fontSize": "44px", "fontWeight": "400", "color": "#7f8c8d"},
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
        text="Time \u2192",
        align="high",
        offset=0,
        x=40,
        y=-20,
        style={"fontSize": "48px", "fontWeight": "600", "color": "#bdc3c7"},
    ),
)

options.y_axis = YAxis(
    visible=True,
    min=-0.8,
    max=8.0,
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
    item_style={"fontSize": "36px", "fontWeight": "500", "color": "#2c3e50"},
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

# Generate JS using highcharts-core
js_literal = chart.to_js_literal()

# Download Highcharts JS for headless rendering
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
    raise RuntimeError("Failed to download Highcharts JS")

# HTML for screenshot with inline JS
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Standalone HTML for interactive viewing
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
</head>
<body style="margin:0; overflow:auto;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Screenshot via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
