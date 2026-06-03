"""anyplot.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: highcharts | Python 3.14
Quality: 85/100 | Updated: 2026-06-03
"""

import json
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


# Theme tokens — Imprint palette
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint categorical palette — 7 of 8 hues, canonical order
IMPRINT_COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Hull fill: Imprint hex → rgba with alpha
_fa = 0.18 if THEME == "light" else 0.28
IMPRINT_FILLS = [f"rgba({int(c[1:3], 16)},{int(c[3:5], 16)},{int(c[5:7], 16)},{_fa})" for c in IMPRINT_COLORS]

# Data — Density (kg/m³) vs Young's Modulus (GPa) for 7 material families
np.random.seed(42)

family_specs = [
    ("Metals & Alloys", (2700, 11000), (40, 400), 25, {"x": 7500, "y": 220}),
    ("Ceramics & Glasses", (2200, 6000), (60, 450), 20, {"x": 3000, "y": 380}),
    ("Polymers", (900, 1500), (0.2, 4), 20, {"x": 1250, "y": 0.15}),
    ("Elastomers", (900, 1300), (0.001, 0.1), 15, {"x": 1150, "y": 0.0006}),
    ("Composites", (1400, 2200), (15, 200), 18, {"x": 1550, "y": 220}),
    ("Foams", (30, 200), (0.001, 0.5), 15, {"x": 60, "y": 0.7}),
    ("Natural Materials", (150, 1300), (0.5, 20), 15, {"x": 350, "y": 25}),
]

all_series = []
hull_data = []

for i, (family_name, density_range, modulus_range, n, label_pos) in enumerate(family_specs):
    color = IMPRINT_COLORS[i]
    fill = IMPRINT_FILLS[i]

    log_d_min, log_d_max = np.log10(density_range[0]), np.log10(density_range[1])
    log_m_min, log_m_max = np.log10(modulus_range[0]), np.log10(modulus_range[1])

    log_density = np.random.uniform(log_d_min, log_d_max, n)
    log_modulus = np.random.uniform(log_m_min, log_m_max, n)
    correlation_noise = np.random.normal(0, 0.15, n)
    log_modulus += 0.3 * (log_density - np.mean(log_density)) + correlation_noise
    log_modulus = np.clip(log_modulus, log_m_min, log_m_max)

    density = 10**log_density
    modulus = 10**log_modulus
    data = [[round(float(d), 2), round(float(m), 4)] for d, m in zip(density, modulus, strict=True)]

    s = ScatterSeries()
    s.name = family_name
    s.data = data
    s.color = color
    s.marker = {"radius": 8, "symbol": "circle", "lineWidth": 1.5, "lineColor": PAGE_BG}
    s.z_index = 3
    all_series.append(s)

    # Convex hull (monotone chain in log space) with reduced expansion to limit overlap
    log_pts = np.column_stack([log_density, log_modulus])
    pts_sorted = log_pts[np.lexsort((log_pts[:, 1], log_pts[:, 0]))]
    lower, upper = [], []
    for p in pts_sorted:
        while len(lower) >= 2:
            o, a = lower[-2], lower[-1]
            if (a[0] - o[0]) * (p[1] - o[1]) - (a[1] - o[1]) * (p[0] - o[0]) <= 0:
                lower.pop()
            else:
                break
        lower.append(p)
    for p in reversed(pts_sorted):
        while len(upper) >= 2:
            o, a = upper[-2], upper[-1]
            if (a[0] - o[0]) * (p[1] - o[1]) - (a[1] - o[1]) * (p[0] - o[0]) <= 0:
                upper.pop()
            else:
                break
        upper.append(p)
    hull_verts = np.array(lower[:-1] + upper[:-1])
    centroid = hull_verts.mean(axis=0)
    expanded = centroid + 1.03 * (hull_verts - centroid)
    expanded = np.vstack([expanded, expanded[0]])
    hull_polygon = [[round(float(10**x), 4), round(float(10**y), 6)] for x, y in expanded]
    hull_data.append(
        {"name": family_name, "fill": fill, "border_color": color, "label_pos": label_pos, "data": hull_polygon}
    )

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif", "color": INK},
    "marginTop": 110,
    "marginBottom": 180,
    "marginLeft": 190,
    "marginRight": 230,
}

chart.options.title = {
    "text": "scatter-ashby-material · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "700", "color": INK},
    "margin": 16,
}

chart.options.subtitle = {
    "text": "Ashby chart — 7 material families across the engineering property space",
    "style": {"fontSize": "36px", "color": INK_SOFT, "fontWeight": "400"},
    "margin": 16,
}

chart.options.x_axis = {
    "type": "logarithmic",
    "title": {
        "text": "Density (kg/m³)",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "600"},
        "margin": 12,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 10,
    "max": 20000,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickWidth": 0,
}

chart.options.y_axis = {
    "type": "logarithmic",
    "title": {
        "text": "Young’s Modulus (GPa)",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "600"},
        "margin": 12,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 0.0005,
    "max": 1000,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickWidth": 0,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "x": -10,
    "y": 0,
    "floating": False,
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "itemStyle": {"fontSize": "44px", "fontWeight": "500", "color": INK_SOFT},
    "padding": 14,
    "itemMarginBottom": 6,
    "symbolRadius": 6,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": '<span style="font-size:28px;font-weight:bold;color:{series.color}">{series.name}</span><br/>',
    "pointFormat": (
        '<span style="font-size:24px">Density: <b>{point.x:.1f} kg/m³</b><br/>Modulus: <b>{point.y:.4f} GPa</b></span>'
    ),
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 6,
    "style": {"color": INK},
}

