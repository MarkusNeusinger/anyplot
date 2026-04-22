""" pyplots.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2025-12-24
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - 3D ripple function z = sin(sqrt(x^2 + y^2))
np.random.seed(42)
n_points = 18  # Grid size optimized for wireframe clarity
x = np.linspace(-5, 5, n_points)
y = np.linspace(-5, 5, n_points)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
Z = np.sin(R)

# Download required Highcharts modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_3d_url = "https://code.highcharts.com/highcharts-3d.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highcharts_3d_url, timeout=30) as response:
    highcharts_3d_js = response.read().decode("utf-8")

# Create line data for X direction (rows) - Python Blue
x_line_series = []
for i in range(n_points):
    line_data = []
    for j in range(n_points):
        line_data.append(
            [
                float(X[i, j]),  # X axis
                float(Y[i, j]),  # Y axis (corrected)
                float(Z[i, j]),  # Z axis (height)
            ]
        )
    x_line_series.append(
        {
            "type": "scatter3d",
            "data": line_data,
            "color": "#306998",
            "lineWidth": 6,
            "showInLegend": False,
            "marker": {"enabled": False},
        }
    )

# Create line data for Y direction (columns) - Darker blue
y_line_series = []
for j in range(n_points):
    line_data = []
    for i in range(n_points):
        line_data.append([float(X[i, j]), float(Y[i, j]), float(Z[i, j])])
    y_line_series.append(
        {
            "type": "scatter3d",
            "data": line_data,
            "color": "#1e4c73",
            "lineWidth": 6,
            "showInLegend": False,
            "marker": {"enabled": False},
        }
    )

all_series = x_line_series + y_line_series
series_json = json.dumps(all_series)

# Highcharts chart configuration with 3D scatter and lines
# Improved canvas utilization with better viewing angle and larger 3D frame
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
            alpha: 18,
            beta: 30,
            depth: 900,
            viewDistance: 5,
            fitToPlot: true,
            frame: {{
                bottom: {{ size: 3, color: 'rgba(48, 105, 152, 0.15)' }},
                back: {{ size: 3, color: 'rgba(48, 105, 152, 0.10)' }},
                side: {{ size: 3, color: 'rgba(48, 105, 152, 0.12)' }}
            }}
        }},
        marginTop: 180,
        marginBottom: 200,
        marginLeft: 120,
        marginRight: 120,
        spacingTop: 10,
        spacingBottom: 60,
        spacingLeft: 30,
        spacingRight: 30
    }},
    title: {{
        text: 'wireframe-3d-basic · highcharts · pyplots.ai',
        style: {{ fontSize: '80px', fontWeight: 'bold' }},
        y: 70
    }},
    subtitle: {{
        text: 'z = sin(√(x² + y²))',
        style: {{ fontSize: '56px', color: '#555555' }},
        y: 130
    }},
    xAxis: {{
        min: -5,
        max: 5,
        tickInterval: 2.5,
        title: {{
            text: 'X Position (units)',
            style: {{ fontSize: '52px', color: '#306998', fontWeight: 'bold' }},
            margin: 50
        }},
        labels: {{
            style: {{ fontSize: '40px' }},
            format: '{{value}}'
        }},
        gridLineWidth: 2,
        gridLineColor: 'rgba(0, 0, 0, 0.15)'
    }},
    yAxis: {{
        min: -5,
        max: 5,
        tickInterval: 2.5,
        title: {{
            text: 'Y Position (units)',
            style: {{ fontSize: '52px', color: '#306998', fontWeight: 'bold' }},
            margin: 50
        }},
        labels: {{
            style: {{ fontSize: '40px' }},
            format: '{{value}}'
        }},
        gridLineWidth: 2,
        gridLineColor: 'rgba(0, 0, 0, 0.15)'
    }},
    zAxis: {{
        min: -1.2,
        max: 1.2,
        tickInterval: 0.4,
        title: {{
            text: 'Z Amplitude',
            style: {{ fontSize: '52px', color: '#306998', fontWeight: 'bold' }},
            margin: 50
        }},
        labels: {{
            style: {{ fontSize: '40px' }},
            format: '{{value:.1f}}'
        }},
        gridLineWidth: 2,
        gridLineColor: 'rgba(0, 0, 0, 0.15)'
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
            lineWidth: 6,
            marker: {{
                enabled: false
            }},
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
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(8)  # Extra time for 3D rendering with many series

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
