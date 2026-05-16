""" anyplot.ai
contour-3d: 3D Contour Plot
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-16
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Viridis colormap (continuous data)
VIRIDIS_COLORS = [
    (68, 1, 84),  # Dark purple
    (59, 82, 139),  # Blue-purple
    (33, 145, 140),  # Teal
    (94, 201, 98),  # Green
    (253, 231, 37),  # Yellow
]

# Data - wave surface (different from other libraries)
np.random.seed(42)
n_points = 45

x = np.linspace(-np.pi, np.pi, n_points)
y = np.linspace(-np.pi, np.pi, n_points)
X, Y = np.meshgrid(x, y)

# Create wave surface: combination of sine and cosine waves
Z = np.sin(X) * np.cos(Y) + 0.3 * np.sin(2 * X) * np.cos(2 * Y)

# Normalize Z values for color mapping
z_min, z_max = Z.min(), Z.max()
z_normalized = (Z - z_min) / (z_max - z_min)


def get_color(val):
    """Interpolate color from viridis palette based on normalized value (0-1)."""
    n_colors = len(VIRIDIS_COLORS) - 1
    idx = min(int(val * n_colors), n_colors - 1)
    t = (val * n_colors) - idx
    r = int(VIRIDIS_COLORS[idx][0] + t * (VIRIDIS_COLORS[idx + 1][0] - VIRIDIS_COLORS[idx][0]))
    g = int(VIRIDIS_COLORS[idx][1] + t * (VIRIDIS_COLORS[idx + 1][1] - VIRIDIS_COLORS[idx][1]))
    b = int(VIRIDIS_COLORS[idx][2] + t * (VIRIDIS_COLORS[idx + 1][2] - VIRIDIS_COLORS[idx][2]))
    return f"rgb({r},{g},{b})"


# Create surface data as scatter3d points
surface_data = []
for i in range(n_points):
    for j in range(n_points):
        val = z_normalized[i, j]
        color = get_color(val)
        surface_data.append({"x": float(X[i, j]), "y": float(Z[i, j]), "z": float(Y[i, j]), "color": color})

# Wireframe mesh lines
x_line_series = []
for i in range(0, n_points, 3):
    line_data = []
    for j in range(n_points):
        val = z_normalized[i, j]
        color = get_color(val)
        line_data.append({"x": float(X[i, j]), "y": float(Z[i, j]), "z": float(Y[i, j]), "color": color})

    x_line_series.append(
        {
            "type": "scatter3d",
            "data": line_data,
            "lineWidth": 2,
            "showInLegend": False,
            "marker": {"enabled": False},
            "color": "#666666" if THEME == "light" else "#999999",
            "opacity": 0.4,
        }
    )

y_line_series = []
for j in range(0, n_points, 3):
    line_data = []
    for i in range(n_points):
        val = z_normalized[i, j]
        color = get_color(val)
        line_data.append({"x": float(X[i, j]), "y": float(Z[i, j]), "z": float(Y[i, j]), "color": color})

    y_line_series.append(
        {
            "type": "scatter3d",
            "data": line_data,
            "lineWidth": 2,
            "showInLegend": False,
            "marker": {"enabled": False},
            "color": "#666666" if THEME == "light" else "#999999",
            "opacity": 0.4,
        }
    )


def extract_contour_paths(Z, X, Y, level, tolerance=0.02):
    """Extract contour paths at a given level using marching squares."""
    rows, cols = Z.shape
    segments = []

    ms_table = {
        0: [],
        1: [[3, 2]],
        2: [[1, 2]],
        3: [[3, 1]],
        4: [[0, 1]],
        5: [[0, 3], [1, 2]],
        6: [[0, 2]],
        7: [[0, 3]],
        8: [[0, 3]],
        9: [[0, 2]],
        10: [[0, 1], [2, 3]],
        11: [[0, 1]],
        12: [[1, 3]],
        13: [[1, 2]],
        14: [[2, 3]],
        15: [],
    }

    for i in range(rows - 1):
        for j in range(cols - 1):
            tl, tr = Z[i, j], Z[i, j + 1]
            br, bl = Z[i + 1, j + 1], Z[i + 1, j]

            config = 0
            if tl >= level:
                config |= 8
            if tr >= level:
                config |= 4
            if br >= level:
                config |= 2
            if bl >= level:
                config |= 1

            edges = ms_table[config]
            if not edges:
                continue

            edge_points = {}

            if tl != tr:
                t = (level - tl) / (tr - tl)
                if 0 <= t <= 1:
                    edge_points[0] = (j + t, i)

            if tr != br:
                t = (level - tr) / (br - tr)
                if 0 <= t <= 1:
                    edge_points[1] = (j + 1, i + t)

            if bl != br:
                t = (level - bl) / (br - bl)
                if 0 <= t <= 1:
                    edge_points[2] = (j + t, i + 1)

            if tl != bl:
                t = (level - tl) / (bl - tl)
                if 0 <= t <= 1:
                    edge_points[3] = (j, i + t)

            for e1, e2 in edges:
                if e1 in edge_points and e2 in edge_points:
                    segments.append((edge_points[e1], edge_points[e2]))

    if not segments:
        return []

    paths = []
    remaining = list(segments)

    while remaining:
        seg = remaining.pop(0)
        path = [seg[0], seg[1]]

        changed = True
        while changed:
            changed = False
            for idx, seg in enumerate(remaining):
                if np.allclose(seg[0], path[-1], atol=tolerance):
                    path.append(seg[1])
                    remaining.pop(idx)
                    changed = True
                    break
                elif np.allclose(seg[1], path[-1], atol=tolerance):
                    path.append(seg[0])
                    remaining.pop(idx)
                    changed = True
                    break
                elif np.allclose(seg[1], path[0], atol=tolerance):
                    path.insert(0, seg[0])
                    remaining.pop(idx)
                    changed = True
                    break
                elif np.allclose(seg[0], path[0], atol=tolerance):
                    path.insert(0, seg[1])
                    remaining.pop(idx)
                    changed = True
                    break

        if len(path) >= 3:
            paths.append(path)

    return paths


# Extract contour lines
n_contour_levels = 12
contour_values = np.linspace(z_min, z_max, n_contour_levels + 2)[1:-1]

contour_series = []
contour_base_series = []

for level in contour_values:
    level_normalized = (level - z_min) / (z_max - z_min)
    contour_color = get_color(level_normalized)

    paths = extract_contour_paths(Z, X, Y, level)

    for path in paths:
        if len(path) < 3:
            continue

        step = max(1, len(path) // 100)
        subsampled = path[::step]
        if len(path) > step:
            subsampled.append(path[-1])

        # Contour line on surface with shadow
        line_data = []
        for pt in subsampled:
            j_idx, i_idx = pt
            i_int, j_int = int(i_idx), int(j_idx)
            i_frac, j_frac = i_idx - i_int, j_idx - j_int

            i_int = min(i_int, n_points - 2)
            j_int = min(j_int, n_points - 2)

            x_val = X[i_int, j_int] * (1 - j_frac) + X[i_int, j_int + 1] * j_frac
            y_val = Y[i_int, j_int] * (1 - i_frac) + Y[i_int + 1, j_int] * i_frac
            z_val = level

            line_data.append({"x": float(x_val), "y": float(z_val), "z": float(y_val)})

        # Shadow line
        contour_series.append(
            {
                "type": "scatter3d",
                "data": line_data,
                "lineWidth": 5,
                "showInLegend": False,
                "marker": {"enabled": False},
                "color": "#000000" if THEME == "light" else "#555555",
                "opacity": 0.3,
                "zIndex": 5,
            }
        )

        # Bright contour line
        contour_series.append(
            {
                "type": "scatter3d",
                "data": line_data,
                "lineWidth": 3,
                "showInLegend": False,
                "marker": {"enabled": False},
                "color": contour_color,
                "zIndex": 6,
            }
        )

        # Base plane projection
        base_data = []
        for pt in line_data:
            base_data.append({"x": pt["x"], "y": float(z_min - 0.1), "z": pt["z"]})

        contour_base_series.append(
            {
                "type": "scatter3d",
                "data": base_data,
                "lineWidth": 2,
                "showInLegend": False,
                "marker": {"enabled": False},
                "color": contour_color,
                "dashStyle": "Dash",
                "opacity": 0.4,
                "zIndex": 1,
            }
        )

# Surface series
surface_series = {
    "type": "scatter3d",
    "data": surface_data,
    "showInLegend": False,
    "marker": {"enabled": True, "radius": 5},
    "colorKey": "color",
    "zIndex": 2,
}

# Combine all series
all_series = [surface_series] + x_line_series + y_line_series + contour_base_series + contour_series
series_json = json.dumps(all_series)


# Download Highcharts JS
def fetch_url(url, max_retries=3):
    """Fetch URL with retries and proper headers."""
    import time as time_module

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://anyplot.ai",
        "Accept": "*/*",
        "Cache-Control": "no-cache",
    }
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8")
        except Exception:
            if attempt == max_retries - 1:
                raise
            time_module.sleep(2**attempt)
    return None


highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_3d_url = "https://code.highcharts.com/highcharts-3d.js"

highcharts_js = fetch_url(highcharts_url)
highcharts_3d_js = fetch_url(highcharts_3d_url)

# Chart configuration
chart_config = f"""
Highcharts.chart('container', {{
    chart: {{
        renderTo: 'container',
        type: 'scatter3d',
        width: 4800,
        height: 2700,
        backgroundColor: '{PAGE_BG}',
        options3d: {{
            enabled: true,
            alpha: 25,
            beta: 40,
            depth: 550,
            viewDistance: 3,
            fitToPlot: false,
            frame: {{
                bottom: {{ size: 2, color: '{GRID}' }},
                back: {{ size: 2, color: '{GRID}' }},
                side: {{ size: 2, color: '{GRID}' }}
            }}
        }},
        marginTop: 200,
        marginBottom: 200,
        marginLeft: 180,
        marginRight: 600
    }},
    title: {{
        text: 'contour-3d · highcharts · anyplot.ai',
        style: {{ fontSize: '28px', fontWeight: 'bold', color: '{INK}' }},
        y: 60
    }},
    xAxis: {{
        min: {-np.pi:.2f},
        max: {np.pi:.2f},
        tickInterval: 1.5,
        title: {{
            text: 'X Position',
            style: {{ fontSize: '22px', color: '{INK}', fontWeight: 'bold' }},
            margin: 50
        }},
        labels: {{
            style: {{ fontSize: '18px', color: '{INK_SOFT}' }},
            format: '{{value:.1f}}'
        }},
        gridLineWidth: 1,
        gridLineColor: '{GRID}',
        lineColor: '{INK_SOFT}',
        tickColor: '{INK_SOFT}'
    }},
    yAxis: {{
        min: {z_min - 0.2:.2f},
        max: {z_max + 0.2:.2f},
        tickInterval: 0.5,
        title: {{
            text: 'Z Height',
            style: {{ fontSize: '22px', color: '{INK}', fontWeight: 'bold' }},
            margin: 40
        }},
        labels: {{
            style: {{ fontSize: '18px', color: '{INK_SOFT}' }},
            format: '{{value:.1f}}'
        }},
        gridLineWidth: 1,
        gridLineColor: '{GRID}',
        lineColor: '{INK_SOFT}',
        tickColor: '{INK_SOFT}'
    }},
    zAxis: {{
        min: {-np.pi:.2f},
        max: {np.pi:.2f},
        tickInterval: 1.5,
        title: {{
            text: 'Y Position',
            style: {{ fontSize: '22px', color: '{INK}', fontWeight: 'bold' }},
            margin: 50
        }},
        labels: {{
            style: {{ fontSize: '18px', color: '{INK_SOFT}' }},
            format: '{{value:.1f}}'
        }},
        gridLineWidth: 1,
        gridLineColor: '{GRID}',
        lineColor: '{INK_SOFT}',
        tickColor: '{INK_SOFT}'
    }},
    legend: {{
        enabled: false
    }},
    credits: {{
        enabled: false
    }},
    tooltip: {{
        enabled: false
    }},
    plotOptions: {{
        scatter3d: {{
            lineWidth: 2,
            states: {{
                hover: {{ enabled: false }},
                inactive: {{ opacity: 1 }}
            }}
        }}
    }},
    series: {series_json}
}});

