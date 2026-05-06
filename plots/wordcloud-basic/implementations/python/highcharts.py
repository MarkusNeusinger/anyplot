""" anyplot.ai
wordcloud-basic: Basic Word Cloud
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-06
"""

import os
import tempfile
import time
from pathlib import Path

import requests
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data - Technology terms and their frequency from a developer survey
words_data = [
    {"name": "python", "weight": 420},
    {"name": "javascript", "weight": 380},
    {"name": "data", "weight": 340},
    {"name": "cloud", "weight": 310},
    {"name": "api", "weight": 280},
    {"name": "machine learning", "weight": 250},
    {"name": "database", "weight": 230},
    {"name": "security", "weight": 210},
    {"name": "docker", "weight": 190},
    {"name": "kubernetes", "weight": 170},
    {"name": "react", "weight": 160},
    {"name": "automation", "weight": 150},
    {"name": "devops", "weight": 140},
    {"name": "microservices", "weight": 130},
    {"name": "testing", "weight": 120},
    {"name": "agile", "weight": 110},
    {"name": "frontend", "weight": 100},
    {"name": "backend", "weight": 90},
    {"name": "scalability", "weight": 80},
    {"name": "typescript", "weight": 70},
    {"name": "git", "weight": 60},
    {"name": "analytics", "weight": 50},
    {"name": "performance", "weight": 45},
    {"name": "infrastructure", "weight": 40},
    {"name": "monitoring", "weight": 35},
    {"name": "deployment", "weight": 30},
    {"name": "integration", "weight": 25},
    {"name": "visualization", "weight": 20},
    {"name": "optimization", "weight": 15},
    {"name": "debugging", "weight": 10},
]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration with theme-aware background
chart.options.chart = {
    "type": "wordcloud",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginTop": 100,
    "marginBottom": 80,
}

# Title with theme-aware styling
chart.options.title = {"text": "wordcloud-basic · highcharts · anyplot.ai", "style": {"fontSize": "28px", "color": INK}}

# Credits
chart.options.credits = {"enabled": False}

# Tooltip
chart.options.tooltip = {
    "style": {"fontSize": "18px", "color": INK},
    "pointFormat": "<b>{point.name}</b>: {point.weight} mentions",
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
}

# Wordcloud series configuration using Okabe-Ito palette
chart.options.series = [
    {
        "type": "wordcloud",
        "name": "Mentions",
        "data": words_data,
        "minFontSize": 28,
        "maxFontSize": 140,
        "spiral": "rectangular",
        "rotation": {"from": 0, "to": 60, "orientations": 4},
        "style": {"fontFamily": "Arial, sans-serif", "fontWeight": "normal"},
        "colors": OKABE_ITO,
    }
]

# Legend not applicable for word clouds
chart.options.legend = {"enabled": False}

# Download Highcharts JS and wordcloud module
# Try jsDelivr CDN as fallback if code.highcharts.com is blocked
highcharts_urls = [
    "https://code.highcharts.com/highcharts.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11.0.0/highcharts.js",
]
wordcloud_urls = [
    "https://code.highcharts.com/modules/wordcloud.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11.0.0/modules/wordcloud.js",
]

session = requests.Session()
session.headers.update(
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0"}
)

highcharts_js = None
for url in highcharts_urls:
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        highcharts_js = response.text
        break
    except requests.RequestException:
        continue

if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS from any CDN")

wordcloud_js = None
for url in wordcloud_urls:
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        wordcloud_js = response.text
        break
    except requests.RequestException:
        continue

if wordcloud_js is None:
    raise RuntimeError("Failed to download Wordcloud module from any CDN")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{wordcloud_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact with theme-aware filename
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
