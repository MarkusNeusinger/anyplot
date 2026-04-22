""" pyplots.ai
contour-3d: 3D Contour Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Viridis-like colormap RGB values for continuous coloring
VIRIDIS_COLORS = [
    (68, 1, 84),  # Dark purple
    (59, 82, 139),  # Blue-purple
    (33, 145, 140),  # Teal
    (94, 201, 98),  # Green
    (253, 231, 37),  # Yellow
]

# Data - create a 3D surface with interesting topography for contour visualization
np.random.seed(42)
n_points = 40  # Grid size for smooth surface

x = np.linspace(-3, 3, n_points)
y = np.linspace(-3, 3, n_points)
X, Y = np.meshgrid(x, y)

# Create an interesting surface: combination of Gaussian peaks and valleys
# Simulates terrain elevation or a response surface
Z = (
    1.2 * np.exp(-((X - 1) ** 2 + (Y - 1) ** 2) / 1.5)  # Peak at (1, 1)
    + 0.9 * np.exp(-((X + 1.5) ** 2 + (Y + 1) ** 2) / 1.2)  # Peak at (-1.5, -1)
    - 0.6 * np.exp(-((X + 0.5) ** 2 + (Y - 1.5) ** 2) / 0.8)  # Valley
    + 0.4 * np.exp(-((X - 1.5) ** 2 + (Y + 1.5) ** 2) / 1.0)  # Smaller peak
)

# Normalize Z values for color mapping
z_min, z_max = Z.min(), Z.max()
z_normalized = (Z - z_min) / (z_max - z_min)

# Download required Highcharts modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_3d_url = "https://code.highcharts.com/highcharts-3d.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highcharts_3d_url, timeout=30) as response:
    highcharts_3d_js = response.read().decode("utf-8")

# Helper to interpolate color from viridis palette
n_colors = len(VIRIDIS_COLORS) - 1


def get_color(val):
    """Interpolate color from viridis palette based on normalized value (0-1)."""
    idx = min(int(val * n_colors), n_colors - 1)
    t = (val * n_colors) - idx
    r = int(VIRIDIS_COLORS[idx][0] + t * (VIRIDIS_COLORS[idx + 1][0] - VIRIDIS_COLORS[idx][0]))
    g = int(VIRIDIS_COLORS[idx][1] + t * (VIRIDIS_COLORS[idx + 1][1] - VIRIDIS_COLORS[idx][1]))
    b = int(VIRIDIS_COLORS[idx][2] + t * (VIRIDIS_COLORS[idx + 1][2] - VIRIDIS_COLORS[idx][2]))
    return f"rgb({r},{g},{b})"


# Create surface data as scatter3d points with colors
surface_data = []
for i in range(n_points):
    for j in range(n_points):
        val = z_normalized[i, j]
        color = get_color(val)
        surface_data.append(
            {
                "x": float(X[i, j]),
                "y": float(Z[i, j]),  # Height is Z value
                "z": float(Y[i, j]),  # Depth is Y grid position
                "color": color,
            }
        )

# Create surface mesh lines for X direction (wireframe effect)
x_line_series = []
for i in range(0, n_points, 2):  # Every other line for cleaner appearance
    line_data = []
    for j in range(n_points):
        val = z_normalized[i, j]
        color = get_color(val)
        line_data.append({"x": float(X[i, j]), "y": float(Z[i, j]), "z": float(Y[i, j]), "color": color})

    mid_val = z_normalized[i, n_points // 2]
    line_color = get_color(mid_val)
    x_line_series.append(
        {
            "type": "scatter3d",
            "data": line_data,
            "lineWidth": 2,
            "showInLegend": False,
            "marker": {"enabled": False},
            "color": line_color,
        }
    )

# Create surface mesh lines for Y direction
y_line_series = []
for j in range(0, n_points, 2):  # Every other line for cleaner appearance
    line_data = []
    for i in range(n_points):
        val = z_normalized[i, j]
        color = get_color(val)
        line_data.append({"x": float(X[i, j]), "y": float(Z[i, j]), "z": float(Y[i, j]), "color": color})

    mid_val = z_normalized[n_points // 2, j]
    line_color = get_color(mid_val)
    y_line_series.append(
        {
            "type": "scatter3d",
            "data": line_data,
            "lineWidth": 2,
            "showInLegend": False,
            "marker": {"enabled": False},
            "color": line_color,
        }
    )

# Define contour levels (10 levels from min to max)
n_contour_levels = 10
contour_values = np.linspace(z_min, z_max, n_contour_levels + 2)[1:-1]  # Exclude endpoints


def extract_contour_paths(Z, X, Y, level, tolerance=0.02):
    """
    Extract contour paths at a given level using marching squares.
    Returns list of paths, each path is a list of (x, y, z) tuples.
    """
    rows, cols = Z.shape
    segments = []

    # Marching squares table
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

            # Top edge
            if tl != tr:
                t = (level - tl) / (tr - tl)
                if 0 <= t <= 1:
                    edge_points[0] = (j + t, i)

            # Right edge
            if tr != br:
                t = (level - tr) / (br - tr)
                if 0 <= t <= 1:
                    edge_points[1] = (j + 1, i + t)

            # Bottom edge
            if bl != br:
                t = (level - bl) / (br - bl)
                if 0 <= t <= 1:
                    edge_points[2] = (j + t, i + 1)

            # Left edge
            if tl != bl:
                t = (level - tl) / (bl - tl)
                if 0 <= t <= 1:
                    edge_points[3] = (j, i + t)

            for e1, e2 in edges:
                if e1 in edge_points and e2 in edge_points:
                    segments.append((edge_points[e1], edge_points[e2]))

    # Connect segments into paths
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


# Extract and create contour line series on the 3D surface
contour_series = []
contour_base_series = []  # Projected onto base plane

for level in contour_values:
    level_normalized = (level - z_min) / (z_max - z_min)
    contour_color = get_color(level_normalized)

    paths = extract_contour_paths(Z, X, Y, level)

    for path in paths:
        if len(path) < 3:
            continue

        # Subsample for performance
        step = max(1, len(path) // 100)
        subsampled = path[::step]
        if len(path) > step:
            subsampled.append(path[-1])

        # Contour line on surface
        line_data = []
        for pt in subsampled:
            j_idx, i_idx = pt
            # Interpolate Z value
            i_int, j_int = int(i_idx), int(j_idx)
            i_frac, j_frac = i_idx - i_int, j_idx - j_int

            # Bilinear interpolation for X, Y, Z
            i_int = min(i_int, n_points - 2)
            j_int = min(j_int, n_points - 2)

            x_val = X[i_int, j_int] * (1 - j_frac) + X[i_int, j_int + 1] * j_frac
            y_val = Y[i_int, j_int] * (1 - i_frac) + Y[i_int + 1, j_int] * i_frac
            z_val = level

            line_data.append(
                {
                    "x": float(x_val),
                    "y": float(z_val),  # Height
                    "z": float(y_val),  # Depth
                }
            )

        # Contour on surface with shadow effect for visibility
        contour_series.append(
            {
                "type": "scatter3d",
                "data": line_data,
                "lineWidth": 5,
                "showInLegend": False,
                "marker": {"enabled": False},
                "color": "#000000",  # Black shadow
                "zIndex": 5,
            }
        )
        contour_series.append(
            {
                "type": "scatter3d",
                "data": line_data,
                "lineWidth": 3,
                "showInLegend": False,
                "marker": {"enabled": False},
                "color": "#ffffff",  # White line
                "zIndex": 6,
            }
        )

        # Project contour onto base plane (z_min height)
        base_data = []
        for pt in line_data:
            base_data.append(
                {
                    "x": pt["x"],
                    "y": float(z_min - 0.05),  # Slightly below surface minimum
                    "z": pt["z"],
                }
            )

        contour_base_series.append(
            {
                "type": "scatter3d",
                "data": base_data,
                "lineWidth": 2,
                "showInLegend": False,
                "marker": {"enabled": False},
                "color": contour_color,
                "dashStyle": "Dash",
                "opacity": 0.5,
                "zIndex": 1,
            }
        )

# Surface points
surface_series = {
    "type": "scatter3d",
    "data": surface_data,
    "showInLegend": False,
    "marker": {"enabled": True, "radius": 6, "symbol": "circle"},
    "colorKey": "color",
    "zIndex": 2,
}

# Combine all series
all_series = [surface_series] + x_line_series + y_line_series + contour_base_series + contour_series
series_json = json.dumps(all_series)

# Highcharts chart configuration
chart_config = f"""
Highcharts.chart('container', {{
    chart: {{
        renderTo: 'container',
        type: 'scatter3d',
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        options3d: {{
            enabled: true,
            alpha: 20,
            beta: 35,
            depth: 550,
            viewDistance: 3,
            fitToPlot: false,
            frame: {{
                bottom: {{ size: 2, color: 'rgba(48, 105, 152, 0.15)' }},
                back: {{ size: 2, color: 'rgba(48, 105, 152, 0.08)' }},
                side: {{ size: 2, color: 'rgba(48, 105, 152, 0.10)' }}
            }}
        }},
        marginTop: 200,
        marginBottom: 200,
        marginLeft: 180,
        marginRight: 550
    }},
    title: {{
        text: 'contour-3d · highcharts · pyplots.ai',
        style: {{ fontSize: '80px', fontWeight: 'bold' }},
        y: 80
    }},
    subtitle: {{
        text: 'Surface with Contour Lines and Base Projections',
        style: {{ fontSize: '52px', color: '#666666' }},
        y: 140
    }},
    xAxis: {{
        min: -3.5,
        max: 3.5,
        tickInterval: 1,
        title: {{
            text: 'X Position (units)',
            style: {{ fontSize: '52px', color: '#306998', fontWeight: 'bold' }},
            margin: 70
        }},
        labels: {{
            style: {{ fontSize: '44px' }},
            format: '{{value}}',
            y: 25
        }},
        gridLineWidth: 2,
        gridLineColor: 'rgba(0, 0, 0, 0.12)'
    }},
    yAxis: {{
        min: {z_min - 0.15:.2f},
        max: {z_max + 0.15:.2f},
        tickInterval: 0.3,
        title: {{
            text: 'Z Height (amplitude)',
            style: {{ fontSize: '52px', color: '#306998', fontWeight: 'bold' }},
            margin: 50
        }},
        labels: {{
            style: {{ fontSize: '44px' }},
            format: '{{value:.1f}}',
            x: -15
        }},
        gridLineWidth: 2,
        gridLineColor: 'rgba(0, 0, 0, 0.12)'
    }},
    zAxis: {{
        min: -3.5,
        max: 3.5,
        tickInterval: 1,
        title: {{
            text: 'Y Position (units)',
            style: {{ fontSize: '52px', color: '#306998', fontWeight: 'bold' }},
            margin: 70
        }},
        labels: {{
            style: {{ fontSize: '44px' }}
        }},
        gridLineWidth: 2,
        gridLineColor: 'rgba(0, 0, 0, 0.12)'
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

// Draw colorbar manually
var chart = Highcharts.charts[0];
var renderer = chart.renderer;

// Colorbar position and dimensions
var colorbarX = 4300;
var colorbarY = 500;
var colorbarWidth = 70;
var colorbarHeight = 1400;

// Draw gradient rectangles for colorbar
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
        'stroke': '#333333',
        'stroke-width': 3,
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
            fontSize: '44px',
            fontWeight: 'bold',
            color: '#333333'
        }})
        .add();
}}