// Colorbar
var chart = Highcharts.charts[0];
var renderer = chart.renderer;

var colorbarX = 4350;
var colorbarY = 450;
var colorbarWidth = 60;
var colorbarHeight = 1600;

var numSteps = 50;
var stepHeight = colorbarHeight / numSteps;
var colors = [
    [68, 1, 84],
    [59, 82, 139],
    [33, 145, 140],
    [94, 201, 98],
    [253, 231, 37]
];

for (var i = 0; i < numSteps; i++) {{
    var val = i / (numSteps - 1);
    var nColors = colors.length - 1;
    var idx = Math.min(Math.floor(val * nColors), nColors - 1);
    var t = (val * nColors) - idx;
    var r = Math.round(colors[idx][0] + t * (colors[idx + 1][0] - colors[idx][0]));
    var g = Math.round(colors[idx][1] + t * (colors[idx + 1][1] - colors[idx][1]));
    var b = Math.round(colors[idx][2] + t * (colors[idx + 1][2] - colors[idx][2]));

    renderer.rect(colorbarX, colorbarY + colorbarHeight - (i + 1) * stepHeight, colorbarWidth, stepHeight + 1)
        .attr({{
            fill: 'rgb(' + r + ',' + g + ',' + b + ')',
            'stroke-width': 0
        }})
        .add();
}}

