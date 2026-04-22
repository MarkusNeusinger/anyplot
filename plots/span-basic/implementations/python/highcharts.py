""" pyplots.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: highcharts unknown | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Monthly stock price with recession period highlighted
months = [
    "Jan 2007",
    "Apr 2007",
    "Jul 2007",
    "Oct 2007",
    "Jan 2008",
    "Apr 2008",
    "Jul 2008",
    "Oct 2008",
    "Jan 2009",
    "Apr 2009",
    "Jul 2009",
    "Oct 2009",
    "Jan 2010",
    "Apr 2010",
    "Jul 2010",
    "Oct 2010",
]
prices = [145, 152, 158, 155, 148, 135, 125, 95, 85, 78, 88, 105, 115, 122, 128, 135]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "spacingBottom": 20,
}

# Title
chart.options.title = {
    "text": "span-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Stock Price with Recession Period Highlighted", "style": {"fontSize": "48px"}}

# X-axis with categories
chart.options.x_axis = {
    "categories": months,
    "title": {"text": "Date", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    # Vertical span - highlight recession period (indices 4-8, Jan 2008 - Jan 2009)
    "plotBands": [
        {
            "from": 4,
            "to": 8,
            "color": "rgba(48, 105, 152, 0.25)",
            "label": {
                "text": "Recession Period",
                "style": {"fontSize": "42px", "color": "#306998", "fontWeight": "bold"},
                "verticalAlign": "top",
                "y": 60,
            },
        }
    ],
}

# Y-axis with horizontal span for threshold zone
chart.options.y_axis = {
    "title": {"text": "Stock Price ($)", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "min": 50,
    "max": 180,
    # Horizontal span - highlight danger zone below $100
    "plotBands": [
        {
            "from": 50,
            "to": 100,
            "color": "rgba(255, 212, 59, 0.25)",
            "label": {
                "text": "Below Target Price",
                "style": {"fontSize": "36px", "color": "#B8860B"},
                "align": "left",
                "x": 50,
            },
        }
    ],
}

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "36px"}}

# Plot options
chart.options.plot_options = {"line": {"lineWidth": 6, "marker": {"radius": 12, "enabled": True}}}

# Add line series
series = LineSeries()
series.name = "Stock Price"
series.data = prices
series.color = "#306998"
series.marker = {"fillColor": "#306998", "lineColor": "#306998", "lineWidth": 2}

chart.add_series(series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

# Save HTML file for interactive viewing
Path("plot.html").write_text(html_content, encoding="utf-8")

# Clean up temp file
Path(temp_path).unlink()
