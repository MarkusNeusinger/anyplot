""" pyplots.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: highcharts unknown | Python 3.14.3
Quality: 87/100 | Created: 2026-03-07
"""

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


# Data — synthetic HR diagram stellar populations
np.random.seed(42)

# Main sequence: luminosity scales as ~T^3.5 (mass-luminosity relation)
spectral_config = {
    "O": {"temp_range": (28000, 45000), "n": 10, "color": "#6b93d6"},
    "B": {"temp_range": (10000, 28000), "n": 25, "color": "#8db4e6"},
    "A": {"temp_range": (7500, 10000), "n": 30, "color": "#cad7f5"},
    "F": {"temp_range": (6000, 7500), "n": 40, "color": "#f8f7e4"},
    "G": {"temp_range": (5200, 6000), "n": 50, "color": "#fff44f"},
    "K": {"temp_range": (3700, 5200), "n": 45, "color": "#ffb347"},
    "M": {"temp_range": (2400, 3700), "n": 55, "color": "#e8684a"},
}

stars_by_type = {}
for stype, cfg in spectral_config.items():
    lo, hi = cfg["temp_range"]
    temps = np.random.uniform(lo, hi, cfg["n"])
    log_lum = 3.5 * np.log10(temps / 5778) + np.random.normal(0, 0.3, cfg["n"])
    luminosities = 10**log_lum
    stars_by_type[stype] = {"temps": temps, "lums": luminosities, "color": cfg["color"]}

# Red giants — cool but luminous
n_rg = 30
rg_temps = np.random.uniform(3000, 5200, n_rg)
rg_lums = 10 ** np.random.uniform(1.5, 3.5, n_rg)

# Supergiants — very high luminosity across temperature range
n_sg = 12
sg_temps = np.random.uniform(3500, 25000, n_sg)
sg_lums = 10 ** np.random.uniform(3.8, 5.5, n_sg)

# White dwarfs — hot but very dim
n_wd = 25
wd_temps = np.random.uniform(6000, 30000, n_wd)
wd_lums = 10 ** np.random.uniform(-4, -1.5, n_wd)

# Chart setup
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#0d1117",
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "marginTop": 180,
    "marginBottom": 220,
    "marginLeft": 280,
    "marginRight": 120,
}

chart.options.title = {
    "text": "scatter-hr-diagram \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "60px", "fontWeight": "600", "color": "#e6edf3", "letterSpacing": "1px"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Hertzsprung\u2013Russell Diagram \u2014 Stellar Luminosity vs Surface Temperature",
    "style": {"fontSize": "36px", "color": "#8b949e", "fontWeight": "400"},
}

# X-axis — reversed (hot on left, cool on right)
chart.options.x_axis = {
    "title": {
        "text": "Surface Temperature (K)",
        "style": {"fontSize": "40px", "color": "#c9d1d9", "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#8b949e"}},
    "reversed": True,
    "type": "logarithmic",
    "min": 2000,
    "max": 50000,
    "tickPixelInterval": 200,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(139, 148, 158, 0.08)",
    "lineColor": "rgba(139, 148, 158, 0.3)",
    "lineWidth": 1,
    "tickColor": "rgba(139, 148, 158, 0.3)",
}

# Y-axis — logarithmic luminosity
chart.options.y_axis = {
    "title": {
        "text": "Luminosity (L\u2609)",
        "style": {"fontSize": "40px", "color": "#c9d1d9", "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#8b949e"}},
    "type": "logarithmic",
    "min": 0.0001,
    "max": 1000000,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(139, 148, 158, 0.08)",
    "lineColor": "rgba(139, 148, 158, 0.3)",
    "lineWidth": 1,
    "tickColor": "rgba(139, 148, 158, 0.3)",
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -30,
    "y": 100,
    "floating": True,
    "backgroundColor": "rgba(13, 17, 23, 0.85)",
    "borderWidth": 1,
    "borderColor": "rgba(139, 148, 158, 0.3)",
    "borderRadius": 8,
    "itemStyle": {"fontSize": "26px", "fontWeight": "400", "color": "#c9d1d9"},
    "itemHoverStyle": {"color": "#e6edf3"},
    "padding": 16,
    "symbolRadius": 6,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:22px;color:{point.color}">\u25cf</span> '
        '<span style="font-size:24px;color:#e6edf3">'
        "Temp: <b>{point.x:,.0f} K</b><br/>"
        "Luminosity: <b>{point.y:.4f} L\u2609</b></span>"
    ),
    "backgroundColor": "rgba(22, 27, 34, 0.95)",
    "borderColor": "#8b949e",
    "borderRadius": 10,
    "borderWidth": 1,
    "style": {"fontSize": "24px"},
}

