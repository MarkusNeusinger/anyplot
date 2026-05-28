""" anyplot.ai
scatter-3d: 3D Scatter Plot
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-08
"""

import gzip
import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (from prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette - first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - 3D clustered data demonstrating spatial relationships
np.random.seed(42)

n_points_per_cluster = 50

# Cluster 1: centered at (2, 2, 2) - Okabe-Ito position 1 (green)
cluster1_x = np.random.randn(n_points_per_cluster) * 0.8 + 2
cluster1_y = np.random.randn(n_points_per_cluster) * 0.8 + 2
cluster1_z = np.random.randn(n_points_per_cluster) * 0.8 + 2

# Cluster 2: centered at (-2, -1, 3) - Okabe-Ito position 2 (orange)
cluster2_x = np.random.randn(n_points_per_cluster) * 0.7 - 2
cluster2_y = np.random.randn(n_points_per_cluster) * 0.7 - 1
cluster2_z = np.random.randn(n_points_per_cluster) * 0.7 + 3

# Cluster 3: centered at (0, -2, -1) - Okabe-Ito position 3 (blue)
cluster3_x = np.random.randn(n_points_per_cluster) * 0.9 + 0
cluster3_y = np.random.randn(n_points_per_cluster) * 0.9 - 2
cluster3_z = np.random.randn(n_points_per_cluster) * 0.9 - 1

# Download required Highcharts modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_3d_url = "https://code.highcharts.com/highcharts-3d.js"


def download_js(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.highcharts.com/",
            "Connection": "keep-alive",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read()
        if data[:2] == b"\x1f\x8b":  # gzip magic number
            data = gzip.decompress(data)
        return data.decode("utf-8")


highcharts_js = download_js(highcharts_url)
time.sleep(1)
highcharts_3d_js = download_js(highcharts_3d_url)

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

# Define series with Okabe-Ito colors
series_data = [
    {
        "type": "scatter3d",
        "name": "Cluster A",
        "data": cluster1_data,
        "color": IMPRINT[0],  # Green
        "marker": {"radius": 14, "symbol": "circle"},
    },
    {
        "type": "scatter3d",
        "name": "Cluster B",
        "data": cluster2_data,
        "color": IMPRINT[1],  # Orange
        "marker": {"radius": 14, "symbol": "circle"},
    },
    {
        "type": "scatter3d",
        "name": "Cluster C",
        "data": cluster3_data,
        "color": IMPRINT[2],  # Blue
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
        backgroundColor: '{PAGE_BG}',
        options3d: {{
            enabled: true,
            alpha: 15,
            beta: 25,
            depth: 700,
            viewDistance: 5,
            fitToPlot: true,
            frame: {{
                bottom: {{ size: 2, color: 'rgba(154,193,205,0.15)' }},
                back: {{ size: 2, color: 'rgba(154,193,205,0.10)' }},
                side: {{ size: 2, color: 'rgba(154,193,205,0.12)' }}
            }}
        }},
        marginTop: 150,
        marginBottom: 150,
        marginLeft: 120,
        marginRight: 120
    }},
    title: {{
        text: 'scatter-3d · highcharts · anyplot.ai',
        style: {{ fontSize: '28px', color: '{INK}', fontWeight: 'normal' }},
        y: 40
    }},
    xAxis: {{
        min: -5,
        max: 5,
        tickInterval: 2,
        title: {{
            text: 'X Position (units)',
            style: {{ fontSize: '22px', color: '{INK}', fontWeight: 'normal' }},
            margin: 30
        }},
        labels: {{
            style: {{ fontSize: '18px', color: '{INK_SOFT}' }},
            format: '{{value}}'
        }},
        lineColor: '{INK_SOFT}',
        tickColor: '{INK_SOFT}',
        gridLineColor: '{GRID}'
    }},
    yAxis: {{
        min: -5,
        max: 5,
        tickInterval: 2,
        title: {{
            text: 'Y Position (units)',
            style: {{ fontSize: '22px', color: '{INK}', fontWeight: 'normal' }},
            margin: 30
        }},
        labels: {{
            style: {{ fontSize: '18px', color: '{INK_SOFT}' }},
            format: '{{value}}'
        }},
        lineColor: '{INK_SOFT}',
        tickColor: '{INK_SOFT}',
        gridLineColor: '{GRID}'
    }},
    zAxis: {{
        min: -4,
        max: 6,
        tickInterval: 2,
        title: {{
            text: 'Z Position (units)',
            style: {{ fontSize: '22px', color: '{INK}', fontWeight: 'normal' }},
            margin: 30
        }},
        labels: {{
            style: {{ fontSize: '18px', color: '{INK_SOFT}' }},
            format: '{{value}}'
        }},
        lineColor: '{INK_SOFT}',
        tickColor: '{INK_SOFT}',
        gridLineColor: '{GRID}'
    }},
    legend: {{
        enabled: true,
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle',
        x: -80,
        y: 0,
        itemStyle: {{
            fontSize: '18px',
            color: '{INK_SOFT}'
        }},
        backgroundColor: '{ELEVATED_BG}',
        borderColor: '{INK_SOFT}',
        borderWidth: 1,
        symbolRadius: 8,
        symbolHeight: 20,
        symbolWidth: 20,
        itemMarginBottom: 15
    }},
    credits: {{
        enabled: false
    }},
    tooltip: {{
        enabled: true,
        headerFormat: '<b>{{series.name}}</b><br>',
        pointFormat: 'X: {{point.x:.2f}}<br>Y: {{point.y:.2f}}<br>Z: {{point.z:.2f}}',
        style: {{ fontSize: '16px', color: '{INK}' }},
        backgroundColor: '{ELEVATED_BG}'
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
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_config}</script>
</body>
</html>"""

# Save HTML artifact for interactive version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG artifact
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
time.sleep(6)  # Wait for 3D rendering

driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
