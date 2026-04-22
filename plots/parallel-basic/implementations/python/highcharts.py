""" pyplots.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: highcharts unknown | Python 3.13.11
Quality: 97/100 | Created: 2025-12-23
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Iris dataset with 4 dimensions (sample for 3 species)
# Setosa: smaller petals, medium sepals
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

# Versicolor: medium everything
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

# Virginica: larger petals
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

# Download required Highcharts modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

parallel_url = "https://code.highcharts.com/modules/parallel-coordinates.js"
with urllib.request.urlopen(parallel_url, timeout=30) as response:
    parallel_js = response.read().decode("utf-8")

# Build series - each data point becomes a line in parallel coordinates
# Group by species with showInLegend flag to avoid duplicate legend entries
series_config = []

# Add Setosa series (Python Blue)
for i, row in enumerate(setosa_data):
    series_config.append({"name": "Setosa", "data": row, "color": "rgba(48, 105, 152, 0.7)", "showInLegend": i == 0})

# Add Versicolor series (Python Yellow)
for i, row in enumerate(versicolor_data):
    series_config.append(
        {"name": "Versicolor", "data": row, "color": "rgba(255, 212, 59, 0.7)", "showInLegend": i == 0}
    )

# Add Virginica series (Purple - colorblind safe)
for i, row in enumerate(virginica_data):
    series_config.append(
        {"name": "Virginica", "data": row, "color": "rgba(148, 103, 189, 0.7)", "showInLegend": i == 0}
    )

# Build chart config as JavaScript
series_json = json.dumps(series_config)

chart_config = f"""
Highcharts.chart('container', {{
    chart: {{
        type: 'line',
        parallelCoordinates: true,
        parallelAxes: {{
            lineWidth: 3
        }},
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        marginBottom: 200,
        marginTop: 150,
        marginLeft: 150,
        marginRight: 150
    }},
    title: {{
        text: 'Iris Dataset · parallel-basic · highcharts · pyplots.ai',
        style: {{
            fontSize: '72px',
            fontWeight: 'bold'
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
            fontSize: '44px'
        }},
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
                fontWeight: 'bold'
            }},
            y: 50
        }},
        lineWidth: 0
    }},
    yAxis: [{{
        min: 4,
        max: 8,
        labels: {{
            style: {{ fontSize: '32px' }},
            x: -15
        }}
    }}, {{
        min: 2,
        max: 4.5,
        labels: {{
            style: {{ fontSize: '32px' }},
            x: -15
        }}
    }}, {{
        min: 1,
        max: 7,
        labels: {{
            style: {{ fontSize: '32px' }},
            x: -15
        }}
    }}, {{
        min: 0,
        max: 3,
        labels: {{
            style: {{ fontSize: '32px' }},
            x: -15
        }}
    }}],
    credits: {{
        enabled: false
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
    <script>{parallel_js}</script>
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
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

# Take screenshot of just the chart container element
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file

# Also save HTML for interactive version
interactive_html = (
    """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/parallel-coordinates.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
"""
    + chart_config
    + """
    </script>
</body>
</html>"""
)

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(interactive_html)
