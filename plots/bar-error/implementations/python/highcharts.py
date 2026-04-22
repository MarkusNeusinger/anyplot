""" pyplots.ai
bar-error: Bar Chart with Error Bars
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-27
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Treatment comparison with ±1 SD error bars
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D"]
values = [42.3, 58.7, 51.2, 67.8, 45.9]
errors = [5.2, 7.1, 4.8, 8.3, 6.0]  # Standard deviation

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download highcharts-more.js for error bars
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 180,
    "style": {"fontFamily": "Arial, sans-serif"},
}

# Title
chart.options.title = {
    "text": "bar-error \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle explaining error bars
chart.options.subtitle = {
    "text": "Error bars represent \u00b11 Standard Deviation",
    "style": {"fontSize": "28px", "color": "#666666"},
}

# X-axis
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Treatment Group", "style": {"fontSize": "32px"}},
    "labels": {"style": {"fontSize": "26px"}},
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Response Value (units)", "style": {"fontSize": "32px"}},
    "labels": {"style": {"fontSize": "24px"}},
    "min": 0,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "24px"}, "symbolHeight": 20, "symbolWidth": 30}

# Plot options
chart.options.plot_options = {
    "column": {"pointPadding": 0.2, "borderWidth": 1, "borderColor": "#1a4d73"},
    "errorbar": {"whiskerLength": "60%", "whiskerWidth": 4, "stemWidth": 4, "color": "#333333"},
}

# Create column series
column_series = ColumnSeries()
column_series.name = "Mean Value"
column_series.data = values
column_series.color = "#306998"

# Add series to chart
chart.add_series(column_series)

# Generate HTML with inline Highcharts and error bar configuration
html_str = chart.to_js_literal()

# Build error bar data for Highcharts errorbar series
error_bar_data = [[v - e, v + e] for v, e in zip(values, errors, strict=True)]

# Create custom HTML with error bar series added
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {{
            chart: {{
                type: 'column',
                width: 4800,
                height: 2700,
                backgroundColor: '#ffffff',
                marginBottom: 300,
                marginLeft: 180,
                style: {{ fontFamily: 'Arial, sans-serif' }}
            }},
            title: {{
                text: 'bar-error \u00b7 highcharts \u00b7 pyplots.ai',
                style: {{ fontSize: '56px', fontWeight: 'bold' }}
            }},
            subtitle: {{
                text: 'Error bars represent \u00b11 Standard Deviation',
                style: {{ fontSize: '32px', color: '#666666' }}
            }},
            xAxis: {{
                categories: {categories},
                title: {{
                    text: 'Treatment Group',
                    style: {{ fontSize: '36px' }},
                    margin: 20
                }},
                labels: {{ style: {{ fontSize: '28px' }} }}
            }},
            yAxis: {{
                title: {{
                    text: 'Response Value (units)',
                    style: {{ fontSize: '36px' }},
                    margin: 20
                }},
                labels: {{ style: {{ fontSize: '26px' }} }},
                min: 0,
                gridLineWidth: 1,
                gridLineColor: '#e0e0e0',
                gridLineDashStyle: 'Dash'
            }},
            legend: {{
                enabled: true,
                itemStyle: {{ fontSize: '28px' }},
                symbolHeight: 24,
                symbolWidth: 36,
                align: 'right',
                verticalAlign: 'top',
                y: 80,
                x: -40
            }},
            plotOptions: {{
                column: {{
                    pointPadding: 0.2,
                    borderWidth: 2,
                    borderColor: '#1a4d73'
                }},
                errorbar: {{
                    whiskerLength: '50%',
                    whiskerWidth: 5,
                    stemWidth: 5,
                    color: '#333333'
                }}
            }},
            series: [{{
                name: 'Mean Value',
                type: 'column',
                data: {values},
                color: '#306998'
            }}, {{
                name: 'Error (\u00b11 SD)',
                type: 'errorbar',
                data: {error_bar_data},
                stemColor: '#333333',
                whiskerColor: '#333333'
            }}]
        }});
    </script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML file
Path("plot.html").write_text(html_content, encoding="utf-8")

# Setup Chrome options for headless rendering
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