// Colorbar title
renderer.text('Z Height', colorbarX + colorbarWidth / 2, colorbarY - 50)
    .attr({{ align: 'center' }})
    .css({{
        fontSize: '52px',
        fontWeight: 'bold',
        color: '#306998'
    }})
    .add();

// Draw contour level indicators on colorbar
var contourLevels = {json.dumps([float(v) for v in contour_values])};
for (var k = 0; k < contourLevels.length; k++) {{
    var levelNorm = (contourLevels[k] - zMinVal) / (zMaxVal - zMinVal);
    var yPos = colorbarY + colorbarHeight - levelNorm * colorbarHeight;

    // White tick mark
    renderer.path(['M', colorbarX - 15, yPos, 'L', colorbarX + colorbarWidth + 15, yPos])
        .attr({{
            'stroke': '#ffffff',
            'stroke-width': 4
        }})
        .add();
}}
"""

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_3d_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_config}</script>
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
time.sleep(10)  # Extra time for 3D rendering with many series

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
    <script src="https://code.highcharts.com/highcharts-3d.js"></script>
    <style>
        body {{ margin: 0; font-family: Arial, sans-serif; }}
        #container {{ width: 100%; height: 100vh; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script>{chart_config}</script>
</body>
</html>"""
    f.write(interactive_html)
