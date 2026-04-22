""" pyplots.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
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


# Data - Lorenz attractor trajectory (chaotic system)
np.random.seed(42)


def lorenz_attractor(x, y, z, sigma=10, rho=28, beta=8 / 3):
    """Compute derivatives for Lorenz system."""
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    return dx, dy, dz


# Generate Lorenz attractor trajectory
dt = 0.01
steps = 3000

x = np.zeros(steps)
y = np.zeros(steps)
z = np.zeros(steps)

# Initial conditions
x[0], y[0], z[0] = 1.0, 1.0, 1.0

# Integrate using Euler method
for i in range(1, steps):
    dx, dy, dz = lorenz_attractor(x[i - 1], y[i - 1], z[i - 1])
    x[i] = x[i - 1] + dx * dt
    y[i] = y[i - 1] + dy * dt
    z[i] = z[i - 1] + dz * dt

# Downsample for smoother rendering (every 3rd point)
sample_rate = 3
x_sampled = x[::sample_rate]
y_sampled = y[::sample_rate]
z_sampled = z[::sample_rate]

# Download required Highcharts modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_3d_url = "https://code.highcharts.com/highcharts-3d.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highcharts_3d_url, timeout=30) as response:
    highcharts_3d_js = response.read().decode("utf-8")

# Create trajectory data as [x, y, z] points
trajectory_data = [[float(x_sampled[i]), float(y_sampled[i]), float(z_sampled[i])] for i in range(len(x_sampled))]

# Create color gradient based on time progression (using point index)
# Highcharts 3D scatter can show connected lines via lineWidth in plotOptions
trajectory_json = json.dumps(trajectory_data)

# Highcharts chart configuration with 3D line trajectory
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
            beta: 30,
            depth: 600,
            viewDistance: 5,
            fitToPlot: true,
            frame: {{
                bottom: {{ size: 2, color: 'rgba(48, 105, 152, 0.12)' }},
                back: {{ size: 2, color: 'rgba(48, 105, 152, 0.08)' }},
                side: {{ size: 2, color: 'rgba(48, 105, 152, 0.10)' }}
            }}
        }},
        marginTop: 180,
        marginBottom: 200,
        marginLeft: 180,
        marginRight: 180
    }},
    title: {{
        text: 'Lorenz Attractor · line-3d-trajectory · highcharts · pyplots.ai',
        style: {{ fontSize: '72px', fontWeight: 'bold' }},
        y: 70
    }},
    subtitle: {{
        text: 'Chaotic trajectory visualization in 3D phase space',
        style: {{ fontSize: '48px', color: '#666666' }},
        y: 130
    }},
    xAxis: {{
        min: -25,
        max: 25,
        tickInterval: 10,
        title: {{
            text: 'X Position',
            style: {{ fontSize: '48px', color: '#306998', fontWeight: 'bold' }},
            margin: 40
        }},
        labels: {{
            style: {{ fontSize: '40px' }},
            format: '{{value}}'
        }},
        gridLineWidth: 2,
        gridLineColor: 'rgba(0, 0, 0, 0.10)'
    }},
    yAxis: {{
        min: -30,
        max: 30,
        tickInterval: 10,
        title: {{
            text: 'Y Position',
            style: {{ fontSize: '48px', color: '#306998', fontWeight: 'bold' }},
            margin: 40
        }},
        labels: {{
            style: {{ fontSize: '40px' }},
            format: '{{value}}'
        }},
        gridLineWidth: 2,
        gridLineColor: 'rgba(0, 0, 0, 0.10)'
    }},
    zAxis: {{
        min: 0,
        max: 55,
        tickInterval: 10,
        title: {{
            text: 'Z Position',
            style: {{ fontSize: '48px', color: '#306998', fontWeight: 'bold' }},
            margin: 40
        }},
        labels: {{
            style: {{ fontSize: '40px' }},
            format: '{{value}}'
        }},
        gridLineWidth: 2,
        gridLineColor: 'rgba(0, 0, 0, 0.10)'
    }},
    legend: {{
        enabled: true,
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle',
        x: -40,
        y: 0,
        itemStyle: {{
            fontSize: '44px',
            fontWeight: 'normal'
        }},
        symbolRadius: 8,
        symbolHeight: 28,
        symbolWidth: 28,
        itemMarginBottom: 20
    }},
    credits: {{
        enabled: false
    }},
    tooltip: {{
        enabled: true,
        headerFormat: '<b>{{series.name}}</b><br>',
        pointFormat: 'X: {{point.x:.2f}}<br>Y: {{point.y:.2f}}<br>Z: {{point.z:.2f}}',
        style: {{ fontSize: '32px' }}
    }},
    plotOptions: {{
        scatter3d: {{
            marker: {{
                radius: 3,
                opacity: 0.7
            }},
            lineWidth: 4,
            lineColor: '#306998',
            states: {{
                hover: {{
                    enabled: true,
                    marker: {{
                        radius: 6
                    }}
                }}
            }}
        }}
    }},
    series: [{{
        type: 'scatter3d',
        name: 'Lorenz Trajectory',
        data: {trajectory_json},
        color: '#306998',
        marker: {{
            radius: 3,
            symbol: 'circle'
        }},
        lineWidth: 4
    }}]
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
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)  # Wait for 3D rendering

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
