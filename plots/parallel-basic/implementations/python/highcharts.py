""" anyplot.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: highcharts unknown | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-27
"""

import json
import os
import tempfile
import time
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

# Data - Iris dataset with 4 dimensions (sepal length, sepal width, petal length, petal width)
setosa_data = [
    [5.0, 3.4, 1.4, 0.2],
    [4.9, 3.1, 1.5, 0.1],
    [4.7, 3.2, 1.3, 0.2],
    [4.6, 3.1, 1.5, 0.2],
    [5.0, 3.6, 1.4, 0.2],
    [5.4, 3.9, 1.7, 0.4],
    [4.6, 3.4, 1.4, 0.3],
    [5.0, 3.4, 1.5, 0.2],
    [4.4, 2.9, 1.4, 0.2],
    [4.9, 3.1, 1.5, 0.1],
]

versicolor_data = [
    [7.0, 3.2, 4.7, 1.4],
    [6.4, 3.2, 4.5, 1.5],
    [6.9, 3.1, 4.9, 1.5],
    [5.5, 2.3, 4.0, 1.3],
    [6.5, 2.8, 4.6, 1.5],
    [5.7, 2.8, 4.5, 1.3],
    [6.3, 3.3, 4.7, 1.6],
    [4.9, 2.4, 3.3, 1.0],
    [6.6, 2.9, 4.6, 1.3],
    [5.2, 2.7, 3.9, 1.4],
]

virginica_data = [
    [6.3, 3.3, 6.0, 2.5],
    [5.8, 2.7, 5.1, 1.9],
    [7.1, 3.0, 5.9, 2.1],
    [6.3, 2.9, 5.6, 1.8],
    [6.5, 3.0, 5.8, 2.2],
    [7.6, 3.0, 6.6, 2.1],
    [4.9, 2.5, 4.5, 1.7],
    [7.3, 2.9, 6.3, 1.8],
    [6.7, 2.5, 5.8, 1.8],
    [7.2, 3.6, 6.1, 2.5],
]

# Build series — Okabe-Ito palette: first series always #009E73
series_config = []
for i, row in enumerate(setosa_data):
    series_config.append({"name": "Setosa", "data": row, "color": "rgba(0,158,115,0.65)", "showInLegend": i == 0})
for i, row in enumerate(versicolor_data):
    series_config.append({"name": "Versicolor", "data": row, "color": "rgba(213,94,0,0.65)", "showInLegend": i == 0})
for i, row in enumerate(virginica_data):
    series_config.append({"name": "Virginica", "data": row, "color": "rgba(0,114,178,0.65)", "showInLegend": i == 0})

# Load Highcharts modules from local npm install (CDN blocked in headless Chrome on file://)
hc_base = Path("/tmp/hc/node_modules/highcharts")
highcharts_js = (hc_base / "highcharts.js").read_text(encoding="utf-8")
parallel_js = (hc_base / "modules/parallel-coordinates.js").read_text(encoding="utf-8")

series_json = json.dumps(series_config)

chart_config = f"""
Highcharts.chart('container', {{
    chart: {{
        type: 'line',
        parallelCoordinates: true,
        parallelAxes: {{
            lineWidth: 3,
            lineColor: '{INK_SOFT}',
            gridLineColor: '{GRID}',
            labels: {{
                style: {{
                    color: '{INK_SOFT}',
                    fontSize: '32px'
                }}
            }}
        }},
        width: 4800,
        height: 2700,
        backgroundColor: '{PAGE_BG}',
        marginBottom: 200,
        marginTop: 150,
        marginLeft: 150,
        marginRight: 150
    }},
    title: {{
        text: 'Iris Dataset · parallel-basic · highcharts · anyplot.ai',
        style: {{
            fontSize: '72px',
            fontWeight: 'bold',
            color: '{INK}'
        }}
    }},
    plotOptions: {{
        series: {{
            lineWidth: 4,
            marker: {{
                enabled: false
            }},
            animation: false,
            states: {{
                hover: {{
                    lineWidth: 6
                }},
                inactive: {{
                    opacity: 0.7
                }}
            }}
        }}
    }},
    legend: {{
        enabled: true,
        align: 'center',
        verticalAlign: 'bottom',
        layout: 'horizontal',
        itemStyle: {{
            fontSize: '44px',
            color: '{INK_SOFT}'
        }},
        backgroundColor: '{ELEVATED_BG}',
        borderColor: '{INK_SOFT}',
        borderWidth: 1,
        symbolWidth: 80,
        symbolHeight: 25,
        itemDistance: 80
    }},
    tooltip: {{
        pointFormat: '<span style="color:{{point.color}}">\\u25CF</span>' +
            '{{series.name}}: <b>{{point.formattedValue}}</b><br/>'
    }},
    xAxis: {{
        categories: ['Sepal Length (cm)', 'Sepal Width (cm)', 'Petal Length (cm)', 'Petal Width (cm)'],
        offset: 10,
        labels: {{
            style: {{
                fontSize: '40px',
                fontWeight: 'bold',
                color: '{INK}'
            }},
            y: 50
        }},
        lineColor: '{INK_SOFT}',
        lineWidth: 0
    }},
    yAxis: [{{
        min: 4,
        max: 8,
        labels: {{
            style: {{ fontSize: '32px', color: '{INK_SOFT}' }},
            x: -15
        }}
    }}, {{
        min: 2,
        max: 4.5,
        labels: {{
            style: {{ fontSize: '32px', color: '{INK_SOFT}' }},
            x: -15
        }}
    }}, {{
        min: 1,
        max: 7,
        labels: {{
            style: {{ fontSize: '32px', color: '{INK_SOFT}' }},
            x: -15
        }}
    }}, {{
        min: 0,
        max: 3,
        labels: {{
            style: {{ fontSize: '32px', color: '{INK_SOFT}' }},
            x: -15
        }}
    }}],
    credits: {{
        enabled: false
    }},
    series: {series_json}
}});
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{parallel_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_config}</script>
</body>
</html>"""

# Save HTML artifact for the site
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and screenshot for PNG artifact
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
