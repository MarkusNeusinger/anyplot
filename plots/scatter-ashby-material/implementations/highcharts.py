"""pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: highcharts unknown | Python 3.14.3
Quality: 84/100 | Created: 2026-03-11
"""

import json
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


# Data - Density (kg/m³) vs Young's Modulus (GPa) for material families
np.random.seed(42)

families = {
    "Metals & Alloys": {
        "color": "rgba(48, 105, 152, 0.7)",
        "fill": "rgba(48, 105, 152, 0.15)",
        "border": "#1e4f7a",
        "density_range": (2700, 11000),
        "modulus_range": (40, 400),
        "n": 25,
        "label_pos": {"x": 7500, "y": 220},
    },
    "Ceramics & Glasses": {
        "color": "rgba(190, 60, 45, 0.7)",
        "fill": "rgba(190, 60, 45, 0.15)",
        "border": "#a03020",
        "density_range": (2200, 6000),
        "modulus_range": (60, 450),
        "n": 20,
        "label_pos": {"x": 3000, "y": 380},
    },
    "Polymers": {
        "color": "rgba(55, 150, 75, 0.7)",
        "fill": "rgba(55, 150, 75, 0.15)",
        "border": "#2a7a3a",
        "density_range": (900, 1500),
        "modulus_range": (0.2, 4),
        "n": 20,
        "label_pos": {"x": 1250, "y": 0.15},
    },
    "Elastomers": {
        "color": "rgba(200, 155, 40, 0.7)",
        "fill": "rgba(200, 155, 40, 0.15)",
        "border": "#9a7a1a",
        "density_range": (900, 1300),
        "modulus_range": (0.001, 0.1),
        "n": 15,
        "label_pos": {"x": 1150, "y": 0.0006},
    },
    "Composites": {
        "color": "rgba(140, 70, 170, 0.7)",
        "fill": "rgba(140, 70, 170, 0.15)",
        "border": "#6b3480",
        "density_range": (1400, 2200),
        "modulus_range": (15, 200),
        "n": 18,
        "label_pos": {"x": 1550, "y": 220},
    },
    "Foams": {
        "color": "rgba(220, 130, 50, 0.7)",
        "fill": "rgba(220, 130, 50, 0.15)",
        "border": "#b06820",
        "density_range": (25, 300),
        "modulus_range": (0.001, 1),
        "n": 15,
        "label_pos": {"x": 60, "y": 1.5},
    },
    "Natural Materials": {
        "color": "rgba(120, 100, 70, 0.7)",
        "fill": "rgba(120, 100, 70, 0.15)",
        "border": "#6a5430",
        "density_range": (150, 1300),
        "modulus_range": (0.5, 20),
        "n": 15,
        "label_pos": {"x": 350, "y": 25},
    },
}

# Generate realistic log-distributed data for each family
all_series = []
hull_data = []

for family_name, props in families.items():
    n = props["n"]
    log_d_min, log_d_max = np.log10(props["density_range"][0]), np.log10(props["density_range"][1])
    log_m_min, log_m_max = np.log10(props["modulus_range"][0]), np.log10(props["modulus_range"][1])

    log_density = np.random.uniform(log_d_min, log_d_max, n)
    log_modulus = np.random.uniform(log_m_min, log_m_max, n)

    # Add correlation within families
    correlation_noise = np.random.normal(0, 0.15, n)
    log_modulus += 0.3 * (log_density - np.mean(log_density)) + correlation_noise
    log_modulus = np.clip(log_modulus, log_m_min, log_m_max)

    density = 10**log_density
    modulus = 10**log_modulus

    data = [[round(float(d), 2), round(float(m), 4)] for d, m in zip(density, modulus, strict=True)]

    s = ScatterSeries()
    s.name = family_name
    s.data = data
    s.color = props["color"]
    s.marker = {"radius": 14, "symbol": "circle", "lineWidth": 2, "lineColor": props["border"]}
    s.z_index = 3
    all_series.append(s)

    # Convex hull in log space (monotone chain, inlined) with slight expansion
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
    expanded = centroid + 1.12 * (hull_verts - centroid)
    expanded = np.vstack([expanded, expanded[0]])
    hull_polygon = [[round(float(10**x), 4), round(float(10**y), 6)] for x, y in expanded]
    hull_data.append(
        {"name": family_name, "fill": props["fill"], "border_color": props["border"], "data": hull_polygon}
    )

# Create chart using highcharts_core
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#f8f9fb",
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "marginTop": 160,
    "marginBottom": 200,
    "marginLeft": 260,
    "marginRight": 200,
    "plotBackgroundColor": "#ffffff",
    "plotBorderWidth": 1,
    "plotBorderColor": "#d0d5dd",
}

chart.options.title = {
    "text": "Density vs. Young\u2019s Modulus \u00b7 scatter-ashby-material \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "52px", "fontWeight": "700", "color": "#1a2332"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Ashby material selection chart \u2014 7 material families across engineering property space",
    "style": {"fontSize": "34px", "color": "#6b7280", "fontWeight": "400"},
}

chart.options.x_axis = {
    "type": "logarithmic",
    "title": {
        "text": "Density (kg/m\u00b3)",
        "style": {"fontSize": "40px", "color": "#2d3748", "fontWeight": "600"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "30px", "color": "#6b7280"}},
    "min": 10,
    "max": 20000,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.05)",
    "gridLineDashStyle": "Dash",
    "lineWidth": 0,
    "tickWidth": 0,
}

