""" anyplot.ai
gantt-basic: Basic Gantt Chart
Library: highcharts unknown | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-10
"""

import os
import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Project tasks with start/end dates and categories
tasks = [
    {
        "name": "Requirements Analysis",
        "start": datetime(2025, 1, 6),
        "end": datetime(2025, 1, 17),
        "category": "Planning",
    },
    {"name": "System Design", "start": datetime(2025, 1, 13), "end": datetime(2025, 1, 31), "category": "Planning"},
    {"name": "Database Schema", "start": datetime(2025, 1, 27), "end": datetime(2025, 2, 7), "category": "Development"},
    {"name": "Backend API", "start": datetime(2025, 2, 3), "end": datetime(2025, 3, 7), "category": "Development"},
    {"name": "Frontend UI", "start": datetime(2025, 2, 10), "end": datetime(2025, 3, 14), "category": "Development"},
    {"name": "Integration", "start": datetime(2025, 3, 10), "end": datetime(2025, 3, 21), "category": "Development"},
    {"name": "Unit Testing", "start": datetime(2025, 2, 17), "end": datetime(2025, 3, 14), "category": "Testing"},
    {"name": "System Testing", "start": datetime(2025, 3, 17), "end": datetime(2025, 3, 28), "category": "Testing"},
    {"name": "User Acceptance", "start": datetime(2025, 3, 24), "end": datetime(2025, 4, 4), "category": "Testing"},
    {"name": "Documentation", "start": datetime(2025, 3, 3), "end": datetime(2025, 3, 28), "category": "Deployment"},
    {"name": "Training", "start": datetime(2025, 3, 31), "end": datetime(2025, 4, 11), "category": "Deployment"},
    {"name": "Go Live", "start": datetime(2025, 4, 14), "end": datetime(2025, 4, 18), "category": "Deployment"},
]

# Map categories to Okabe-Ito colors
category_colors = {
    "Planning": IMPRINT[0],  # #009E73
    "Development": IMPRINT[1],  # #C475FD
    "Testing": IMPRINT[2],  # #4467A3
    "Deployment": IMPRINT[3],  # #BD8233
}

task_names = [t["name"] for t in tasks]

# Download Highcharts JS from jsDelivr CDN
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
xrange_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/modules/xrange.js"

req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request(
    xrange_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    xrange_js = response.read().decode("utf-8")

# Build series data with timestamps
today_ts = int(datetime(2025, 2, 15).timestamp() * 1000)
series_data_planning = []
series_data_development = []
series_data_testing = []
series_data_deployment = []

for i, task in enumerate(tasks):
    point = {
        "x": int(task["start"].timestamp() * 1000),
        "x2": int(task["end"].timestamp() * 1000),
        "y": i,
        "name": task["name"],
    }
    if task["category"] == "Planning":
        series_data_planning.append(point)
    elif task["category"] == "Development":
        series_data_development.append(point)
    elif task["category"] == "Testing":
        series_data_testing.append(point)
    else:
        series_data_deployment.append(point)

# Format task names as JavaScript array
task_names_js = "[" + ",".join([f'"{name}"' for name in task_names]) + "]"

# Generate HTML with embedded JavaScript configuration
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{xrange_js}</script>
</head>
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {{
            chart: {{
                type: 'xrange',
                width: 4800,
                height: 2700,
                backgroundColor: '{PAGE_BG}',
                spacingBottom: 120,
                marginLeft: 360,
                marginTop: 150,
            }},
            colors: ['{IMPRINT[0]}', '{IMPRINT[1]}', '{IMPRINT[2]}', '{IMPRINT[3]}'],
            title: {{
                text: 'gantt-basic · highcharts · anyplot.ai',
                style: {{fontSize: '28px', fontWeight: 'bold', color: '{INK}'}},
                y: 40,
            }},
            xAxis: {{
                type: 'datetime',
                title: {{
                    text: 'Timeline',
                    style: {{fontSize: '22px', color: '{INK}'}}
                }},
                labels: {{style: {{fontSize: '18px', color: '{INK_SOFT}'}}}},
                lineColor: '{INK_SOFT}',
                tickColor: '{INK_SOFT}',
                gridLineWidth: 1,
                gridLineColor: '{GRID}',
                plotLines: [{{
                    value: {today_ts},
                    color: '#E53935',
                    width: 4,
                    zIndex: 10,
                    label: {{
                        text: 'Today (Feb 15)',
                        style: {{fontSize: '18px', color: '#E53935', fontWeight: 'bold'}},
                        rotation: 0,
                        align: 'center',
                        y: -20
                    }}
                }}]
            }},
            yAxis: {{
                type: 'category',
                categories: {task_names_js},
                title: {{
                    text: 'Tasks',
                    style: {{fontSize: '22px', color: '{INK}'}}
                }},
                labels: {{style: {{fontSize: '18px', color: '{INK_SOFT}'}}}},
                lineColor: '{INK_SOFT}',
                tickColor: '{INK_SOFT}',
                gridLineWidth: 1,
                gridLineColor: '{GRID}',
                reversed: true
            }},
            legend: {{
                enabled: true,
                align: 'center',
                verticalAlign: 'bottom',
                layout: 'horizontal',
                itemStyle: {{fontSize: '18px', color: '{INK_SOFT}'}},
                backgroundColor: '{ELEVATED_BG}',
                borderColor: '{INK_SOFT}',
                borderWidth: 1,
                symbolRadius: 6,
                symbolWidth: 60,
                symbolHeight: 30
            }},
            tooltip: {{
                headerFormat: '<span style="font-size: 18px; font-weight: bold;">{{point.key}}</span><br/>',
                pointFormat: '<span style="font-size: 16px; color: {{series.color}}">● {{series.name}}</span><br/><span style="font-size: 16px">{{point.x:%b %e}} - {{point.x2:%b %e, %Y}}</span>',
                style: {{fontSize: '16px', color: '{INK}'}},
                backgroundColor: '{ELEVATED_BG}',
                borderColor: '{INK_SOFT}',
                borderRadius: 6
            }},
            plotOptions: {{
                xrange: {{
                    pointWidth: 55,
                    borderRadius: 6,
                    borderWidth: 2,
                    borderColor: '{INK_SOFT}',
                    dataLabels: {{enabled: false}}
                }}
            }},
            series: [
                {{
                    name: 'Planning',
                    data: {str(series_data_planning)},
                    color: '{IMPRINT[0]}'
                }},
                {{
                    name: 'Development',
                    data: {str(series_data_development)},
                    color: '{IMPRINT[1]}'
                }},
                {{
                    name: 'Testing',
                    data: {str(series_data_testing)},
                    color: '{IMPRINT[2]}'
                }},
                {{
                    name: 'Deployment',
                    data: {str(series_data_deployment)},
                    color: '{IMPRINT[3]}'
                }}
            ],
            credits: {{enabled: false}}
        }});
    </script>
</body>
</html>"""

# Save HTML
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(10)

container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")

driver.quit()
Path(temp_path).unlink()
