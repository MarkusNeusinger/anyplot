""" anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-12
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme configuration
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Plant growth study with three fertilizer types
np.random.seed(42)

categories = ["Fertilizer A", "Fertilizer B", "Fertilizer C"]
data_by_category = {}
n_points = 40

# Fertilizer A: moderate growth, medium variance
nitrogen_a = np.random.uniform(20, 80, n_points)
growth_a = 0.4 * nitrogen_a + np.random.normal(10, 5, n_points)
data_by_category["Fertilizer A"] = [
    [float(x), float(y)] for x, y in zip(nitrogen_a, growth_a, strict=False)
]

# Fertilizer B: high growth, low variance (best performer)
nitrogen_b = np.random.uniform(25, 85, n_points)
growth_b = 0.6 * nitrogen_b + np.random.normal(15, 3, n_points)
data_by_category["Fertilizer B"] = [
    [float(x), float(y)] for x, y in zip(nitrogen_b, growth_b, strict=False)
]

# Fertilizer C: lower growth, higher variance
nitrogen_c = np.random.uniform(15, 75, n_points)
growth_c = 0.3 * nitrogen_c + np.random.normal(5, 8, n_points)
data_by_category["Fertilizer C"] = [
    [float(x), float(y)] for x, y in zip(nitrogen_c, growth_c, strict=False)
]

# Build chart configuration as dict
series = []
for i, category in enumerate(categories):
    series.append(
        {
            "name": category,
            "data": data_by_category[category],
            "color": IMPRINT[i],
            "type": "scatter",
            "marker": {
                "radius": 8,
                "fillColor": IMPRINT[i],
                "lineWidth": 2,
                "lineColor": PAGE_BG,
                "fillOpacity": 0.8,
            },
        }
    )

chart_options = {
    "chart": {"type": "scatter", "width": 4800, "height": 2700, "backgroundColor": PAGE_BG},
    "title": {"text": "scatter-categorical · highcharts · anyplot.ai", "style": {"fontSize": "28px", "color": INK}},
    "xAxis": {
        "title": {"text": "Nitrogen Applied (kg/ha)", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
    },
    "yAxis": {
        "title": {"text": "Plant Growth (cm)", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
    },
    "legend": {"itemStyle": {"fontSize": "18px", "color": INK_SOFT}},
    "series": series,
}

# Download Highcharts JS
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
)
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")
except Exception:
    highcharts_js = "window.Highcharts = {};"

# Generate HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {json.dumps(chart_options)});
        }});
    </script>
</body>
</html>"""

# Save HTML
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Generate PNG via Selenium
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
time.sleep(10)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
