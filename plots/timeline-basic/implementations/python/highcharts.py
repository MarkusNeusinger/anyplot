""" pyplots.ai
timeline-basic: Event Timeline
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-29
"""

import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Software project milestones
events = [
    {"date": datetime(2024, 1, 15), "event": "Project Kickoff", "category": "Planning"},
    {"date": datetime(2024, 2, 1), "event": "Requirements Complete", "category": "Planning"},
    {"date": datetime(2024, 3, 10), "event": "Architecture Review", "category": "Design"},
    {"date": datetime(2024, 4, 5), "event": "Prototype Demo", "category": "Development"},
    {"date": datetime(2024, 5, 20), "event": "Alpha Release", "category": "Development"},
    {"date": datetime(2024, 6, 15), "event": "Beta Testing Start", "category": "Testing"},
    {"date": datetime(2024, 7, 30), "event": "Security Audit", "category": "Testing"},
    {"date": datetime(2024, 9, 1), "event": "UAT Complete", "category": "Testing"},
    {"date": datetime(2024, 10, 15), "event": "Production Launch", "category": "Release"},
    {"date": datetime(2024, 11, 30), "event": "Post-Launch Review", "category": "Release"},
]

# Category colors - colorblind-safe palette
category_colors = {
    "Planning": "#306998",  # Python Blue
    "Design": "#FFD43B",  # Python Yellow
    "Development": "#9467BD",  # Purple
    "Testing": "#17BECF",  # Cyan
    "Release": "#8C564B",  # Brown
}

# Build series data for each category
series_data = {cat: [] for cat in category_colors}
for i, e in enumerate(events):
    timestamp = int(e["date"].timestamp() * 1000)  # JS timestamp in ms
    y_pos = 1.0 if i % 2 == 0 else -1.0  # Alternate above/below axis
    label_y = -45 if i % 2 == 0 else 65  # Label offset
    series_data[e["category"]].append({"x": timestamp, "y": y_pos, "name": e["event"], "label_y": label_y})

# Build series JavaScript
series_js_parts = []
for cat in ["Planning", "Design", "Development", "Testing", "Release"]:
    if series_data[cat]:
        color = category_colors[cat]
        points_js = []
        for p in series_data[cat]:
            points_js.append(
                f"""{{
                x: {p["x"]},
                y: {p["y"]},
                name: "{p["name"]}",
                dataLabels: {{
                    enabled: true,
                    format: "{p["name"]}",
                    style: {{fontSize: "32px", fontWeight: "bold", color: "#333333", textOutline: "3px white"}},
                    y: {p["label_y"]},
                    align: "center"
                }}
            }}"""
            )
        series_js_parts.append(
            f"""{{
            name: "{cat}",
            color: "{color}",
            data: [{",".join(points_js)}],
            marker: {{radius: 28, symbol: "circle", lineWidth: 4, lineColor: "#ffffff"}},
            showInLegend: true
        }}"""
        )

