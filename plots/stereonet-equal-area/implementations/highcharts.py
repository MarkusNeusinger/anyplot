""" pyplots.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: highcharts unknown | Python 3.14.3
Quality: 81/100 | Created: 2026-03-15
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import matplotlib
import numpy as np
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

# Feature colors
feat_colors = {"Bedding": "#306998", "Joints": "#E5863D", "Faults": "#D64045"}

# === Build all Highcharts series ===
all_series = []

# --- Stereonet framework: primitive circle ---
theta_circ = np.linspace(0, 2 * np.pi, 361)
circ_data = [[round(float(np.cos(t)), 4), round(float(np.sin(t)), 4)] for t in theta_circ]
all_series.append(
    {
        "type": "line",
        "data": circ_data,
        "color": "#333333",
        "lineWidth": 3,
        "enableMouseTracking": False,
        "showInLegend": False,
        "marker": {"enabled": False},
        "zIndex": 10,
    }
)

# --- Grid: concentric circles at 15-degree dip intervals ---
for dip_val in range(15, 90, 15):
    colat_rad = np.radians(dip_val)
    r_grid = np.sqrt(2) * np.sin(colat_rad / 2)
    grid_data = [[round(float(r_grid * np.cos(t)), 4), round(float(r_grid * np.sin(t)), 4)] for t in theta_circ]
    all_series.append(
        {
            "type": "line",
            "data": grid_data,
            "color": "rgba(180, 180, 180, 0.3)",
            "lineWidth": 1,
            "enableMouseTracking": False,
            "showInLegend": False,
            "marker": {"enabled": False},
            "zIndex": 1,
            "dashStyle": "Dot",
        }
    )

# --- Grid: radial lines every 30 degrees ---
radial_data = []
for az in range(0, 360, 30):
    az_rad = np.radians(az)
    radial_data.append([0.0, 0.0])
    radial_data.append([round(float(np.sin(az_rad)), 4), round(float(np.cos(az_rad)), 4)])
    radial_data.append(None)
all_series.append(
    {
        "type": "line",
        "data": radial_data,
        "color": "rgba(180, 180, 180, 0.3)",
        "lineWidth": 1,
        "enableMouseTracking": False,
        "showInLegend": False,
        "marker": {"enabled": False},
        "zIndex": 1,
        "dashStyle": "Dot",
    }
)

# --- Tick marks every 10 degrees around perimeter ---
tick_data = []
for az in range(0, 360, 10):
    az_rad = np.radians(az)
    r_in = 0.97 if az % 30 != 0 else 0.95
    tick_data.append([round(float(r_in * np.sin(az_rad)), 4), round(float(r_in * np.cos(az_rad)), 4)])
    tick_data.append([round(float(1.0 * np.sin(az_rad)), 4), round(float(1.0 * np.cos(az_rad)), 4)])
    tick_data.append(None)
all_series.append(
    {
        "type": "line",
        "data": tick_data,
        "color": "#333333",
        "lineWidth": 2,
        "enableMouseTracking": False,
        "showInLegend": False,
        "marker": {"enabled": False},
        "zIndex": 10,
    }
)

# --- Cardinal and degree labels around perimeter ---
label_points = []
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
for az, label in label_map.items():
    az_rad = np.radians(az)
    r_label = 1.12
    label_points.append(
        {"x": round(float(r_label * np.sin(az_rad)), 4), "y": round(float(r_label * np.cos(az_rad)), 4), "name": label}
    )
all_series.append(
    {
        "type": "scatter",
        "data": label_points,
        "color": "transparent",
        "marker": {"enabled": False},
        "showInLegend": False,
        "enableMouseTracking": False,
        "dataLabels": {
            "enabled": True,
            "format": "{point.name}",
            "style": {"fontSize": "36px", "fontWeight": "bold", "color": "#333", "textOutline": "none"},
            "align": "center",
            "verticalAlign": "middle",
        },
        "zIndex": 10,
    }
)

# --- Density contours (Kamb-style) on pole data ---
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

# Extract contour paths using matplotlib (computation only, not for display)
pos_density = density[density > 0]
contour_colors = [
    "rgba(34, 139, 34, 0.15)",
    "rgba(34, 139, 34, 0.25)",
    "rgba(34, 139, 34, 0.40)",
    "rgba(34, 139, 34, 0.55)",
    "rgba(34, 139, 34, 0.70)",
]

if len(pos_density) > 0:
    vmin = np.percentile(pos_density, 30)
    vmax = np.percentile(pos_density, 95)
    levels = np.linspace(vmin, vmax, 5)

    fig_temp, ax_temp = plt.subplots()
    cs = ax_temp.contour(gx_lin, gy_lin, density, levels=levels)

    # Extract paths - handle different matplotlib API versions
    extracted = False
    try:
        for i, collection in enumerate(cs.collections):
            for path in collection.get_paths():
                vertices = path.vertices
                pts = [[round(float(x), 4), round(float(y), 4)] for x, y in vertices]
                if len(pts) > 3:
                    all_series.append(
                        {
                            "type": "line",
                            "data": pts,
                            "color": contour_colors[min(i, len(contour_colors) - 1)],
                            "lineWidth": 2,
                            "enableMouseTracking": False,
                            "showInLegend": False,
                            "marker": {"enabled": False},
                            "zIndex": 2,
                        }
                    )
        extracted = True
    except AttributeError, TypeError:
        pass

    if not extracted:
        try:
            for i, segs in enumerate(cs.allsegs):
                for seg in segs:
                    pts = [[round(float(x), 4), round(float(y), 4)] for x, y in seg]
                    if len(pts) > 3:
                        all_series.append(
                            {
                                "type": "line",
                                "data": pts,
                                "color": contour_colors[min(i, len(contour_colors) - 1)],
                                "lineWidth": 2,
                                "enableMouseTracking": False,
                                "showInLegend": False,
                                "marker": {"enabled": False},
                                "zIndex": 2,
                            }
                        )
        except AttributeError, TypeError:
            pass

    plt.close(fig_temp)

# --- Great circles (representative planes per type) ---
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

        # Strike vector (E, N, Down)
        vs = np.array([np.sin(s_rad), np.cos(s_rad), 0.0])
        # Dip vector (down-dip direction)
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

        all_series.append(
            {
                "type": "line",
                "data": gc_pts,
                "color": feat_colors[ftype],
                "lineWidth": 2.5,
                "opacity": 0.7,
                "enableMouseTracking": False,
                "showInLegend": False,
                "marker": {"enabled": False},
                "zIndex": 3,
            }
        )

# --- Legend entries for great circles ---
for ftype in ["Bedding", "Joints", "Faults"]:
    all_series.append(
        {
            "name": f"{ftype} (planes)",
            "type": "line",
            "data": [],
            "color": feat_colors[ftype],
            "lineWidth": 3,
            "showInLegend": True,
            "marker": {"enabled": False},
            "zIndex": 0,
        }
    )

# --- Pole scatter series ---
for ftype in ["Bedding", "Joints", "Faults"]:
    mask = np.array(types_all) == ftype
    px = pole_x[mask]
    py = pole_y[mask]
    pts = [[round(float(x), 4), round(float(y), 4)] for x, y in zip(px, py, strict=True)]
    all_series.append(
        {
            "name": f"{ftype} (poles)",
            "type": "scatter",
            "data": pts,
            "color": feat_colors[ftype],
            "marker": {"radius": 10, "symbol": "circle", "lineWidth": 2, "lineColor": "#ffffff"},
            "zIndex": 5,
        }
    )

# --- Density contour legend entry ---
all_series.append(
    {
        "name": "Density contours",
        "type": "line",
        "data": [],
        "color": "rgba(34, 139, 34, 0.55)",
        "lineWidth": 2,
        "showInLegend": True,
        "marker": {"enabled": False},
    }
)

# Chart configuration
chart_config = {
    "chart": {
        "width": 3600,
        "height": 3600,
        "backgroundColor": "#ffffff",
        "marginTop": 180,
        "marginBottom": 180,
        "marginLeft": 220,
        "marginRight": 220,
    },
    "title": {
        "text": "stereonet-equal-area \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "60px", "fontWeight": "bold"},
        "y": 60,
    },
    "subtitle": {
        "text": "Lower Hemisphere Equal-Area (Schmidt) Projection",
        "style": {"fontSize": "40px", "color": "#666"},
        "y": 115,
    },
    "xAxis": {
        "min": -1.3,
        "max": 1.3,
        "gridLineWidth": 0,
        "lineWidth": 0,
        "tickWidth": 0,
        "labels": {"enabled": False},
        "title": None,
    },
    "yAxis": {
        "min": -1.3,
        "max": 1.3,
        "gridLineWidth": 0,
        "lineWidth": 0,
        "tickWidth": 0,
        "labels": {"enabled": False},
        "title": None,
    },
    "plotOptions": {"series": {"animation": False, "states": {"inactive": {"opacity": 1}}}},
    "legend": {
        "enabled": True,
        "layout": "horizontal",
        "align": "center",
        "verticalAlign": "bottom",
        "itemStyle": {"fontSize": "32px"},
        "symbolHeight": 18,
        "symbolWidth": 28,
        "y": 30,
    },
    "tooltip": {"enabled": True, "headerFormat": "", "pointFormat": "<b>{series.name}</b>"},
    "credits": {"enabled": False},
    "series": all_series,
}

# Render chart
chart_js = json.dumps(chart_config)
chart_script = f"Highcharts.chart('container', {chart_js});"

# Download Highcharts JS (with fallback CDN)
highcharts_js = None
for url in ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue

# HTML for screenshot (inline JS for headless Chrome)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:#ffffff;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{chart_script}</script>
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
</head>
<body style="margin:0; background:#ffffff;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{chart_script}</script>
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
