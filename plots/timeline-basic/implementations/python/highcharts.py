""" anyplot.ai
timeline-basic: Event Timeline
Library: highcharts unknown | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-11
"""

import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette - first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data - Software project milestones
events = [
    {"date": datetime(2024, 1, 15), "event": "Project Kickoff", "category": "Planning"},
    {"date": datetime(2024, 2, 1), "event": "Requirements Complete", "category": "Planning"},
    {"date": datetime(2024, 3, 10), "event": "Architecture Review", "category": "Design"},
    {"date": datetime(2024, 4, 5), "event": "Prototype Demo", "category": "Development"},
    {"date": datetime(2024, 5, 20), "event": "Alpha Release", "category": "Development"},
    {"date": datetime(2024, 6, 15), "event": "Beta Testing Start", "category": "Testing"},
    {"date": datetime(2024, 7, 30), "event": "Security Audit", "category": "Testing"},
    {"date": datetime(2024, 9, 1), "event": "UAT Complete", "category": "Release"},
    {"date": datetime(2024, 10, 15), "event": "Production Launch", "category": "Release"},
    {"date": datetime(2024, 11, 30), "event": "Post-Launch Review", "category": "Release"},
]

category_order = ["Planning", "Design", "Development", "Testing", "Release"]
category_colors = {cat: IMPRINT[i] for i, cat in enumerate(category_order)}

# Build series data for each category
series_data = {cat: [] for cat in category_colors}
for i, e in enumerate(events):
    timestamp = int(e["date"].timestamp() * 1000)
    y_pos = 1.0 if i % 2 == 0 else -1.0
    label_y = -45 if i % 2 == 0 else 65
    series_data[e["category"]].append({"x": timestamp, "y": y_pos, "name": e["event"], "label_y": label_y})

# Build series JavaScript
series_js_parts = []
for cat in category_order:
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
                    style: {{fontSize: "32px", fontWeight: "bold", color: "{INK}", textOutline: "3px {PAGE_BG}"}},
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
            marker: {{radius: 28, symbol: "circle", lineWidth: 4, lineColor: "{PAGE_BG}"}},
            showInLegend: true
        }}"""
        )

series_js = ",".join(series_js_parts)

# Download Highcharts JS from jsDelivr (more reliable CDN)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11.4.0/highcharts.js"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
response = requests.get(highcharts_url, headers=headers, timeout=30)
response.raise_for_status()
highcharts_js = response.text

# Generate HTML with inline script
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    Highcharts.chart('container', {{
        chart: {{
            type: 'scatter',
            width: 4800,
            height: 2700,
            backgroundColor: '{PAGE_BG}',
            marginTop: 160,
            marginBottom: 200,
            marginLeft: 100,
            marginRight: 200
        }},
        title: {{
            text: 'timeline-basic · highcharts · anyplot.ai',
            style: {{fontSize: '28px', fontWeight: 'bold', color: '{INK}'}},
            y: 60
        }},
        subtitle: {{
            text: 'Software Development Project Milestones 2024',
            style: {{fontSize: '22px', color: '{INK_SOFT}'}},
            y: 120
        }},
        xAxis: {{
            type: 'datetime',
            title: {{text: 'Timeline', style: {{fontSize: '22px', color: '{INK}'}}}},
            lineWidth: 3,
            lineColor: '{INK_SOFT}',
            tickWidth: 0,
            labels: {{
                style: {{fontSize: '18px', color: '{INK_SOFT}'}},
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
            title: {{text: 'Event Position', style: {{fontSize: '22px', color: '{INK}'}}}},
            labels: {{enabled: false}},
            gridLineWidth: 0,
            lineWidth: 0,
            min: -2.5,
            max: 2.5,
            plotLines: [{{color: '{INK_SOFT}', width: 3, value: 0, zIndex: 5}}]
        }},
        legend: {{
            enabled: true,
            layout: 'horizontal',
            align: 'center',
            verticalAlign: 'top',
            floating: true,
            backgroundColor: '{ELEVATED_BG}',
            borderColor: '{INK_SOFT}',
            borderWidth: 1,
            borderRadius: 4,
            y: 160,
            itemStyle: {{fontSize: '18px', fontWeight: 'normal', color: '{INK_SOFT}'}},
            symbolRadius: 10,
            symbolHeight: 20,
            symbolWidth: 20,
            itemDistance: 50
        }},
        tooltip: {{
            enabled: true,
            style: {{fontSize: '18px', color: '{INK}'}},
            headerFormat: '',
            pointFormat: '<b>{{point.name}}</b><br/>{{point.x:%b %d, %Y}}',
            backgroundColor: '{ELEVATED_BG}',
            borderColor: '{INK_SOFT}',
            borderWidth: 1
        }},
        plotOptions: {{
            scatter: {{
                marker: {{radius: 28, symbol: 'circle', lineWidth: 4, lineColor: '{PAGE_BG}'}},
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

# Write temp HTML and take screenshot for PNG
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
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML artifact for interactive version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