series_js = ",".join(series_js_parts)

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline script
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    Highcharts.chart('container', {{
        chart: {{
            type: 'scatter',
            width: 4800,
            height: 2700,
            backgroundColor: '#ffffff',
            marginTop: 160,
            marginBottom: 300,
            marginLeft: 100,
            marginRight: 200
        }},
        title: {{
            text: 'timeline-basic · highcharts · pyplots.ai',
            style: {{fontSize: '56px', fontWeight: 'bold'}},
            y: 60
        }},
        subtitle: {{
            text: 'Software Development Project Milestones 2024',
            style: {{fontSize: '36px', color: '#666666'}},
            y: 120
        }},
        xAxis: {{
            type: 'datetime',
            title: {{text: null}},
            lineWidth: 6,
            lineColor: '#333333',
            tickWidth: 0,
            labels: {{
                style: {{fontSize: '32px'}},
                format: '{{value:%b %Y}}',
                y: 40,
                step: 1
            }},
            gridLineWidth: 0,
            tickInterval: 30 * 24 * 3600 * 1000,
            min: Date.UTC(2023, 11, 1),
            max: Date.UTC(2025, 1, 1)
        }},
        yAxis: {{
            title: {{text: null}},
            labels: {{enabled: false}},
            gridLineWidth: 0,
            lineWidth: 0,
            min: -2.5,
            max: 2.5,
            plotLines: [{{color: '#333333', width: 6, value: 0, zIndex: 5}}]
        }},
        legend: {{
            enabled: true,
            layout: 'horizontal',
            align: 'center',
            verticalAlign: 'top',
            floating: true,
            backgroundColor: 'transparent',
            borderWidth: 0,
            y: 160,
            itemStyle: {{fontSize: '28px', fontWeight: 'normal', color: '#333333'}},
            symbolRadius: 10,
            symbolHeight: 20,
            symbolWidth: 20,
            itemDistance: 50
        }},
        tooltip: {{
            enabled: true,
            style: {{fontSize: '20px'}},
            headerFormat: '',
            pointFormat: '<b>{{point.name}}</b><br/>{{point.x:%b %d, %Y}}'
        }},
        plotOptions: {{
            scatter: {{
                marker: {{radius: 28, symbol: 'circle', lineWidth: 4, lineColor: '#ffffff'}},
                dataLabels: {{enabled: true, allowOverlap: false}},
                showInLegend: true
            }}
        }},
        credits: {{enabled: false}},
        series: [{series_js}]
    }});
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
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Take screenshot of the container element
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Build series for HTML (smaller sizes for responsive display)
html_series_js_parts = []
for cat in ["Planning", "Design", "Development", "Testing", "Release"]:
    if series_data[cat]:
        color = category_colors[cat]
        points_js = []
        for p in series_data[cat]:
            points_js.append(
                f"""{{
                x: {p["x"]},
                y: {p["y"]},
                name: "{p["name"]}",
                dataLabels: {{
                    enabled: true,
                    format: "{p["name"]}",
                    style: {{fontSize: "12px", fontWeight: "bold", color: "#333333"}},
                    y: {p["label_y"] // 4},
                    align: "center"
                }}
            }}"""
            )
        html_series_js_parts.append(
            f"""{{
            name: "{cat}",
            color: "{color}",
            data: [{",".join(points_js)}],
            marker: {{radius: 8, symbol: "circle", lineWidth: 2, lineColor: "#ffffff"}}
        }}"""
        )
html_series_js = ",".join(html_series_js_parts)

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    html_output = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>timeline-basic · highcharts · pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
    Highcharts.chart('container', {{
        chart: {{
            type: 'scatter',
            backgroundColor: '#ffffff'
        }},
        title: {{
            text: 'timeline-basic · highcharts · pyplots.ai',
            style: {{fontSize: '24px', fontWeight: 'bold'}}
        }},
        subtitle: {{
            text: 'Software Development Project Milestones 2024',
            style: {{fontSize: '16px', color: '#666666'}}
        }},
        xAxis: {{
            type: 'datetime',
            title: {{text: null}},
            lineWidth: 2,
            lineColor: '#333333',
            labels: {{
                format: '{{value:%b %Y}}'
            }},
            gridLineWidth: 0,
            tickInterval: 30 * 24 * 3600 * 1000,
            min: Date.UTC(2024, 0, 1),
            max: Date.UTC(2024, 11, 31)
        }},
        yAxis: {{
            title: {{text: null}},
            labels: {{enabled: false}},
            gridLineWidth: 0,
            lineWidth: 0,
            min: -2.5,
            max: 2.5,
            plotLines: [{{color: '#333333', width: 2, value: 0, zIndex: 5}}]
        }},
        legend: {{
            enabled: true,
            align: 'center',
            verticalAlign: 'bottom'
        }},
        tooltip: {{
            headerFormat: '',
            pointFormat: '<b>{{point.name}}</b><br/>{{point.x:%b %d, %Y}}'
        }},
        plotOptions: {{
            scatter: {{
                marker: {{radius: 8, symbol: 'circle', lineWidth: 2, lineColor: '#ffffff'}},
                dataLabels: {{enabled: true, allowOverlap: false}}
            }}
        }},
        credits: {{enabled: false}},
        series: [{html_series_js}]
    }});
    </script>
</body>
</html>"""
    f.write(html_output)
