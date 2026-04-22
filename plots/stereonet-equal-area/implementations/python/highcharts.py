""" pyplots.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: highcharts unknown | Python 3.14.3
Quality: 85/100 | Created: 2026-03-15
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import matplotlib
import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from scipy.stats import gaussian_kde


matplotlib.use("Agg")
import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Field measurements from a geological mapping campaign
np.random.seed(42)

strikes_all = []
dips_all = []
types_all = []

# Bedding planes - NE striking, moderate dip (consistent fabric)
n_bed = 40
strikes_all.append(np.random.normal(45, 12, n_bed) % 360)
dips_all.append(np.clip(np.random.normal(35, 8, n_bed), 5, 85))
types_all.extend(["Bedding"] * n_bed)

# Joint set - NW striking, steep dip
n_jnt = 35
strikes_all.append(np.random.normal(315, 15, n_jnt) % 360)
dips_all.append(np.clip(np.random.normal(75, 10, n_jnt), 5, 89))
types_all.extend(["Joints"] * n_jnt)

# Fault planes - roughly N-S striking, steep dip
n_flt = 15
strikes_all.append(np.random.normal(0, 18, n_flt) % 360)
dips_all.append(np.clip(np.random.normal(65, 12, n_flt), 10, 89))
types_all.extend(["Faults"] * n_flt)

strikes = np.concatenate(strikes_all)
dips_arr = np.concatenate(dips_all)

# Equal-area (Schmidt) projection for poles to planes
# Pole: trend = strike + 90 (dip direction), plunge = 90 - dip
pole_trends = (strikes + 90) % 360
pole_plunges = 90 - dips_arr
pole_colat_rad = np.radians(90 - pole_plunges)
pole_r = np.sqrt(2) * np.sin(pole_colat_rad / 2)
pole_x = pole_r * np.sin(np.radians(pole_trends))
pole_y = pole_r * np.cos(np.radians(pole_trends))

# Colorblind-safe palette
feat_colors = {"Bedding": "#306998", "Joints": "#E5863D", "Faults": "#8B5CF6"}

# === Build Highcharts chart using highcharts_core API ===
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#FAFAFA",
    "marginTop": 200,
    "marginBottom": 200,
    "marginLeft": 200,
    "marginRight": 200,
    "spacingBottom": 0,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

chart.options.title = {
    "text": "stereonet-equal-area \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "700", "color": "#1a1a2e"},
    "y": 55,
}

chart.options.subtitle = {
    "text": "Lower Hemisphere Equal-Area (Schmidt) Projection",
    "style": {"fontSize": "38px", "color": "#555", "fontWeight": "400"},
    "y": 110,
}

chart.options.x_axis = {
    "min": -1.35,
    "max": 1.35,
    "gridLineWidth": 0,
    "lineWidth": 0,
    "tickWidth": 0,
    "tickLength": 0,
    "labels": {"enabled": False},
    "title": None,
}

chart.options.y_axis = {
    "min": -1.35,
    "max": 1.35,
    "gridLineWidth": 0,
    "lineWidth": 0,
    "tickWidth": 0,
    "tickLength": 0,
    "minorTickLength": 0,
    "labels": {"enabled": False},
    "title": None,
    "visible": False,
}

chart.options.plot_options = {"series": {"animation": False, "states": {"inactive": {"opacity": 1}}}}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "floating": True,
    "y": -20,
    "itemStyle": {"fontSize": "30px", "fontWeight": "normal", "color": "#333"},
    "itemMarginBottom": 6,
    "symbolHeight": 16,
    "symbolWidth": 28,
    "itemWidth": 440,
    "backgroundColor": "rgba(250,250,250,0.95)",
    "borderColor": "#ccc",
    "borderWidth": 1,
    "borderRadius": 6,
    "padding": 16,
}

chart.options.tooltip = {"enabled": True, "headerFormat": "", "pointFormat": "<b>{series.name}</b>"}

chart.options.credits = {"enabled": False}

# === Build series using highcharts_core API ===
theta_circ = np.linspace(0, 2 * np.pi, 361)

# Primitive circle
circ_data = [[round(float(np.cos(t)), 4), round(float(np.sin(t)), 4)] for t in theta_circ]
primitive = LineSeries()
primitive.data = circ_data
primitive.color = "#1a1a2e"
primitive.line_width = 3
primitive.enable_mouse_tracking = False
primitive.show_in_legend = False
primitive.marker = {"enabled": False}
primitive.z_index = 10
chart.add_series(primitive)

# Grid: concentric circles at 15-degree dip intervals
for dip_val in range(15, 90, 15):
    colat_rad = np.radians(dip_val)
    r_grid = np.sqrt(2) * np.sin(colat_rad / 2)
    grid_data = [[round(float(r_grid * np.cos(t)), 4), round(float(r_grid * np.sin(t)), 4)] for t in theta_circ]
    grid_circle = LineSeries()
    grid_circle.data = grid_data
    grid_circle.color = "rgba(160, 160, 180, 0.25)"
    grid_circle.line_width = 1
    grid_circle.enable_mouse_tracking = False
    grid_circle.show_in_legend = False
    grid_circle.marker = {"enabled": False}
    grid_circle.z_index = 1
    grid_circle.dash_style = "Dot"
    chart.add_series(grid_circle)

# Grid: radial lines every 30 degrees
radial_data = []
for az in range(0, 360, 30):
    az_rad = np.radians(az)
    radial_data.append([0.0, 0.0])
    radial_data.append([round(float(np.sin(az_rad)), 4), round(float(np.cos(az_rad)), 4)])
    radial_data.append(None)
radial_lines = LineSeries()
radial_lines.data = radial_data
radial_lines.color = "rgba(160, 160, 180, 0.25)"
radial_lines.line_width = 1
radial_lines.enable_mouse_tracking = False
radial_lines.show_in_legend = False
radial_lines.marker = {"enabled": False}
radial_lines.z_index = 1
radial_lines.dash_style = "Dot"
chart.add_series(radial_lines)

# Tick marks every 10 degrees around perimeter
tick_data = []
for az in range(0, 360, 10):
    az_rad = np.radians(az)
    r_in = 0.97 if az % 30 != 0 else 0.94
    tick_data.append([round(float(r_in * np.sin(az_rad)), 4), round(float(r_in * np.cos(az_rad)), 4)])
    tick_data.append([round(float(1.0 * np.sin(az_rad)), 4), round(float(1.0 * np.cos(az_rad)), 4)])
    tick_data.append(None)
tick_series = LineSeries()
tick_series.data = tick_data
tick_series.color = "#1a1a2e"
tick_series.line_width = 2
tick_series.enable_mouse_tracking = False
tick_series.show_in_legend = False
tick_series.marker = {"enabled": False}
tick_series.z_index = 10
chart.add_series(tick_series)

# Cardinal and degree labels via annotations
label_map = {
    0: "N",
    30: "30\u00b0",
    60: "60\u00b0",
    90: "E",
    120: "120\u00b0",
    150: "150\u00b0",
    180: "S",
    210: "210\u00b0",
    240: "240\u00b0",
    270: "W",
    300: "300\u00b0",
    330: "330\u00b0",
}
annotation_labels = []
for az, label in label_map.items():
    az_rad = np.radians(az)
    r_label = 1.14
    is_cardinal = label in ("N", "E", "S", "W")
    annotation_labels.append(
        {
            "point": {
                "x": round(float(r_label * np.sin(az_rad)), 4),
                "y": round(float(r_label * np.cos(az_rad)), 4),
                "xAxis": 0,
                "yAxis": 0,
            },
            "text": label,
            "style": {
                "fontSize": "38px" if is_cardinal else "30px",
                "fontWeight": "bold" if is_cardinal else "normal",
                "color": "#1a1a2e",
            },
            "backgroundColor": "transparent",
            "borderWidth": 0,
            "shadow": False,
            "shape": "rect",
            "padding": 4,
        }
    )
chart.options.annotations = [{"labels": annotation_labels, "draggable": ""}]

# === Density contours (Kamb-style) ===
kde_data = np.vstack([pole_x, pole_y])
kde = gaussian_kde(kde_data, bw_method=0.18)

grid_n = 150
gx_lin = np.linspace(-1.1, 1.1, grid_n)
gy_lin = np.linspace(-1.1, 1.1, grid_n)
gx_grid, gy_grid = np.meshgrid(gx_lin, gy_lin)
grid_pts = np.vstack([gx_grid.ravel(), gy_grid.ravel()])
density = kde(grid_pts).reshape(grid_n, grid_n)

# Mask outside unit circle
dist = np.sqrt(gx_grid**2 + gy_grid**2)
density[dist > 0.98] = 0

# Extract contour paths using matplotlib (computation only)
pos_density = density[density > 0]
contour_colors = [
    "rgba(16, 120, 80, 0.12)",
    "rgba(16, 120, 80, 0.22)",
    "rgba(16, 120, 80, 0.35)",
    "rgba(16, 120, 80, 0.50)",
    "rgba(16, 120, 80, 0.65)",
]

if len(pos_density) > 0:
    vmin = np.percentile(pos_density, 30)
    vmax = np.percentile(pos_density, 95)
    levels = np.linspace(vmin, vmax, 5)

    fig_temp, ax_temp = plt.subplots()
    cs = ax_temp.contour(gx_lin, gy_lin, density, levels=levels)

    # Extract contour paths - try newer matplotlib API first
    extracted = False
    try:
        for i, segs in enumerate(cs.allsegs):
            for seg in segs:
                pts = [[round(float(x), 4), round(float(y), 4)] for x, y in seg]
                if len(pts) > 3:
                    contour_line = LineSeries()
                    contour_line.data = pts
                    contour_line.color = contour_colors[min(i, len(contour_colors) - 1)]
                    contour_line.line_width = 2
                    contour_line.enable_mouse_tracking = False
                    contour_line.show_in_legend = False
                    contour_line.marker = {"enabled": False}
                    contour_line.z_index = 2
                    chart.add_series(contour_line)
        extracted = True
    except AttributeError, TypeError:
        pass

    if not extracted:
        try:
            for i, collection in enumerate(cs.collections):
                for path in collection.get_paths():
                    vertices = path.vertices
                    pts = [[round(float(x), 4), round(float(y), 4)] for x, y in vertices]
                    if len(pts) > 3:
                        contour_line = LineSeries()
                        contour_line.data = pts
                        contour_line.color = contour_colors[min(i, len(contour_colors) - 1)]
                        contour_line.line_width = 2
                        contour_line.enable_mouse_tracking = False
                        contour_line.show_in_legend = False
                        contour_line.marker = {"enabled": False}
                        contour_line.z_index = 2
                        chart.add_series(contour_line)
        except AttributeError, TypeError:
            pass

    plt.close(fig_temp)

# === Great circles (representative planes per type) ===
alpha_pts = np.linspace(0, np.pi, 100)

for ftype, n_show in [("Bedding", 5), ("Joints", 4), ("Faults", 3)]:
    mask = np.array(types_all) == ftype
    f_strikes = strikes[mask]
    f_dips = dips_arr[mask]
    indices = np.linspace(0, np.sum(mask) - 1, n_show, dtype=int)

    for idx in indices:
        s_rad = np.radians(f_strikes[idx])
        d_rad = np.radians(f_dips[idx])
        dd_rad = s_rad + np.pi / 2

        vs = np.array([np.sin(s_rad), np.cos(s_rad), 0.0])
        vd = np.array([np.cos(d_rad) * np.sin(dd_rad), np.cos(d_rad) * np.cos(dd_rad), np.sin(d_rad)])

        gc_pts = []
        for a in alpha_pts:
            line = np.cos(a) * vs + np.sin(a) * vd
            if line[2] < 0:
                line = -line
            plunge = np.arcsin(np.clip(line[2], 0, 1))
            trend = np.arctan2(line[0], line[1]) % (2 * np.pi)
            colat = np.pi / 2 - plunge
            r = np.sqrt(2) * np.sin(colat / 2)
            gc_pts.append([round(float(r * np.sin(trend)), 4), round(float(r * np.cos(trend)), 4)])

        gc_series = LineSeries()
        gc_series.data = gc_pts
        gc_series.color = feat_colors[ftype]
        gc_series.line_width = 2.5
        gc_series.opacity = 0.7
        gc_series.enable_mouse_tracking = False
        gc_series.show_in_legend = False
        gc_series.marker = {"enabled": False}
        gc_series.z_index = 3
        chart.add_series(gc_series)

# Legend entries for great circles
for ftype in ["Bedding", "Joints", "Faults"]:
    legend_gc = LineSeries()
    legend_gc.name = f"{ftype} (planes)"
    legend_gc.data = []
    legend_gc.color = feat_colors[ftype]
    legend_gc.line_width = 3
    legend_gc.show_in_legend = True
    legend_gc.marker = {"enabled": False}
    legend_gc.z_index = 0
    chart.add_series(legend_gc)

# Pole scatter series
for ftype in ["Bedding", "Joints", "Faults"]:
    mask = np.array(types_all) == ftype
    px = pole_x[mask]
    py = pole_y[mask]
    pts = [[round(float(x), 4), round(float(y), 4)] for x, y in zip(px, py, strict=True)]
    pole_series = ScatterSeries()
    pole_series.name = f"{ftype} (poles)"
    pole_series.data = pts
    pole_series.color = feat_colors[ftype]
    pole_series.marker = {"radius": 10, "symbol": "circle", "lineWidth": 2, "lineColor": "#ffffff"}
    pole_series.z_index = 5
    chart.add_series(pole_series)

# Density contour legend entry
density_legend = LineSeries()
density_legend.name = "Density contours"
density_legend.data = []
density_legend.color = "rgba(16, 120, 80, 0.55)"
density_legend.line_width = 2
density_legend.show_in_legend = True
density_legend.marker = {"enabled": False}
chart.add_series(density_legend)

# === Render ===
# Download Highcharts JS and annotations module
highcharts_js = ""
js_urls = [
    "https://code.highcharts.com/highcharts.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js",
]
for url in js_urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js += response.read().decode("utf-8") + "\n"
    except Exception:
        # Try CDN fallback for main library
        if "highcharts.js" in url and "modules" not in url:
            try:
                fallback = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
                req = urllib.request.Request(fallback, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as response:
                    highcharts_js += response.read().decode("utf-8") + "\n"
            except Exception:
                pass

# Generate JS literal using highcharts_core API
html_str = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:#FAFAFA;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive HTML
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js"></script>
</head>
<body style="margin:0; background:#FAFAFA;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3800,3800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
