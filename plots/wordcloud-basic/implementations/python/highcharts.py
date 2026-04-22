""" pyplots.ai
wordcloud-basic: Basic Word Cloud
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Technology terms and their frequency from a developer survey
# Words preprocessed: lowercase, common terms from survey responses
words_data = [
    {"name": "python", "weight": 150},
    {"name": "javascript", "weight": 142},
    {"name": "data", "weight": 128},
    {"name": "cloud", "weight": 115},
    {"name": "api", "weight": 108},
    {"name": "machine learning", "weight": 98},
    {"name": "database", "weight": 95},
    {"name": "security", "weight": 88},
    {"name": "docker", "weight": 82},
    {"name": "kubernetes", "weight": 78},
    {"name": "react", "weight": 75},
    {"name": "automation", "weight": 72},
    {"name": "devops", "weight": 68},
    {"name": "microservices", "weight": 65},
    {"name": "testing", "weight": 62},
    {"name": "agile", "weight": 58},
    {"name": "frontend", "weight": 55},
    {"name": "backend", "weight": 52},
    {"name": "scalability", "weight": 48},
    {"name": "typescript", "weight": 45},
    {"name": "git", "weight": 42},
    {"name": "analytics", "weight": 40},
    {"name": "performance", "weight": 38},
    {"name": "infrastructure", "weight": 35},
    {"name": "monitoring", "weight": 32},
    {"name": "deployment", "weight": 30},
    {"name": "integration", "weight": 28},
    {"name": "visualization", "weight": 26},
    {"name": "optimization", "weight": 24},
    {"name": "debugging", "weight": 22},
    {"name": "architecture", "weight": 20},
    {"name": "collaboration", "weight": 18},
    {"name": "documentation", "weight": 16},
    {"name": "refactoring", "weight": 14},
    {"name": "opensource", "weight": 12},
]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {"type": "wordcloud", "width": 4800, "height": 2700, "backgroundColor": "#ffffff"}

# Title
chart.options.title = {
    "text": "Developer Survey · wordcloud-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
}

# Credits
chart.options.credits = {"enabled": False}

# Tooltip
chart.options.tooltip = {"style": {"fontSize": "32px"}, "pointFormat": "<b>{point.name}</b>: {point.weight} mentions"}

# Wordcloud series configuration with colorblind-safe colors
chart.options.series = [
    {
        "type": "wordcloud",
        "name": "Mentions",
        "data": words_data,
        "minFontSize": 24,
        "maxFontSize": 120,
        "spiral": "archimedean",
        "rotation": {"from": 0, "to": 60, "orientations": 5},
        "style": {"fontFamily": "Arial, sans-serif", "fontWeight": "bold"},
        "colors": ["#306998", "#FFD43B", "#9467BD", "#17BECF", "#8C564B", "#2CA02C", "#E377C2"],
    }
]

# Legend not applicable for word clouds
chart.options.legend = {"enabled": False}

# Download Highcharts JS and wordcloud module
highcharts_url = "https://code.highcharts.com/highcharts.js"
wordcloud_url = "https://code.highcharts.com/modules/wordcloud.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(wordcloud_url, timeout=30) as response:
    wordcloud_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{wordcloud_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive version (uses CDN for better compatibility)
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/wordcloud.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Write temp HTML and take screenshot
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
