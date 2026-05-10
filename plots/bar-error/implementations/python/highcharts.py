"""anyplot.ai
bar-error: Bar Chart with Error Bars
Library: highcharts | Python 3.13
Quality: 91 | Updated: 2025-05-10
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
BRAND = "#009E73"

# Data - Treatment comparison with ±1 SD error bars
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D"]
values = [42.3, 58.7, 51.2, 67.8, 45.9]
errors = [5.2, 7.1, 4.8, 8.3, 6.0]

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://code.highcharts.com/"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download highcharts-more.js for error bars
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
req_more = urllib.request.Request(
    highcharts_more_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://code.highcharts.com/"}
)
with urllib.request.urlopen(req_more, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Build error bar data for Highcharts errorbar series
error_bar_data = [[v - e, v + e] for v, e in zip(values, errors, strict=True)]

# Generate HTML with inline Highcharts and error bar configuration
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {{
            chart: {{
                type: 'column',
                width: 4800,
                height: 2700,
                backgroundColor: '{PAGE_BG}',
                marginBottom: 200,
                marginLeft: 180,
                style: {{ fontFamily: 'system-ui, -apple-system, sans-serif', color: '{INK}' }}
            }},
            title: {{
                text: 'bar-error · highcharts · anyplot.ai',
                style: {{ fontSize: '28px', fontWeight: '500', color: '{INK}' }}
            }},
            subtitle: {{
                text: 'Error bars represent ±1 Standard Deviation',
                style: {{ fontSize: '18px', color: '{INK_SOFT}' }}
            }},
            xAxis: {{
                categories: {categories},
                title: {{
                    text: 'Treatment Group',
                    style: {{ fontSize: '22px', color: '{INK}' }}
                }},
                labels: {{ style: {{ fontSize: '18px', color: '{INK_SOFT}' }} }},
                lineColor: '{INK_SOFT}',
                tickColor: '{INK_SOFT}'
            }},
            yAxis: {{
                title: {{
                    text: 'Response Value (units)',
                    style: {{ fontSize: '22px', color: '{INK}' }}
                }},
                labels: {{ style: {{ fontSize: '18px', color: '{INK_SOFT}' }} }},
                min: 0,
                gridLineWidth: 1,
                gridLineColor: '{GRID}'
            }},
            legend: {{
                enabled: true,
                backgroundColor: '{ELEVATED_BG}',
                borderColor: '{INK_SOFT}',
                borderWidth: 1,
                itemStyle: {{ fontSize: '18px', color: '{INK_SOFT}' }},
                symbolHeight: 18,
                symbolWidth: 24,
                align: 'right',
                verticalAlign: 'top',
                y: 60,
                x: -20
            }},
            plotOptions: {{
                column: {{
                    pointPadding: 0.2,
                    borderWidth: 0
                }},
                errorbar: {{
                    whiskerLength: '50%',
                    whiskerWidth: 4,
                    stemWidth: 4,
                    color: '{INK_SOFT}',
                    stemColor: '{INK_SOFT}',
                    whiskerColor: '{INK_SOFT}'
                }}
            }},
            series: [{{
                name: 'Mean Value',
                type: 'column',
                data: {values},
                color: '{BRAND}'
            }}, {{
                name: 'Error (±1 SD)',
                type: 'errorbar',
                data: {error_bar_data}
            }}]
        }});
    </script>
</body>
</html>"""

# Write HTML file
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Setup Chrome options for headless rendering
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