chart.options.y_axis = {
    "type": "logarithmic",
    "title": {
        "text": "Young\u2019s Modulus (GPa)",
        "style": {"fontSize": "40px", "color": "#2d3748", "fontWeight": "600"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "30px", "color": "#6b7280"}},
    "min": 0.0005,
    "max": 1000,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.05)",
    "gridLineDashStyle": "Dash",
    "lineWidth": 0,
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
    "backgroundColor": "rgba(255, 255, 255, 0.92)",
    "borderWidth": 1,
    "borderColor": "#d0d5dd",
    "borderRadius": 10,
    "itemStyle": {"fontSize": "28px", "fontWeight": "500", "color": "#2d3748"},
    "padding": 16,
    "itemMarginBottom": 6,
    "symbolRadius": 6,
    "shadow": {"color": "rgba(0,0,0,0.06)", "offsetX": 1, "offsetY": 2, "width": 4},
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": '<span style="font-size:26px;font-weight:bold;color:{series.color}">{series.name}</span><br/>',
    "pointFormat": '<span style="font-size:22px">'
    "Density: <b>{point.x:.1f} kg/m\u00b3</b><br/>"
    "Modulus: <b>{point.y:.4f} GPa</b></span>",
    "backgroundColor": "rgba(255, 255, 255, 0.96)",
    "borderColor": "#d0d5dd",
    "borderRadius": 8,
    "shadow": {"color": "rgba(0, 0, 0, 0.08)", "offsetX": 1, "offsetY": 2, "width": 4},
}

chart.options.plot_options = {"scatter": {"marker": {"radius": 14}, "states": {"hover": {"marker": {"radiusPlus": 5}}}}}

# Build annotation labels for family names
label_annotations = []
for family_name, props in families.items():
    label_annotations.append(
        {
            "point": {"x": props["label_pos"]["x"], "y": props["label_pos"]["y"], "xAxis": 0, "yAxis": 0},
            "text": family_name,
            "style": {"fontSize": "30px", "fontWeight": "bold", "color": props["border"]},
            "backgroundColor": "rgba(255, 255, 255, 0.80)",
            "borderWidth": 0,
            "borderRadius": 4,
            "padding": 6,
            "shadow": False,
        }
    )

chart.options.annotations = [
    {"labels": label_annotations, "labelOptions": {"shape": "rect", "overflow": "none", "crop": False}, "draggable": ""}
]

for s in all_series:
    chart.add_series(s)

# Get the JS literal from highcharts_core (uses DOMContentLoaded wrapper)
base_js = chart.to_js_literal()

# Prepare hull and guide line drawing via Highcharts renderer API
hull_data_json = json.dumps(hull_data)

renderer_callback = (
    """
function drawOverlays(chart) {
    var xAxis = chart.xAxis[0];
    var yAxis = chart.yAxis[0];
    var hullData = """
    + hull_data_json
    + """;

    // Draw convex hull envelopes
    hullData.forEach(function(hull) {
        var pathArr = [];
        hull.data.forEach(function(pt, i) {
            var px = xAxis.toPixels(pt[0]);
            var py = yAxis.toPixels(pt[1]);
            if (i === 0) {
                pathArr.push('M', px, py);
            } else {
                pathArr.push('L', px, py);
            }
        });
        pathArr.push('Z');
        chart.renderer.path(pathArr)
            .attr({
                fill: hull.fill,
                stroke: hull.border_color,
                'stroke-width': 2.5,
                'stroke-dasharray': '8,5',
                zIndex: 1
            })
            .add();
    });

    // Performance index guide lines: E/rho = const (lightweight stiffness)
    var guideConfigs = [
        {val: 0.01, label: 'E/\\u03C1 = 0.01'},
        {val: 1, label: 'E/\\u03C1 = 1'},
        {val: 100, label: 'E/\\u03C1 = 100'}
    ];
    guideConfigs.forEach(function(g) {
        var pathArr = [];
        var labelX = 0, labelY = 0;
        var firstPt = true;
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
                firstPt = false;
            } else {
                pathArr.push('L', px, py);
            }
            labelX = px;
            labelY = py;
        }
        if (pathArr.length > 3) {
            chart.renderer.path(pathArr)
                .attr({
                    stroke: 'rgba(100, 110, 140, 0.5)',
                    'stroke-width': 3,
                    'stroke-dasharray': '14,8',
                    zIndex: 0
                })
                .add();
            chart.renderer.text(g.label, labelX + 10, labelY - 10)
                .css({
                    color: 'rgba(80, 90, 120, 0.75)',
                    fontSize: '26px',
                    fontStyle: 'italic',
                    fontWeight: '500'
                })
                .attr({ zIndex: 0 })
                .add();
        }
    });
}
"""
)

# Post-render script that finds the chart and draws overlays
post_render_js = """
setTimeout(function() {
    var chart = Highcharts.charts[Highcharts.charts.length - 1];
    if (chart) { drawOverlays(chart); }
}, 100);
"""

# Download Highcharts JS and annotations module
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
annotations_url = "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:#f8f9fb;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    {renderer_callback}
    {base_js}
    {post_render_js}
    </script>
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
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js"></script>
</head>
<body style="margin:0; background:#f8f9fb;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
    {renderer_callback}
    {base_js}
    {post_render_js}
    </script>
</body>
</html>"""
    f.write(interactive_html)