chart.options.plot_options = {"scatter": {"marker": {"radius": 8}, "states": {"hover": {"marker": {"radiusPlus": 4}}}}}

for s in all_series:
    chart.add_series(s)

# Get JS literal from highcharts_core
base_js = chart.to_js_literal()

# Build data vars JS block — theme tokens + hull data (no f-string in callback)
hull_data_json = json.dumps(hull_data)
data_vars_js = (
    "var ANYPLOT_HULL_DATA = "
    + hull_data_json
    + ";\n"
    + "var ANYPLOT_INK_SOFT = '"
    + INK_SOFT
    + "';\n"
    + "var ANYPLOT_ELEVATED_BG = '"
    + ELEVATED_BG
    + "';\n"
    + "var ANYPLOT_INK_MUTED = '"
    + INK_MUTED
    + "';\n"
)

# Static renderer callback — uses ANYPLOT_* globals set above
renderer_callback = """
function drawOverlays(chart) {
    var xAxis = chart.xAxis[0];
    var yAxis = chart.yAxis[0];
    var hullData = ANYPLOT_HULL_DATA;

    // Draw convex hull envelopes
    hullData.forEach(function(hull) {
        var pathArr = [];
        hull.data.forEach(function(pt, i) {
            var px = xAxis.toPixels(pt[0]);
            var py = yAxis.toPixels(pt[1]);
            pathArr.push(i === 0 ? 'M' : 'L', px, py);
        });
        pathArr.push('Z');
        chart.renderer.path(pathArr)
            .attr({
                fill: hull.fill,
                stroke: hull.border_color,
                'stroke-width': 2,
                'stroke-dasharray': '8,5',
                zIndex: 1
            })
            .add();
    });

    // Family name labels
    hullData.forEach(function(hull) {
        var px = xAxis.toPixels(hull.label_pos.x);
        var py = yAxis.toPixels(hull.label_pos.y);
        if (px < chart.plotLeft || px > chart.plotLeft + chart.plotWidth) return;
        if (py < chart.plotTop || py > chart.plotTop + chart.plotHeight) return;
        chart.renderer.label(hull.name, px - 10, py - 20)
            .css({ color: hull.border_color, fontSize: '30px', fontWeight: '700' })
            .attr({
                fill: ANYPLOT_ELEVATED_BG,
                stroke: hull.border_color,
                'stroke-width': 1,
                r: 4,
                padding: 5,
                zIndex: 5
            })
            .add();
    });

    // Performance index guide lines: E/rho = const (lightweight stiffness)
    var guideConfigs = [
        {val: 0.01, label: 'E/ρ = 0.01'},
        {val: 1,    label: 'E/ρ = 1'},
        {val: 100,  label: 'E/ρ = 100'}
    ];
    guideConfigs.forEach(function(g) {
        var pathArr = [];
        var firstVisX = 0, firstVisY = 0, firstPt = true;
        for (var logD = 1.0; logD <= 4.4; logD += 0.05) {
            var d = Math.pow(10, logD);
            var e = g.val * d / 1000;
            if (e < 0.0005 || e > 1000) continue;
            var px = xAxis.toPixels(d);
            var py = yAxis.toPixels(e);
            if (px < chart.plotLeft || px > chart.plotLeft + chart.plotWidth) continue;
            if (py < chart.plotTop || py > chart.plotTop + chart.plotHeight) continue;
            if (firstPt) {
                pathArr.push('M', px, py);
                firstVisX = px; firstVisY = py; firstPt = false;
            } else {
                pathArr.push('L', px, py);
            }
        }
        if (pathArr.length > 3) {
            chart.renderer.path(pathArr)
                .attr({
                    stroke: ANYPLOT_INK_MUTED,
                    'stroke-width': 2,
                    'stroke-dasharray': '12,7',
                    zIndex: 0
                })
                .add();
            chart.renderer.text(g.label, firstVisX + 8, firstVisY - 10)
                .css({ color: ANYPLOT_INK_MUTED, fontSize: '28px', fontStyle: 'italic' })
                .attr({ zIndex: 0 })
                .add();
        }
    });
}
"""

post_render_js = """
setTimeout(function() {
    var chart = Highcharts.charts[Highcharts.charts.length - 1];
    if (chart) { drawOverlays(chart); }
}, 300);
"""

# Download Highcharts JS inline (required for headless Chrome file:// URLs)
with urllib.request.urlopen("https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js", timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build HTML with inline scripts
html_parts = [
    "<!DOCTYPE html>\n<html>\n<head>\n",
    '    <meta charset="utf-8">\n',
    "    <script>",
    highcharts_js,
    "</script>\n",
    "</head>\n",
    '<body style="margin:0; background:',
    PAGE_BG,
    ';">\n',
    '    <div id="container" style="width: 3200px; height: 1800px;"></div>\n',
    "    <script>\n",
    data_vars_js,
    "    </script>\n",
    "    <script>\n",
    renderer_callback,
    "\n    </script>\n",
    "    <script>\n",
    base_js,
    "\n    </script>\n",
    "    <script>\n",
    post_render_js,
    "\n    </script>\n",
    "</body>\n</html>",
]
html_content = "".join(html_parts)

# Save HTML artifact (both themes)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome — CDP override is authoritative for exact viewport
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

# Normalize to exact canvas dims (safety net for CDP rounding)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
