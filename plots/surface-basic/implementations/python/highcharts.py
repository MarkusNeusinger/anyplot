""" pyplots.ai
surface-basic: Basic 3D Surface Plot
Library: highcharts unknown | Python 3.13.11
Quality: 87/100 | Created: 2025-12-23
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Viridis-like colormap RGB values (inline to follow KISS - no functions)
VIRIDIS_COLORS = [
    (68, 1, 84),  # Dark purple
    (59, 82, 139),  # Blue-purple
    (33, 145, 140),  # Teal
    (94, 201, 98),  # Green
    (253, 231, 37),  # Yellow
]

# Data - Gaussian surface with peaks and valleys
np.random.seed(42)
n_points = 40  # Grid size for smooth surface
x = np.linspace(-3, 3, n_points)
y = np.linspace(-3, 3, n_points)
X, Y = np.meshgrid(x, y)

# Create an interesting surface: combination of Gaussian peaks
Z = (
    np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))  # Peak at (1, 1)
    + 0.8 * np.exp(-((X + 1) ** 2 + (Y + 1) ** 2))  # Peak at (-1, -1)
    - 0.5 * np.exp(-((X) ** 2 + (Y) ** 2) / 0.5)  # Valley at center
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

# Create surface data as scatter3d points with colors (inline color calc for KISS)
surface_data = []
n_colors = len(VIRIDIS_COLORS) - 1
for i in range(n_points):
    for j in range(n_points):
        val = z_normalized[i, j]
        idx = min(int(val * n_colors), n_colors - 1)
        t = (val * n_colors) - idx
        r = int(VIRIDIS_COLORS[idx][0] + t * (VIRIDIS_COLORS[idx + 1][0] - VIRIDIS_COLORS[idx][0]))
        g = int(VIRIDIS_COLORS[idx][1] + t * (VIRIDIS_COLORS[idx + 1][1] - VIRIDIS_COLORS[idx][1]))
        b = int(VIRIDIS_COLORS[idx][2] + t * (VIRIDIS_COLORS[idx + 1][2] - VIRIDIS_COLORS[idx][2]))
        color = f"rgb({r},{g},{b})"
        surface_data.append(
            {
                "x": float(X[i, j]),
                "y": float(Z[i, j]),  # Height is Z value
                "z": float(Y[i, j]),  # Depth is Y grid position
                "color": color,
            }
        )

# Create connecting lines for X direction (reduced density for cleaner surface)
x_line_series = []
for i in range(0, n_points, 2):  # Skip every other line for cleaner appearance
    line_data = []
    for j in range(n_points):
        val = z_normalized[i, j]
        idx = min(int(val * n_colors), n_colors - 1)
        t = (val * n_colors) - idx
        r = int(VIRIDIS_COLORS[idx][0] + t * (VIRIDIS_COLORS[idx + 1][0] - VIRIDIS_COLORS[idx][0]))
        g = int(VIRIDIS_COLORS[idx][1] + t * (VIRIDIS_COLORS[idx + 1][1] - VIRIDIS_COLORS[idx][1]))
        b = int(VIRIDIS_COLORS[idx][2] + t * (VIRIDIS_COLORS[idx + 1][2] - VIRIDIS_COLORS[idx][2]))
        color = f"rgb({r},{g},{b})"
        line_data.append({"x": float(X[i, j]), "y": float(Z[i, j]), "z": float(Y[i, j]), "color": color})

    # Color for the line based on middle value
    mid_val = z_normalized[i, n_points // 2]
    mid_idx = min(int(mid_val * n_colors), n_colors - 1)
    mid_t = (mid_val * n_colors) - mid_idx
    mid_r = int(VIRIDIS_COLORS[mid_idx][0] + mid_t * (VIRIDIS_COLORS[mid_idx + 1][0] - VIRIDIS_COLORS[mid_idx][0]))
    mid_g = int(VIRIDIS_COLORS[mid_idx][1] + mid_t * (VIRIDIS_COLORS[mid_idx + 1][1] - VIRIDIS_COLORS[mid_idx][1]))
    mid_b = int(VIRIDIS_COLORS[mid_idx][2] + mid_t * (VIRIDIS_COLORS[mid_idx + 1][2] - VIRIDIS_COLORS[mid_idx][2]))
    line_color = f"rgb({mid_r},{mid_g},{mid_b})"
    x_line_series.append(
        {
            "type": "scatter3d",
            "data": line_data,
            "lineWidth": 3,
            "showInLegend": False,
            "marker": {"enabled": False},
            "color": line_color,
        }
    )

# Create connecting lines for Y direction (reduced density for cleaner surface)
y_line_series = []
for j in range(0, n_points, 2):  # Skip every other line for cleaner appearance
    line_data = []
    for i in range(n_points):
        val = z_normalized[i, j]
        idx = min(int(val * n_colors), n_colors - 1)
        t = (val * n_colors) - idx
        r = int(VIRIDIS_COLORS[idx][0] + t * (VIRIDIS_COLORS[idx + 1][0] - VIRIDIS_COLORS[idx][0]))
        g = int(VIRIDIS_COLORS[idx][1] + t * (VIRIDIS_COLORS[idx + 1][1] - VIRIDIS_COLORS[idx][1]))
        b = int(VIRIDIS_COLORS[idx][2] + t * (VIRIDIS_COLORS[idx + 1][2] - VIRIDIS_COLORS[idx][2]))
        color = f"rgb({r},{g},{b})"
        line_data.append({"x": float(X[i, j]), "y": float(Z[i, j]), "z": float(Y[i, j]), "color": color})

    # Color for the line based on middle value
    mid_val = z_normalized[n_points // 2, j]
    mid_idx = min(int(mid_val * n_colors), n_colors - 1)
    mid_t = (mid_val * n_colors) - mid_idx
    mid_r = int(VIRIDIS_COLORS[mid_idx][0] + mid_t * (VIRIDIS_COLORS[mid_idx + 1][0] - VIRIDIS_COLORS[mid_idx][0]))
    mid_g = int(VIRIDIS_COLORS[mid_idx][1] + mid_t * (VIRIDIS_COLORS[mid_idx + 1][1] - VIRIDIS_COLORS[mid_idx][1]))
    mid_b = int(VIRIDIS_COLORS[mid_idx][2] + mid_t * (VIRIDIS_COLORS[mid_idx + 1][2] - VIRIDIS_COLORS[mid_idx][2]))
    line_color = f"rgb({mid_r},{mid_g},{mid_b})"
    y_line_series.append(
        {
            "type": "scatter3d",
            "data": line_data,
            "lineWidth": 3,
            "showInLegend": False,
            "marker": {"enabled": False},
            "color": line_color,
        }
    )

# Surface points with large markers to create filled appearance
surface_series = {
    "type": "scatter3d",
    "data": surface_data,
    "showInLegend": False,
    "marker": {"enabled": True, "radius": 8, "symbol": "circle"},
    "colorKey": "color",
}

all_series = [surface_series] + x_line_series + y_line_series
series_json = json.dumps(all_series)

# Highcharts chart configuration with improved layout and colorbar
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
            alpha: 15,
            beta: 30,
            depth: 550,
            viewDistance: 3,
            fitToPlot: false,
            frame: {{
                bottom: {{ size: 1, color: 'rgba(0,0,0,0.08)' }},
                back: {{ size: 1, color: 'rgba(0,0,0,0.05)' }},
                side: {{ size: 1, color: 'rgba(0,0,0,0.05)' }}
            }}
        }},
        marginTop: 220,
        marginBottom: 250,
        marginLeft: 200,
        marginRight: 550
    }},
    title: {{
        text: 'surface-basic · highcharts · pyplots.ai',
        style: {{ fontSize: '80px', fontWeight: 'bold' }}
    }},
    subtitle: {{
        text: 'Gaussian Surface with Peaks and Valley',
        style: {{ fontSize: '52px', color: '#666666' }}
    }},
    xAxis: {{
        min: -3.5,
        max: 3.5,
        tickInterval: 1,
        title: {{
            text: 'X Position (units)',
            style: {{ fontSize: '56px', color: '#306998', fontWeight: 'bold' }},
            margin: 80
        }},
        labels: {{
            style: {{ fontSize: '44px' }},
            format: '{{value}}',
            y: 30
        }},
        gridLineWidth: 1,
        gridLineColor: 'rgba(0, 0, 0, 0.1)'
    }},
    yAxis: {{
        min: -0.6,
        max: 1.2,
        tickInterval: 0.3,
        title: {{
            text: 'Z Height (amplitude)',
            style: {{ fontSize: '56px', color: '#306998', fontWeight: 'bold' }},
            margin: 60
        }},
        labels: {{
            style: {{ fontSize: '44px' }},
            format: '{{value:.1f}}',
            x: -20
        }},
        gridLineWidth: 1,
        gridLineColor: 'rgba(0, 0, 0, 0.1)'
    }},
    zAxis: {{
        min: -3.5,
        max: 3.5,
        tickInterval: 1,
        title: {{
            text: 'Y Position (units)',
            style: {{ fontSize: '56px', color: '#306998', fontWeight: 'bold' }},
            margin: 80
        }},
        labels: {{
            style: {{ fontSize: '44px' }}
        }},
        gridLineWidth: 1,
        gridLineColor: 'rgba(0, 0, 0, 0.1)'
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
            lineWidth: 3,
            states: {{
                hover: {{
                    enabled: false
                }},
                inactive: {{
                    opacity: 1
                }}
            }}
        }}
    }},
    series: {series_json}
}});

// Draw colorbar manually
var chart = Highcharts.charts[0];
var renderer = chart.renderer;

// Colorbar position and dimensions - moved left for better visibility
var colorbarX = 4300;
var colorbarY = 550;
var colorbarWidth = 70;
var colorbarHeight = 1300;

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

// Colorbar labels with more values for clarity
var zMin = {z_min:.2f};
var zMax = {z_max:.2f};
var labelValues = [zMin, zMin + (zMax - zMin) * 0.25, (zMin + zMax) / 2, zMin + (zMax - zMin) * 0.75, zMax];
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
renderer.text('Z Height (amplitude)', colorbarX + colorbarWidth / 2, colorbarY - 50)
    .attr({{
        align: 'center'
    }})
    .css({{
        fontSize: '52px',
        fontWeight: 'bold',
        color: '#306998'
    }})
    .add();
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
time.sleep(10)  # Extra time for 3D rendering with many series and colorbar

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
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{chart_config}</script>
</body>
</html>"""
    f.write(interactive_html)
