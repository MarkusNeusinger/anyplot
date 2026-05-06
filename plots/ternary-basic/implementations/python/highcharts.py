""" anyplot.ai
ternary-basic: Basic Ternary Plot
Library: highcharts unknown | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-06
"""

import math
import os
import tempfile
import time
from pathlib import Path

import numpy as np
import requests
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data - Soil composition samples (sand, silt, clay percentages)
np.random.seed(42)
n_points = 50

# Generate random ternary compositions that sum to 100
raw = np.random.dirichlet([2, 2, 2], n_points) * 100
sand = raw[:, 0]
silt = raw[:, 1]
clay = raw[:, 2]

# Convert ternary coordinates to Cartesian for equilateral triangle
tri_height = math.sqrt(3) / 2
cart_x = []
cart_y = []
for s, si, cl in zip(sand, silt, clay, strict=True):
    total = s + si + cl
    a_norm = s / total
    b_norm = si / total
    c_norm = cl / total
    x = 0.5 * (2 * b_norm + c_norm)
    y = tri_height * a_norm
    cart_x.append(x)
    cart_y.append(y)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginTop": 200,
    "marginBottom": 250,
    "marginLeft": 400,
    "marginRight": 400,
}

# Title
chart.options.title = {"text": "ternary-basic · highcharts · anyplot.ai", "style": {"fontSize": "28px", "color": INK}}

# Axes - hide them since we're drawing our own triangle grid
chart.options.x_axis = {"min": -0.15, "max": 1.15, "visible": False, "gridLineWidth": 0}
chart.options.y_axis = {"min": -0.15, "max": 1.05, "visible": False, "gridLineWidth": 0}

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"color": INK_SOFT}}

# Credits
chart.options.credits = {"enabled": False}

# Tooltip showing ternary values
chart.options.tooltip = {
    "enabled": True,
    "headerFormat": "",
    "pointFormat": "<b>Sand:</b> {point.sand:.1f}%<br><b>Silt:</b> {point.silt:.1f}%<br><b>Clay:</b> {point.clay:.1f}%",
    "style": {"fontSize": "18px"},
}

# Create scatter series with Okabe-Ito brand color
series = ScatterSeries()
series.data = [
    {"x": float(x), "y": float(y), "sand": float(s), "silt": float(si), "clay": float(cl)}
    for x, y, s, si, cl in zip(cart_x, cart_y, sand, silt, clay, strict=True)
]
series.name = "Soil Samples"
series.color = BRAND
series.marker = {"radius": 8}

chart.add_series(series)

# Download Highcharts JS with retry (try multiple CDNs)
urls = ["https://cdn.jsdelivr.net/npm/highcharts@11.0.0/highcharts.js", "https://code.highcharts.com/highcharts.js"]
highcharts_js = None
for url in urls:
    for attempt in range(2):
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=30,
                allow_redirects=True,
            )
            response.raise_for_status()
            highcharts_js = response.text
            break
        except Exception as e:
            if attempt > 0 or url != urls[-1]:
                continue
            raise e
    if highcharts_js:
        break

if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts JS")

# Custom JavaScript to draw triangle grid and labels after chart renders
custom_js = f"""
(function() {{
    var chart = Highcharts.charts[Highcharts.charts.length - 1];
    var renderer = chart.renderer;

    var triHeight = {tri_height};
    var ink = "{INK}";
    var inkSoft = "{INK_SOFT}";
    var gridColor = "{GRID}";

    // Convert normalized coords to pixels
    function toPixel(nx, ny) {{
        return [chart.xAxis[0].toPixels(nx), chart.yAxis[0].toPixels(ny)];
    }}

    // Triangle vertices
    var A = toPixel(0.5, triHeight);
    var B = toPixel(0, 0);
    var C = toPixel(1, 0);

    // Draw main triangle
    renderer.path(['M', A[0], A[1], 'L', B[0], B[1], 'L', C[0], C[1], 'Z'])
        .attr({{
            'stroke': inkSoft,
            'stroke-width': 3,
            'fill': 'none'
        }})
        .add();

    // Draw grid lines at 20% intervals
    for (var i = 1; i <= 4; i++) {{
        var frac = i * 0.2;

        // Lines parallel to BC (constant Sand/A)
        var p1 = toPixel(0.5 * (1 - frac) + frac * 0, triHeight * (1 - frac));
        var p2 = toPixel(0.5 * (1 - frac) + frac * 1, triHeight * (1 - frac));
        renderer.path(['M', p1[0], p1[1], 'L', p2[0], p2[1]])
            .attr({{'stroke': gridColor, 'stroke-width': 2}}).add();

        // Lines parallel to AC (constant Silt/B)
        var q1 = toPixel(0.5 * frac, triHeight * frac);
        var q2 = toPixel(frac, 0);
        renderer.path(['M', q1[0], q1[1], 'L', q2[0], q2[1]])
            .attr({{'stroke': gridColor, 'stroke-width': 2}}).add();

        // Lines parallel to AB (constant Clay/C)
        var r1 = toPixel(0.5 * frac + (1 - frac), triHeight * frac);
        var r2 = toPixel(1 - frac, 0);
        renderer.path(['M', r1[0], r1[1], 'L', r2[0], r2[1]])
            .attr({{'stroke': gridColor, 'stroke-width': 2}}).add();
    }}

    // Vertex labels
    renderer.text('Sand (100%)', A[0], A[1] - 40)
        .css({{'fontSize': '22px', 'color': ink, 'textAnchor': 'middle'}})
        .add();

    renderer.text('Silt (100%)', B[0] - 60, B[1] + 80)
        .css({{'fontSize': '22px', 'color': ink, 'textAnchor': 'middle'}})
        .add();

    renderer.text('Clay (100%)', C[0] + 60, C[1] + 80)
        .css({{'fontSize': '22px', 'color': ink, 'textAnchor': 'middle'}})
        .add();

    // Tick labels along edges (20%, 40%, 60%, 80%)
    for (var i = 1; i <= 4; i++) {{
        var pct = i * 20;
        var frac = i * 0.2;

        // Sand axis (left edge, going up from B to A)
        var sandPos = toPixel(0.5 * frac, triHeight * frac);
        renderer.text(pct + '%', sandPos[0] - 80, sandPos[1] + 10)
            .css({{'fontSize': '18px', 'color': inkSoft}}).add();

        // Silt axis (bottom edge, going right from B to C)
        var siltPos = toPixel(frac, 0);
        renderer.text(pct + '%', siltPos[0], siltPos[1] + 70)
            .css({{'fontSize': '18px', 'color': inkSoft}}).add();

        // Clay axis (right edge, going up from C to A)
        var clayPos = toPixel(1 - 0.5 * frac, triHeight * frac);
        renderer.text(pct + '%', clayPos[0] + 50, clayPos[1] + 10)
            .css({{'fontSize': '18px', 'color': inkSoft}}).add();
    }}
}})();
"""

html_str = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        {html_str}
        setTimeout(function() {{
            {custom_js}
        }}, 100);
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG
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

driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
