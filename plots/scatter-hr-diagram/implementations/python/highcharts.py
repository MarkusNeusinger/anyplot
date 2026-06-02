""" anyplot.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Updated: 2026-06-02
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
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Data — synthetic HR diagram stellar populations
np.random.seed(42)

# Main sequence: luminosity scales as ~T^3.5 (mass-luminosity relation)
spectral_config = {
    "O": {"temp_range": (28000, 45000), "n": 10, "color": "#4169e1"},
    "B": {"temp_range": (10000, 28000), "n": 25, "color": "#7ec8e3"},
    "A": {"temp_range": (7500, 10000), "n": 30, "color": "#c8c8ff"},
    "F": {"temp_range": (6000, 7500), "n": 40, "color": "#ffe9a0"},
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
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "marginTop": 160,
    "marginBottom": 240,
    "marginLeft": 260,
    "marginRight": 200,
}

chart.options.title = {
    "text": "scatter-hr-diagram · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "600", "color": INK, "letterSpacing": "0.5px"},
    "margin": 20,
}

chart.options.subtitle = {
    "text": "Hertzsprung–Russell Diagram — Stellar Luminosity vs Surface Temperature",
    "style": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "400"},
}

# Spectral class boundary lines
x_plot_lines = [
    {"value": v, "color": GRID, "width": 2, "dashStyle": "Dash", "zIndex": 1}
    for v in [28000, 10000, 7500, 6000, 5200, 3700]
]

# X-axis — reversed (hot on left, cool on right) per astrophysical convention
chart.options.x_axis = {
    "title": {
        "text": "Surface Temperature (K)",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "reversed": True,
    "type": "logarithmic",
    "min": 2000,
    "max": 50000,
    "tickPixelInterval": 320,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickColor": INK_SOFT,
    "plotLines": x_plot_lines,
}

# Y-axis — logarithmic luminosity
chart.options.y_axis = {
    "title": {
        "text": "Luminosity (L☉)",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "500"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "type": "logarithmic",
    "min": 0.0001,
    "max": 1000000,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickColor": INK_SOFT,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -20,
    "y": 80,
    "floating": True,
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "itemStyle": {"fontSize": "44px", "fontWeight": "400", "color": INK_SOFT},
    "itemHoverStyle": {"color": INK},
    "padding": 16,
    "itemMarginBottom": 4,
    "symbolRadius": 7,
}

chart.options.plot_options = {
    "scatter": {
        "marker": {
            "radius": 8,
            "symbol": "circle",
            "lineWidth": 1,
            "lineColor": "rgba(128,128,128,0.25)",
            "states": {"hover": {"radiusPlus": 3}},
        },
        "opacity": 0.85,
    }
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:20px;color:{point.color}">●</span> '
        '<span style="font-size:22px">'
        "Temp: <b>{point.x:,.0f} K</b><br/>"
        "Luminosity: <b>{point.y:.4f} L☉</b></span>"
    ),
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 10,
    "borderWidth": 1,
    "style": {"fontSize": "22px", "color": INK},
}

# Main sequence series — domain spectral colors per astrophysical convention
for stype, data in stars_by_type.items():
    series = ScatterSeries()
    series.data = [[float(t), float(lum)] for t, lum in zip(data["temps"], data["lums"], strict=True)]
    series.name = f"Type {stype}"
    series.color = data["color"]
    series.z_index = 2
    # Type A (#c8c8ff lavender) is near-invisible on light cream — add visible border
    if stype == "A":
        series.marker = {"lineWidth": 2, "lineColor": INK_SOFT if THEME == "light" else "rgba(128,128,128,0.35)"}
    chart.add_series(series)

# Red giants — larger markers, cool+luminous region
rg_series = ScatterSeries()
rg_series.data = [[float(t), float(lum)] for t, lum in zip(rg_temps, rg_lums, strict=True)]
rg_series.name = "Red Giants"
rg_series.color = "#ff6347"
rg_series.marker = {"radius": 12, "states": {"hover": {"radiusPlus": 4}}}
rg_series.opacity = 0.85
rg_series.z_index = 3
chart.add_series(rg_series)

# Supergiants — largest markers, highest luminosity
sg_series = ScatterSeries()
sg_series.data = [[float(t), float(lum)] for t, lum in zip(sg_temps, sg_lums, strict=True)]
sg_series.name = "Supergiants"
sg_series.color = "#ffd700"
sg_series.marker = {
    "radius": 16,
    "lineWidth": 2,
    "lineColor": "rgba(255,215,0,0.5)",
    "states": {"hover": {"radiusPlus": 5}},
}
sg_series.z_index = 4
chart.add_series(sg_series)

# White dwarfs — small markers, hot+dim region
wd_series = ScatterSeries()
wd_series.data = [[float(t), float(lum)] for t, lum in zip(wd_temps, wd_lums, strict=True)]
wd_series.name = "White Dwarfs"
wd_series.color = "#b0c4de"
wd_series.marker = {"radius": 6, "lineColor": "rgba(128,128,128,0.4)"}
wd_series.z_index = 2
chart.add_series(wd_series)

# Sun — reference point; label shifted toward hotter side to avoid G-type cluster
sun_series = ScatterSeries()
sun_series.data = [[5778, 1.0]]
sun_series.name = "Sun ☉"
sun_series.color = "#ffee58"
sun_series.marker = {
    "radius": 18,
    "symbol": "circle",
    "lineWidth": 3,
    "lineColor": INK,
    "states": {"hover": {"radiusPlus": 5}},
}
sun_series.z_index = 5
sun_series.data_labels = {
    "enabled": True,
    "format": "Sun ☉",
    "style": {"fontSize": "36px", "color": "#ffee58", "textOutline": f"2px {INK_SOFT}", "fontWeight": "600"},
    "x": -80,
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
    req = urllib.request.Request(
        "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js", headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")

# Text shadow for low-contrast spectral letters (A, F) in light mode
spectral_text_shadow = "0 0 4px #1A1A17, -1px -1px 2px rgba(26,26,23,0.6)" if THEME == "light" else "none"

# Region annotation colors — theme-adaptive: darker on light bg, lighter on dark bg
main_seq_color = "rgba(50,90,180,0.65)" if THEME == "light" else "rgba(200,215,245,0.45)"
rg_color = "rgba(200,50,25,0.65)" if THEME == "light" else "rgba(255,99,71,0.45)"
sg_color = "rgba(160,120,0,0.65)" if THEME == "light" else "rgba(255,215,0,0.45)"
wd_color = "rgba(80,110,160,0.65)" if THEME == "light" else "rgba(176,196,222,0.45)"

# Region and spectral class labels via Highcharts renderer API
region_labels_js = f"""
setTimeout(function() {{
    var chart = Highcharts.charts[0];
    if (!chart) return;
    var r = chart.renderer;
    var xA = chart.xAxis[0];
    var yA = chart.yAxis[0];

    var labels = [
        ['MAIN SEQUENCE', 8000, 8, '{main_seq_color}', '40px'],
        ['RED GIANTS', 3800, 3000, '{rg_color}', '40px'],
        ['SUPERGIANTS', 12000, 150000, '{sg_color}', '40px'],
        ['WHITE DWARFS', 18000, 0.0005, '{wd_color}', '40px']
    ];
    for (var i = 0; i < labels.length; i++) {{
        var l = labels[i];
        var px = xA.toPixels(l[1]);
        var py = yA.toPixels(l[2]);
        r.text(l[0], px, py).css({{
            color: l[3],
            fontSize: l[4],
            fontWeight: '600',
            letterSpacing: '3px'
        }}).add();
    }}

    // Spectral class letters along the top of the plot area — domain stellar colors
    var spectralLabels = [
        ['O', 36000, '#4169e1'],
        ['B', 17000, '#7ec8e3'],
        ['A', 8700, '#c8c8ff'],
        ['F', 6750, '#ffe9a0'],
        ['G', 5600, '#fff44f'],
        ['K', 4400, '#ffb347'],
        ['M', 3000, '#e8684a']
    ];
    var topY = chart.plotTop + 40;
    for (var j = 0; j < spectralLabels.length; j++) {{
        var s = spectralLabels[j];
        var sx = xA.toPixels(s[1]);
        r.text(s[0], sx, topY).css({{
            color: s[2],
            fontSize: '44px',
            fontWeight: '700',
            textAnchor: 'middle',
            textShadow: '{spectral_text_shadow}'
        }}).attr({{zIndex: 6}}).add();
    }}
}}, 500);
"""

# Generate HTML with inline scripts (no CDN — headless Chrome can't load external URLs)
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
    <script>{region_labels_js}</script>
</body>
</html>"""

# Save HTML artifact for the site
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and capture screenshot
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
# CDP override is authoritative — --window-size alone loses ~139 px to Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Normalize to exact 3200×1800 as safety net against ±1-2 px rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
