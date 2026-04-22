""" pyplots.ai
scatter-3d: 3D Scatter Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - 3D clustered data demonstrating spatial relationships
np.random.seed(42)

# Create three distinct clusters in 3D space
n_points_per_cluster = 50

# Cluster 1: centered at (2, 2, 2) - Python Blue
cluster1_x = np.random.randn(n_points_per_cluster) * 0.8 + 2
cluster1_y = np.random.randn(n_points_per_cluster) * 0.8 + 2
cluster1_z = np.random.randn(n_points_per_cluster) * 0.8 + 2

# Cluster 2: centered at (-2, -1, 3) - Python Yellow
cluster2_x = np.random.randn(n_points_per_cluster) * 0.7 - 2
cluster2_y = np.random.randn(n_points_per_cluster) * 0.7 - 1
cluster2_z = np.random.randn(n_points_per_cluster) * 0.7 + 3

# Cluster 3: centered at (0, -2, -1) - Teal
cluster3_x = np.random.randn(n_points_per_cluster) * 0.9 + 0
cluster3_y = np.random.randn(n_points_per_cluster) * 0.9 - 2
cluster3_z = np.random.randn(n_points_per_cluster) * 0.9 - 1

# Download required Highcharts modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_3d_url = "https://code.highcharts.com/highcharts-3d.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highcharts_3d_url, timeout=30) as response:
    highcharts_3d_js = response.read().decode("utf-8")

# Create series data for each cluster
cluster1_data = [
    [float(cluster1_x[i]), float(cluster1_y[i]), float(cluster1_z[i])] for i in range(n_points_per_cluster)
]
cluster2_data = [
    [float(cluster2_x[i]), float(cluster2_y[i]), float(cluster2_z[i])] for i in range(n_points_per_cluster)
]
cluster3_data = [
    [float(cluster3_x[i]), float(cluster3_y[i]), float(cluster3_z[i])] for i in range(n_points_per_cluster)
]

# Define series with colorblind-safe colors
series_data = [
    {
        "type": "scatter3d",
        "name": "Cluster A",
        "data": cluster1_data,
        "color": "#306998",  # Python Blue
        "marker": {"radius": 14, "symbol": "circle"},
    },
    {
        "type": "scatter3d",
        "name": "Cluster B",
        "data": cluster2_data,
        "color": "#FFD43B",  # Python Yellow
        "marker": {"radius": 14, "symbol": "circle"},
    },
    {
        "type": "scatter3d",
        "name": "Cluster C",
        "data": cluster3_data,
        "color": "#17BECF",  # Teal
        "marker": {"radius": 14, "symbol": "circle"},
    },
]

series_json = json.dumps(series_data)

# Highcharts chart configuration with 3D scatter plot
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
            beta: 25,
            depth: 700,
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
        marginLeft: 150,
        marginRight: 220
    }},
    title: {{
        text: 'scatter-3d · highcharts · pyplots.ai',
        style: {{ fontSize: '80px', fontWeight: 'bold' }},
        y: 70
    }},
    subtitle: {{
        text: 'Three-dimensional clustered data visualization',
        style: {{ fontSize: '52px', color: '#666666' }},
        y: 130
    }},
    xAxis: {{
        min: -5,
        max: 5,
        tickInterval: 2,
        title: {{
            text: 'X Position (units)',
            style: {{ fontSize: '52px', color: '#306998', fontWeight: 'bold' }},
            margin: 50
        }},
        labels: {{
            style: {{ fontSize: '48px' }},
            format: '{{value}}'
        }},
        gridLineWidth: 2,
        gridLineColor: 'rgba(0, 0, 0, 0.12)'
    }},
    yAxis: {{
        min: -5,
        max: 5,
        tickInterval: 2,
        title: {{
            text: 'Y Position (units)',
            style: {{ fontSize: '52px', color: '#306998', fontWeight: 'bold' }},
            margin: 50
        }},
        labels: {{
            style: {{ fontSize: '48px' }},
            format: '{{value}}'
        }},
        gridLineWidth: 2,
        gridLineColor: 'rgba(0, 0, 0, 0.12)'
    }},
    zAxis: {{
        min: -4,
        max: 6,
        tickInterval: 2,
        title: {{
            text: 'Z Position (units)',
            style: {{ fontSize: '52px', color: '#306998', fontWeight: 'bold' }},
            margin: 50
        }},
        labels: {{
            style: {{ fontSize: '48px' }},
            format: '{{value}}'
        }},
        gridLineWidth: 2,
        gridLineColor: 'rgba(0, 0, 0, 0.12)'
    }},
    legend: {{
        enabled: true,
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle',
        x: -40,
        y: 0,
        itemStyle: {{
            fontSize: '48px',
            fontWeight: 'normal'
        }},
        symbolRadius: 12,
        symbolHeight: 32,
        symbolWidth: 32,
        itemMarginBottom: 25
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
                radius: 14,
                opacity: 0.8
            }},
            states: {{
                hover: {{
                    enabled: true,
                    marker: {{
                        radius: 18
                    }}
                }},
                inactive: {{
                    opacity: 0.6
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
