""" pyplots.ai
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
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Electron-positron annihilation (e⁻e⁺ → γ → μ⁻μ⁺)
# Vertices positioned for good canvas utilization
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
    {"start": (0.3, 7.0), "end": v1, "label": "e\u207b", "side": "above", "dir": "forward"},
    {"start": (0.3, 1.0), "end": v1, "label": "e\u207a", "side": "below", "dir": "backward"},
    {"start": v2, "end": (9.7, 7.0), "label": "\u03bc\u207b", "side": "above", "dir": "forward"},
    {"start": v2, "end": (9.7, 1.0), "label": "\u03bc\u207a", "side": "below", "dir": "backward"},
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

    y_off = -55 if fl["side"] == "above" else 55
    label_pt = {
        "x": mx,
        "y": my,
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

    # Fermion line
    series_list.append(
        {
            "type": "line",
            "data": [{"x": sx, "y": sy}, label_pt, {"x": ex, "y": ey}],
            "color": fermion_color,
            "lineWidth": 8,
            "showInLegend": False,
            "enableMouseTracking": False,
            "marker": {"enabled": False},
        }
    )

    # Arrowhead (V shape)
    series_list.append(
        {
            "type": "line",
            "data": [
                {
                    "x": round(mx - sign * arrow_len * ux + arrow_spread * perpx, 4),
                    "y": round(my - sign * arrow_len * uy + arrow_spread * perpy, 4),
                },
                {"x": round(mx, 4), "y": round(my, 4)},
                {
                    "x": round(mx - sign * arrow_len * ux - arrow_spread * perpx, 4),
                    "y": round(my - sign * arrow_len * uy - arrow_spread * perpy, 4),
                },
            ],
            "color": fermion_color,
            "lineWidth": 7,
            "showInLegend": False,
            "enableMouseTracking": False,
            "marker": {"enabled": False},
        }
    )

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
series_list.append(
    {
        "type": "spline",
        "data": photon_data,
        "color": photon_color,
        "lineWidth": 7,
        "showInLegend": False,
        "enableMouseTracking": False,
        "marker": {"enabled": False},
    }
)

# Vertex dots
series_list.append(
    {
        "type": "scatter",
        "data": [{"x": v1[0], "y": v1[1]}, {"x": v2[0], "y": v2[1]}],
        "color": vertex_color,
        "marker": {"radius": 24, "symbol": "circle", "lineWidth": 4, "lineColor": "#ffffff"},
        "showInLegend": False,
        "enableMouseTracking": False,
        "zIndex": 10,
    }
)

# --- Reference line styles at bottom showing gluon and boson ---
ref_y = -0.6
ref_label_style = {"fontSize": "44px", "fontWeight": "600", "textOutline": "2px #ffffff"}

# "Line Styles:" label
series_list.append(
    {
        "type": "scatter",
        "data": [
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
        ],
        "color": "transparent",
        "marker": {"enabled": False},
        "showInLegend": False,
        "enableMouseTracking": False,
    }
)

# Gluon reference line (curly/looped pattern using abs(sin) for bumps)
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
series_list.append(
    {
        "type": "spline",
        "data": gluon_data,
        "color": gluon_color,
        "lineWidth": 6,
        "showInLegend": False,
        "enableMouseTracking": False,
        "marker": {"enabled": False},
    }
)

# Boson reference line (dashed)
boson_x_s, boson_x_e = 6.2, 8.5
boson_mid_x = (boson_x_s + boson_x_e) / 2
series_list.append(
    {
        "type": "line",
        "data": [
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
        ],
        "color": boson_color,
        "lineWidth": 6,
        "dashStyle": "Dash",
        "showInLegend": False,
        "enableMouseTracking": False,
        "marker": {"enabled": False},
    }
)

# Legend entries for all 4 particle types + vertex
legend_entries = [
    {"type": "line", "name": "Fermion (e\u207b, \u03bc\u207b, ...)", "color": fermion_color, "lineWidth": 8},
    {"type": "spline", "name": "Photon (\u03b3)", "color": photon_color, "lineWidth": 7},
    {"type": "spline", "name": "Gluon (g)", "color": gluon_color, "lineWidth": 6},
    {"type": "line", "name": "Scalar Boson (H)", "color": boson_color, "lineWidth": 6, "dashStyle": "Dash"},
]
for entry in legend_entries:
    series_list.append({**entry, "data": [], "showInLegend": True, "marker": {"enabled": False}})
series_list.append(
    {
        "type": "scatter",
        "name": "Interaction Vertex",
        "data": [],
        "color": vertex_color,
        "marker": {"radius": 14, "symbol": "circle"},
        "showInLegend": True,
    }
)

# Build chart using highcharts-core Python API
chart = Chart(container="container")
chart.options = HighchartsOptions.from_dict(
    {
        "chart": {
            "width": 4800,
            "height": 2700,
            "backgroundColor": "#ffffff",
            "marginTop": 200,
            "marginBottom": 200,
            "marginLeft": 120,
            "marginRight": 120,
            "style": {"fontFamily": "'Segoe UI', Arial, Helvetica, sans-serif"},
        },
        "title": {
            "text": "Electron-Positron Annihilation \u00b7 feynman-basic \u00b7 highcharts \u00b7 pyplots.ai",
            "style": {"fontSize": "64px", "fontWeight": "700", "color": "#2c3e50", "letterSpacing": "1px"},
            "margin": 40,
        },
        "subtitle": {
            "text": "e\u207be\u207a \u2192 \u03b3 \u2192 \u03bc\u207b\u03bc\u207a  \u2014  Quantum Electrodynamics (QED) Process",
            "style": {"fontSize": "44px", "fontWeight": "400", "color": "#7f8c8d"},
        },
        "xAxis": {
            "visible": True,
            "min": -0.5,
            "max": 10.5,
            "lineWidth": 0,
            "gridLineWidth": 0,
            "tickWidth": 0,
            "labels": {"enabled": False},
            "title": {
                "text": "Time \u2192",
                "align": "high",
                "offset": 0,
                "x": 40,
                "y": -20,
                "style": {"fontSize": "48px", "fontWeight": "600", "color": "#bdc3c7"},
            },
        },
        "yAxis": {
            "visible": True,
            "min": -1.5,
            "max": 8.0,
            "lineWidth": 0,
            "gridLineWidth": 0,
            "tickWidth": 0,
            "labels": {"enabled": False},
            "title": {"text": None},
        },
        "legend": {
            "enabled": True,
            "layout": "horizontal",
            "align": "center",
            "verticalAlign": "bottom",
            "itemStyle": {"fontSize": "36px", "fontWeight": "500", "color": "#2c3e50"},
            "symbolWidth": 60,
            "symbolHeight": 10,
            "itemDistance": 50,
            "y": -10,
        },
        "tooltip": {"enabled": False},
        "plotOptions": {"series": {"animation": False, "states": {"hover": {"enabled": False}}}},
        "credits": {"enabled": False},
        "series": series_list,
    }
)

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