# Main sequence series by spectral type
for stype, data in stars_by_type.items():
    series = ScatterSeries()
    series.data = [[float(t), float(lum)] for t, lum in zip(data["temps"], data["lums"], strict=True)]
    series.name = f"Type {stype}"
    series.color = data["color"]
    series.marker = {
        "radius": 8,
        "symbol": "circle",
        "lineWidth": 1,
        "lineColor": "rgba(255, 255, 255, 0.3)",
        "states": {"hover": {"radiusPlus": 3}},
    }
    series.z_index = 2
    chart.add_series(series)

# Red giants
rg_series = ScatterSeries()
rg_series.data = [[float(t), float(lum)] for t, lum in zip(rg_temps, rg_lums, strict=True)]
rg_series.name = "Red Giants"
rg_series.color = "#ff6347"
rg_series.marker = {
    "radius": 12,
    "symbol": "circle",
    "lineWidth": 1,
    "lineColor": "rgba(255, 255, 255, 0.3)",
    "states": {"hover": {"radiusPlus": 4}},
}
rg_series.z_index = 3
chart.add_series(rg_series)

# Supergiants
sg_series = ScatterSeries()
sg_series.data = [[float(t), float(lum)] for t, lum in zip(sg_temps, sg_lums, strict=True)]
sg_series.name = "Supergiants"
sg_series.color = "#ffd700"
sg_series.marker = {
    "radius": 16,
    "symbol": "circle",
    "lineWidth": 2,
    "lineColor": "rgba(255, 215, 0, 0.5)",
    "states": {"hover": {"radiusPlus": 5}},
}
sg_series.z_index = 4
chart.add_series(sg_series)

# White dwarfs
wd_series = ScatterSeries()
wd_series.data = [[float(t), float(lum)] for t, lum in zip(wd_temps, wd_lums, strict=True)]
wd_series.name = "White Dwarfs"
wd_series.color = "#b0c4de"
wd_series.marker = {
    "radius": 6,
    "symbol": "circle",
    "lineWidth": 1,
    "lineColor": "rgba(255, 255, 255, 0.4)",
    "states": {"hover": {"radiusPlus": 3}},
}
wd_series.z_index = 2
chart.add_series(wd_series)

# Sun — distinct reference point
sun_series = ScatterSeries()
sun_series.data = [[5778, 1.0]]
sun_series.name = "Sun \u2609"
sun_series.color = "#ffee58"
sun_series.marker = {
    "radius": 18,
    "symbol": "circle",
    "lineWidth": 3,
    "lineColor": "#ffffff",
    "states": {"hover": {"radiusPlus": 5}},
}
sun_series.z_index = 5
sun_series.data_labels = {
    "enabled": True,
    "format": "Sun \u2609",
    "style": {"fontSize": "32px", "color": "#ffee58", "textOutline": "2px #0d1117", "fontWeight": "600"},
    "x": 25,
    "y": -25,
}
chart.add_series(sun_series)

# Load Highcharts JS (local node_modules first, CDN fallback)
highcharts_paths = [
    Path(__file__).resolve().parents[3] / "node_modules" / "highcharts" / "highcharts.js",
    Path("node_modules/highcharts/highcharts.js"),
]
highcharts_js = None
for p in highcharts_paths:
    if p.exists():
        highcharts_js = p.read_text(encoding="utf-8")
        break
if highcharts_js is None:
    highcharts_url = "https://code.highcharts.com/highcharts.js"
    req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")

# Region labels added via Highcharts renderer after chart renders
region_labels_js = """
setTimeout(function() {
    var chart = Highcharts.charts[0];
    if (!chart) return;
    var r = chart.renderer;
    var xA = chart.xAxis[0];
    var yA = chart.yAxis[0];

    var labels = [
        ['MAIN SEQUENCE', 8000, 8, 'rgba(200,215,245,0.45)', '30px'],
        ['RED GIANTS', 3800, 3000, 'rgba(255,99,71,0.45)', '30px'],
        ['SUPERGIANTS', 12000, 150000, 'rgba(255,215,0,0.45)', '30px'],
        ['WHITE DWARFS', 18000, 0.0005, 'rgba(176,196,222,0.45)', '30px']
    ];

    for (var i = 0; i < labels.length; i++) {
        var l = labels[i];
        var px = xA.toPixels(l[1]);
        var py = yA.toPixels(l[2]);
        r.text(l[0], px, py).css({
            color: l[3],
            fontSize: l[4],
            fontWeight: '600',
            letterSpacing: '3px'
        }).add();
    }
}, 500);
"""

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:#0d1117;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
    <script>{region_labels_js}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
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

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background:#0d1117;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
    <script>{region_labels_js}</script>
</body>
</html>"""
    f.write(interactive_html)
