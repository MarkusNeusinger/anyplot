""" pyplots.ai
circlepacking-basic: Circle Packing Chart
Library: highcharts unknown | Python 3.13.11
Quality: 82/100 | Created: 2025-12-30
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Software project structure with lines of code
# Hierarchical structure: Project -> Modules -> Components
# Using packedbubble with splitSeries for circle packing visualization
# Each series represents a parent category, bubbles are children packed inside

series_data = [
    {
        "name": "Frontend",
        "color": "#306998",
        "data": [
            {"name": "Components", "value": 8500},
            {"name": "Pages", "value": 6200},
            {"name": "Styles", "value": 3800},
            {"name": "Hooks", "value": 2100},
            {"name": "Assets", "value": 1200},
        ],
    },
    {
        "name": "Backend",
        "color": "#FFD43B",
        "data": [
            {"name": "Services", "value": 7200},
            {"name": "API Routes", "value": 5400},
            {"name": "Database", "value": 4500},
            {"name": "Models", "value": 3100},
            {"name": "Middleware", "value": 1800},
        ],
    },
    {
        "name": "Shared",
        "color": "#9467BD",
        "data": [
            {"name": "Utilities", "value": 2800},
            {"name": "Types", "value": 1500},
            {"name": "Constants", "value": 800},
        ],
    },
]

# Convert to JSON format for JavaScript
series_json = json.dumps(series_data)

# Highcharts configuration for packedbubble (circle packing) chart
# splitSeries creates parent bubbles that contain child bubbles - achieving the nested circle effect
highcharts_config = f"""{{
    chart: {{
        type: 'packedbubble',
        width: 3600,
        height: 3600,
        backgroundColor: '#ffffff',
        spacing: [60, 60, 60, 60]
    }},
    title: {{
        text: 'circlepacking-basic · highcharts · pyplots.ai',
        style: {{ fontSize: '56px', fontWeight: 'bold', color: '#333333' }},
        margin: 40
    }},
    subtitle: {{
        text: 'Software Project Structure by Lines of Code',
        style: {{ fontSize: '36px', color: '#666666' }}
    }},
    credits: {{ enabled: false }},
    legend: {{
        enabled: true,
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle',
        x: -40,
        itemStyle: {{ fontSize: '36px', fontWeight: '600' }},
        symbolRadius: 24,
        symbolHeight: 36,
        symbolWidth: 36,
        itemMarginTop: 20,
        itemMarginBottom: 20,
        backgroundColor: 'rgba(255,255,255,0.9)',
        borderWidth: 2,
        borderColor: '#cccccc',
        padding: 20
    }},
    tooltip: {{
        useHTML: true,
        pointFormat: '<b>{{point.name}}</b><br/>Lines of Code: {{point.value:,.0f}}',
        style: {{ fontSize: '28px' }}
    }},
    plotOptions: {{
        packedbubble: {{
            minSize: '30%',
            maxSize: '80%',
            zMin: 0,
            zMax: 10000,
            layoutAlgorithm: {{
                gravitationalConstant: 0.02,
                splitSeries: true,
                seriesInteraction: false,
                dragBetweenSeries: false,
                parentNodeLimit: true,
                bubblePadding: 15,
                parentNodeOptions: {{
                    marker: {{
                        fillColor: null,
                        fillOpacity: 0.15,
                        lineWidth: 5,
                        lineColor: null
                    }}
                }}
            }},
            dataLabels: {{
                enabled: true,
                format: '{{point.name}}',
                style: {{
                    color: 'white',
                    textOutline: '3px #333333',
                    fontWeight: '700',
                    fontSize: '32px'
                }},
                filter: {{
                    property: 'value',
                    operator: '>',
                    value: 2000
                }}
            }},
            marker: {{
                fillOpacity: 0.85,
                lineWidth: 3,
                lineColor: '#ffffff'
            }}
        }}
    }},
    series: {series_json}
}}"""

# Download Highcharts JS and highcharts-more for packedbubble
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts for PNG export
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
        Highcharts.chart('container', {highcharts_config});
    </script>
</body>
</html>"""

# Write temp HTML for PNG screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive HTML with CDN links
with open("plot.html", "w", encoding="utf-8") as f:
    html_standalone = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>circlepacking-basic · highcharts · pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
</head>
<body style="margin:0; padding:20px; background:#ffffff;">
    <div id="container" style="width: 100%; height: 90vh; min-height: 600px;"></div>
    <script>
        Highcharts.chart('container', {{
            chart: {{
                type: 'packedbubble',
                height: '100%',
                backgroundColor: '#ffffff'
            }},
            title: {{
                text: 'circlepacking-basic · highcharts · pyplots.ai',
                style: {{ fontSize: '24px', fontWeight: 'bold' }}
            }},
            subtitle: {{
                text: 'Software Project Structure by Lines of Code'
            }},
            credits: {{ enabled: false }},
            tooltip: {{
                useHTML: true,
                pointFormat: '<b>{{point.name}}</b>: {{point.value:,.0f}} lines of code'
            }},
            plotOptions: {{
                packedbubble: {{
                    minSize: '30%',
                    maxSize: '100%',
                    layoutAlgorithm: {{
                        gravitationalConstant: 0.05,
                        splitSeries: true,
                        seriesInteraction: false,
                        dragBetweenSeries: false,
                        parentNodeLimit: true
                    }},
                    dataLabels: {{
                        enabled: true,
                        format: '{{point.name}}',
                        style: {{ color: 'white', textOutline: '1px #333', fontWeight: '600' }},
                        filter: {{ property: 'value', operator: '>', value: 1500 }}
                    }}
                }}
            }},
            series: {series_json}
        }});
    </script>
</body>
</html>"""
    f.write(html_standalone)

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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