// Colorbar border
renderer.rect(colorbarX, colorbarY, colorbarWidth, colorbarHeight)
    .attr({{
        'stroke': '{INK_SOFT}',
        'stroke-width': 2,
        fill: 'none'
    }})
    .add();

// Colorbar labels
var zMinVal = {z_min:.2f};
var zMaxVal = {z_max:.2f};
var labelValues = [zMinVal, zMinVal + (zMaxVal - zMinVal) * 0.25, (zMinVal + zMaxVal) / 2, zMinVal + (zMaxVal - zMinVal) * 0.75, zMaxVal];
var labelPositions = [
    colorbarY + colorbarHeight,
    colorbarY + colorbarHeight * 0.75,
    colorbarY + colorbarHeight / 2,
    colorbarY + colorbarHeight * 0.25,
    colorbarY
];

for (var j = 0; j < 5; j++) {{
    renderer.text(labelValues[j].toFixed(2), colorbarX + colorbarWidth + 25, labelPositions[j] + 15)
        .css({{
            fontSize: '16px',
            color: '{INK_SOFT}'
        }})
        .add();
}}

// Colorbar title
renderer.text('Z Height', colorbarX + colorbarWidth / 2, colorbarY - 60)
    .attr({{ align: 'center' }})
    .css({{
        fontSize: '18px',
        fontWeight: 'bold',
        color: '{INK}'
    }})
    .add();
"""

# Save interactive HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_3d_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_config}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot for PNG
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
time.sleep(8)

driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
