""" anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-16
"""

import json
import os
import tempfile
import time
from pathlib import Path

import numpy as np
import requests
from requests.adapters import HTTPAdapter
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib3.util.retry import Retry


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data - Lorenz attractor trajectory (chaotic system)
np.random.seed(42)

# Generate Lorenz attractor trajectory using Euler method
sigma, rho, beta = 10, 28, 8 / 3
dt = 0.01
steps = 3000

x = np.zeros(steps)
y = np.zeros(steps)
z = np.zeros(steps)
x[0], y[0], z[0] = 1.0, 1.0, 1.0

for i in range(1, steps):
    dx = sigma * (y[i - 1] - x[i - 1])
    dy = x[i - 1] * (rho - z[i - 1]) - y[i - 1]
    dz = x[i - 1] * y[i - 1] - beta * z[i - 1]
    x[i] = x[i - 1] + dx * dt
    y[i] = y[i - 1] + dy * dt
    z[i] = z[i - 1] + dz * dt

# Downsample for smoother rendering
sample_rate = 3
x_sampled = x[::sample_rate]
y_sampled = y[::sample_rate]
z_sampled = z[::sample_rate]

# Create trajectory data with color gradient (time progression)
trajectory_data = []
color_axis_data = []
n_points = len(x_sampled)
for i in range(n_points):
    trajectory_data.append(
        {
            "x": float(x_sampled[i]),
            "y": float(y_sampled[i]),
            "z": float(z_sampled[i]),
            "colorValue": i / n_points,  # Time progression: 0 to 1
        }
    )
    color_axis_data.append(i / n_points)

# Download required Highcharts modules from jsDelivr CDN
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
highcharts_3d_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts-3d.js"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})

retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

response = session.get(highcharts_url, timeout=30)
response.raise_for_status()
highcharts_js = response.text

response = session.get(highcharts_3d_url, timeout=30)
response.raise_for_status()
highcharts_3d_js = response.text

# Create HTML content with inline scripts
trajectory_json = json.dumps(trajectory_data)

chart_config = f"""
Highcharts.chart('container', {{
    chart: {{
        type: 'scatter3d',
        width: 4800,
        height: 2700,
        backgroundColor: '{PAGE_BG}',
        options3d: {{
            enabled: true,
            alpha: 20,
            beta: 30,
            depth: 600,
            viewDistance: 5,
            fitToPlot: true,
            frame: {{
                bottom: {{ size: 1, color: '{INK_SOFT}' }},
                back: {{ size: 1, color: '{INK_SOFT}' }},
                side: {{ size: 1, color: '{INK_SOFT}' }}
            }}
        }},
        marginTop: 200,
        marginBottom: 200,
        marginLeft: 150,
        marginRight: 150
    }},
    title: {{
        text: 'Lorenz Attractor · line-3d-trajectory · highcharts · anyplot.ai',
        style: {{ fontSize: '28px', fontWeight: 'bold', color: '{INK}' }},
        y: 40
    }},
    xAxis: {{
        min: -25,
        max: 25,
        tickInterval: 10,
        title: {{
            text: 'X Position',
            style: {{ fontSize: '22px', color: '{INK}', fontWeight: 'normal' }},
            margin: 30
        }},
        labels: {{
            style: {{ fontSize: '18px', color: '{INK_SOFT}' }},
            format: '{{value}}'
        }},
        lineColor: '{INK_SOFT}',
        tickColor: '{INK_SOFT}',
        gridLineWidth: 0
    }},
    yAxis: {{
        min: -30,
        max: 30,
        tickInterval: 10,
        title: {{
            text: 'Y Position',
            style: {{ fontSize: '22px', color: '{INK}', fontWeight: 'normal' }},
            margin: 30
        }},
        labels: {{
            style: {{ fontSize: '18px', color: '{INK_SOFT}' }},
            format: '{{value}}'
        }},
        lineColor: '{INK_SOFT}',
        tickColor: '{INK_SOFT}',
        gridLineWidth: 0
    }},
    zAxis: {{
        min: 0,
        max: 55,
        tickInterval: 10,
        title: {{
            text: 'Z Position',
            style: {{ fontSize: '22px', color: '{INK}', fontWeight: 'normal' }},
            margin: 30
        }},
        labels: {{
            style: {{ fontSize: '18px', color: '{INK_SOFT}' }},
            format: '{{value}}'
        }},
        lineColor: '{INK_SOFT}',
        tickColor: '{INK_SOFT}',
        gridLineWidth: 0
    }},
    colorAxis: {{
        min: 0,
        max: 1,
        stops: [
            [0, '{BRAND}'],
            [0.5, '#C475FD'],
            [1, '#4467A3']
        ],
        showInLegend: true
    }},
    legend: {{
        enabled: false
    }},
    tooltip: {{
        enabled: true,
        headerFormat: '<b>Position</b><br/>',
        pointFormat: 'X: {{point.x:.1f}}<br/>Y: {{point.y:.1f}}<br/>Z: {{point.z:.1f}}',
        style: {{ fontSize: '16px', color: '{INK}' }}
    }},
    plotOptions: {{
        scatter3d: {{
            marker: {{
                radius: 3,
                opacity: 0.8
            }},
            lineWidth: 2,
            lineColor: '{BRAND}',
            states: {{
                hover: {{
                    marker: {{
                        radius: 5,
                        opacity: 1
                    }}
                }}
            }}
        }}
    }},
    series: [{{
        type: 'scatter3d',
        name: 'Lorenz Trajectory',
        data: {trajectory_json},
        colorByPoint: true,
        lineWidth: 2,
        marker: {{
            radius: 2,
            symbol: 'circle'
        }}
    }}],
    credits: {{
        enabled: false
    }}
}});
"""

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
time.sleep(6)

driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML artifact with theme-aware styling
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
