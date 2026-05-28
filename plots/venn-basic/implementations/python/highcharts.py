""" anyplot.ai
venn-basic: Venn Diagram
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-11
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.venn import VennSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Download Highcharts JS and Venn module (required for headless Chrome)
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "text/javascript",
    "Referer": "https://www.highcharts.com/",
}

highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_req = urllib.request.Request(highcharts_url, headers=headers)
with urllib.request.urlopen(highcharts_req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

venn_url = "https://code.highcharts.com/modules/venn.js"
venn_req = urllib.request.Request(venn_url, headers=headers)
with urllib.request.urlopen(venn_req, timeout=30) as response:
    venn_js = response.read().decode("utf-8")

# Data: Three programming skill sets with realistic overlaps
# Set A: Backend developers, Set B: Frontend developers, Set C: DevOps engineers
venn_data = [
    {"sets": ["Backend"], "value": 100},
    {"sets": ["Frontend"], "value": 80},
    {"sets": ["DevOps"], "value": 60},
    {"sets": ["Backend", "Frontend"], "value": 30},
    {"sets": ["Backend", "DevOps"], "value": 20},
    {"sets": ["Frontend", "DevOps"], "value": 15},
    {"sets": ["Backend", "Frontend", "DevOps"], "value": 10},
]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings with theme-adaptive background
chart.options.chart = {"type": "venn", "width": 4800, "height": 2700, "backgroundColor": PAGE_BG, "marginBottom": 100}

# Title with theme-adaptive color
chart.options.title = {
    "text": "venn-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# Subtitle
chart.options.subtitle = {
    "text": "Developer Skill Distribution (Team of 150)",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# Create Venn series
series = VennSeries()
series.data = venn_data
series.name = "Team Skills"

# Series styling with theme-adaptive labels
series.data_labels = {
    "enabled": True,
    "style": {"fontSize": "20px", "fontWeight": "normal", "textOutline": "none", "color": INK},
    "format": "{point.name}: {point.value}",
}

# Use Okabe-Ito palette (first series #009E73)
chart.options.colors = IMPRINT

chart.add_series(series)

# Legend with theme-adaptive colors
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Accessibility
chart.options.accessibility = {"enabled": False}

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{venn_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML for the site
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
