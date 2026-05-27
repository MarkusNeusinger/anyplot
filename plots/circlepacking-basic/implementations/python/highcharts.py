""" anyplot.ai
circlepacking-basic: Circle Packing Chart
Library: highcharts unknown | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-11
"""

import json
import os
import tempfile
import time
import urllib.request
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

# Data: Company organizational structure across 3 hierarchy levels
# Root (Company) -> Departments -> Teams -> Team Members (40+ nodes total)
series_data = [
    {
        "name": "Engineering",
        "color": IMPRINT[0],
        "data": [
            {"name": "Frontend", "value": 8},
            {"name": "  - React Team", "value": 5},
            {"name": "  - UI Kit", "value": 3},
            {"name": "Backend", "value": 10},
            {"name": "  - API Services", "value": 6},
            {"name": "  - Database", "value": 4},
            {"name": "DevOps", "value": 6},
            {"name": "  - Infrastructure", "value": 4},
            {"name": "  - CI/CD", "value": 2},
            {"name": "QA", "value": 7},
            {"name": "  - Automation", "value": 4},
            {"name": "  - Manual Testing", "value": 3},
        ],
    },
    {
        "name": "Product",
        "color": IMPRINT[1],
        "data": [
            {"name": "Product Management", "value": 5},
            {"name": "  - Platform PM", "value": 2},
            {"name": "  - Growth PM", "value": 3},
            {"name": "Design", "value": 8},
            {"name": "  - UX/UI Design", "value": 5},
            {"name": "  - Design Systems", "value": 3},
            {"name": "Analytics", "value": 4},
            {"name": "  - Data Analytics", "value": 2},
            {"name": "  - BI Team", "value": 2},
        ],
    },
    {
        "name": "Operations",
        "color": IMPRINT[2],
        "data": [
            {"name": "Sales", "value": 9},
            {"name": "  - Enterprise", "value": 5},
            {"name": "  - SMB", "value": 4},
            {"name": "Marketing", "value": 7},
            {"name": "  - Content", "value": 3},
            {"name": "  - Demand Gen", "value": 4},
            {"name": "Customer Success", "value": 6},
            {"name": "  - Support", "value": 4},
            {"name": "  - Onboarding", "value": 2},
        ],
    },
]

# Convert to JSON format for JavaScript
series_json = json.dumps(series_data)

# Highcharts configuration for packedbubble (circle packing) chart
highcharts_config = f"""{{
    chart: {{
        type: 'packedbubble',
        width: 3600,
        height: 3600,
        backgroundColor: '{PAGE_BG}',
        spacing: [60, 60, 60, 60]
    }},
    title: {{
        text: 'circlepacking-basic · highcharts · anyplot.ai',
        style: {{ fontSize: '28px', fontWeight: '600', color: '{INK}' }},
        margin: 40
    }},
    subtitle: {{
        text: 'Company Organization Structure by Team Size',
        style: {{ fontSize: '22px', color: '{INK_SOFT}' }}
    }},
    credits: {{ enabled: false }},
    legend: {{
        enabled: true,
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle',
        x: -40,
        itemStyle: {{ fontSize: '18px', color: '{INK_SOFT}' }},
        symbolRadius: 12,
        symbolHeight: 14,
        symbolWidth: 14,
        itemMarginTop: 12,
        itemMarginBottom: 12,
        backgroundColor: '{ELEVATED_BG}',
        borderColor: '{INK_SOFT}',
        borderWidth: 1,
        padding: 16
    }},
    tooltip: {{
        useHTML: true,
        pointFormat: '<b>{{point.name}}</b><br/>Team Size: {{point.value}}',
        style: {{ fontSize: '16px', color: '{INK}' }},
        backgroundColor: '{ELEVATED_BG}',
        borderColor: '{INK_SOFT}'
    }},
    plotOptions: {{
        packedbubble: {{
            minSize: '25%',
            maxSize: '75%',
            zMin: 0,
            zMax: 10,
            layoutAlgorithm: {{
                gravitationalConstant: 0.02,
                splitSeries: true,
                seriesInteraction: false,
                dragBetweenSeries: false,
                parentNodeLimit: true,
                bubblePadding: 8,
                parentNodeOptions: {{
                    marker: {{
                        fillColor: null,
                        fillOpacity: 0.15,
                        lineWidth: 3,
                        lineColor: null
                    }}
                }}
            }},
            dataLabels: {{
                enabled: true,
                format: '{{point.name}}',
                style: {{
                    color: '#ffffff',
                    textOutline: '2px {INK}',
                    fontWeight: '600',
                    fontSize: '16px'
                }},
                filter: {{
                    property: 'value',
                    operator: '>',
                    value: 3
                }}
            }},
            marker: {{
                fillOpacity: 0.85,
                lineWidth: 2,
                lineColor: '{PAGE_BG}'
            }}
        }}
    }},
    series: {series_json}
}}"""

# Download Highcharts JS from unpkg CDN (more accessible)
highcharts_url = "https://unpkg.com/highcharts"
highcharts_more_url = "https://unpkg.com/highcharts/highcharts-more.js"

req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req_more = urllib.request.Request(
    highcharts_more_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req_more, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts for PNG export
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
        Highcharts.chart('container', {highcharts_config});
    </script>
</body>
</html>"""

# Save interactive HTML (both themes)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML for PNG screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Chrome options for headless rendering
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)  # Wait for packedbubble layout algorithm to complete
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
