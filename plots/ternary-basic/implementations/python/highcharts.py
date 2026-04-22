""" pyplots.ai
ternary-basic: Basic Ternary Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import math
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


# Data - Soil composition samples (sand, silt, clay percentages)
np.random.seed(42)
n_points = 50

# Generate random ternary compositions that sum to 100
raw = np.random.dirichlet([2, 2, 2], n_points) * 100
sand = raw[:, 0]  # Component A - Sand
silt = raw[:, 1]  # Component B - Silt
clay = raw[:, 2]  # Component C - Clay


# Convert ternary coordinates (a, b, c) to Cartesian (x, y) for equilateral triangle
# Triangle vertices: A at top (0.5, sqrt(3)/2), B at bottom-left (0, 0), C at bottom-right (1, 0)
def ternary_to_cartesian(a, b, c):
    """Convert ternary (a, b, c) to Cartesian (x, y) for equilateral triangle."""
    total = a + b + c
    a_norm = a / total
    b_norm = b / total
    c_norm = c / total
    x = 0.5 * (2 * b_norm + c_norm)
    y = (math.sqrt(3) / 2) * a_norm
    return x, y


# Convert all data points
cart_x = []
cart_y = []
for s, si, cl in zip(sand, silt, clay, strict=True):
    x, y = ternary_to_cartesian(s, si, cl)
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
    "backgroundColor": "#ffffff",
    "marginTop": 200,
    "marginBottom": 250,
    "marginLeft": 400,
    "marginRight": 400,
}

# Title
chart.options.title = {
    "text": "Soil Composition · ternary-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Axes - hide them since we're drawing our own triangle grid
chart.options.x_axis = {"min": -0.15, "max": 1.15, "visible": False, "gridLineWidth": 0}
chart.options.y_axis = {"min": -0.15, "max": 1.05, "visible": False, "gridLineWidth": 0}

# Legend
chart.options.legend = {"enabled": False}

# Credits
chart.options.credits = {"enabled": False}

# Tooltip showing ternary values
chart.options.tooltip = {
    "enabled": True,
    "headerFormat": "",
    "pointFormat": "<b>Sand:</b> {point.sand:.1f}%<br><b>Silt:</b> {point.silt:.1f}%<br><b>Clay:</b> {point.clay:.1f}%",
    "style": {"fontSize": "32px"},
}

# Create scatter series
series = ScatterSeries()
series.data = [
    {"x": float(x), "y": float(y), "sand": float(s), "silt": float(si), "clay": float(cl)}
    for x, y, s, si, cl in zip(cart_x, cart_y, sand, silt, clay, strict=True)
]
series.name = "Soil Samples"
series.color = "rgba(48, 105, 152, 0.7)"  # Python Blue with alpha
series.marker = {"radius": 18, "symbol": "circle"}

chart.add_series(series)

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Triangle coordinates (equilateral triangle)
tri_height = math.sqrt(3) / 2
# Vertices: A (top) = Sand, B (bottom-left) = Silt, C (bottom-right) = Clay
# A = (0.5, tri_height), B = (0, 0), C = (1, 0)

# Generate HTML with inline scripts and SVG annotations for the triangle
html_str = chart.to_js_literal()

# Custom JavaScript to draw triangle grid and labels after chart renders
custom_js = f"""
(function() {{
    var chart = Highcharts.charts[Highcharts.charts.length - 1];
    var renderer = chart.renderer;

    // Triangle vertices in pixel coordinates
    var xAxis = chart.xAxis[0];
    var yAxis = chart.yAxis[0];

    var triHeight = {tri_height};

    // Convert normalized coords to pixels
    function toPixel(nx, ny) {{
        return [xAxis.toPixels(nx), yAxis.toPixels(ny)];
    }}

    // Triangle vertices
    var A = toPixel(0.5, triHeight);  // Top - Sand
    var B = toPixel(0, 0);             // Bottom-left - Silt
    var C = toPixel(1, 0);             // Bottom-right - Clay

    // Draw main triangle
    renderer.path(['M', A[0], A[1], 'L', B[0], B[1], 'L', C[0], C[1], 'Z'])
        .attr({{
            'stroke': '#333333',
            'stroke-width': 4,
            'fill': 'none'
        }})
        .add();

    // Draw grid lines at 20% intervals
    var gridColor = 'rgba(0, 0, 0, 0.2)';
    var gridWidth = 2;

    for (var i = 1; i <= 4; i++) {{
        var frac = i * 0.2;

        // Lines parallel to BC (constant Sand/A)
        var p1 = toPixel(0.5 * (1 - frac) + frac * 0, triHeight * (1 - frac));
        var p2 = toPixel(0.5 * (1 - frac) + frac * 1, triHeight * (1 - frac));
        renderer.path(['M', p1[0], p1[1], 'L', p2[0], p2[1]])
            .attr({{'stroke': gridColor, 'stroke-width': gridWidth}}).add();

        // Lines parallel to AC (constant Silt/B)
        var q1 = toPixel(0.5 * frac, triHeight * frac);
        var q2 = toPixel(frac, 0);
        renderer.path(['M', q1[0], q1[1], 'L', q2[0], q2[1]])
            .attr({{'stroke': gridColor, 'stroke-width': gridWidth}}).add();

        // Lines parallel to AB (constant Clay/C)
        var r1 = toPixel(0.5 * frac + (1 - frac), triHeight * frac);
        var r2 = toPixel(1 - frac, 0);
        renderer.path(['M', r1[0], r1[1], 'L', r2[0], r2[1]])
            .attr({{'stroke': gridColor, 'stroke-width': gridWidth}}).add();
    }}

    // Vertex labels
    renderer.text('Sand (100%)', A[0], A[1] - 40)
        .css({{'fontSize': '48px', 'fontWeight': 'bold', 'textAnchor': 'middle'}})
        .add();

    renderer.text('Silt (100%)', B[0] - 60, B[1] + 80)
        .css({{'fontSize': '48px', 'fontWeight': 'bold', 'textAnchor': 'middle'}})
        .add();

    renderer.text('Clay (100%)', C[0] + 60, C[1] + 80)
        .css({{'fontSize': '48px', 'fontWeight': 'bold', 'textAnchor': 'middle'}})
        .add();

    // Tick labels along edges (20%, 40%, 60%, 80%)
    var labelStyle = {{'fontSize': '32px', 'fill': '#666666'}};

    for (var i = 1; i <= 4; i++) {{
        var pct = i * 20;
        var frac = i * 0.2;

        // Sand axis (left edge, going up from B to A)
        var sandPos = toPixel(0.5 * frac, triHeight * frac);
        renderer.text(pct + '%', sandPos[0] - 80, sandPos[1] + 10)
            .css(labelStyle).add();

        // Silt axis (bottom edge, going right from B to C)
        var siltPos = toPixel(frac, 0);
        renderer.text(pct + '%', siltPos[0], siltPos[1] + 70)
            .css(labelStyle).add();

        // Clay axis (right edge, going up from C to A)
        var clayPos = toPixel(1 - 0.5 * frac, triHeight * frac);
        renderer.text(pct + '%', clayPos[0] + 50, clayPos[1] + 10)
            .css(labelStyle).add();
    }}
}})();
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        {html_str}
        setTimeout(function() {{
            {custom_js}
        }}, 100);
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
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Take screenshot of just the chart container element
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        {html_str}
        setTimeout(function() {{
            {custom_js}
        }}, 100);
    </script>
</body>
</html>"""
    f.write(interactive_html)
