""" anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: highcharts unknown | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-17
"""

import os
import ssl
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
OKABE_ITO = [
    "#009E73",  # position 1 (brand green - ALWAYS first series)
    "#D55E00",  # position 2
    "#0072B2",  # position 3
    "#CC79A7",  # position 4
]

# Data - Simulated word embeddings after dimensionality reduction
np.random.seed(42)

programming_words = ["Python", "JavaScript", "Java", "C++", "Ruby", "Rust", "Go", "Swift"]
data_words = ["Pandas", "NumPy", "TensorFlow", "PyTorch", "Scikit-learn", "Keras"]
web_words = ["React", "Vue", "Angular", "Django", "Flask", "Node.js"]
database_words = ["PostgreSQL", "MongoDB", "Redis", "MySQL", "SQLite", "Cassandra"]

# Create clustered positions
x_coords = []
y_coords = []

for _ in programming_words:
    x_coords.append(np.random.normal(-2.5, 0.7))
    y_coords.append(np.random.normal(2, 0.7))

for _ in data_words:
    x_coords.append(np.random.normal(2.5, 0.6))
    y_coords.append(np.random.normal(2.5, 0.6))

for _ in web_words:
    x_coords.append(np.random.normal(2, 0.5))
    y_coords.append(np.random.normal(-2, 0.5))

for _ in database_words:
    x_coords.append(np.random.normal(-2, 0.6))
    y_coords.append(np.random.normal(-2, 0.6))

x = np.array(x_coords)
y = np.array(y_coords)

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
ssl_context = ssl._create_unverified_context()
request = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://anyplot.ai"})
with urllib.request.urlopen(request, timeout=30, context=ssl_context) as response:
    highcharts_js = response.read().decode("utf-8")

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginLeft": 250,
    "marginRight": 300,
    "marginTop": 200,
    "marginBottom": 300,
}

# Title
chart.options.title = {
    "text": "scatter-text · Python · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "500", "color": INK},
}

# Axes
chart.options.x_axis = {
    "title": {"text": "Dimension 1", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.y_axis = {
    "title": {"text": "Dimension 2", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "top",
    "x": -50,
    "y": 100,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "backgroundColor": ELEVATED_BG,
    "padding": 20,
}

# Create data with text labels
categories = {
    "Programming Languages": (programming_words, OKABE_ITO[0], 0),
    "Data Science": (data_words, OKABE_ITO[1], len(programming_words)),
    "Web Frameworks": (web_words, OKABE_ITO[2], len(programming_words) + len(data_words)),
    "Databases": (database_words, OKABE_ITO[3], len(programming_words) + len(data_words) + len(web_words)),
}

for cat_name, (words, color, start_idx) in categories.items():
    series = ScatterSeries()
    series.name = cat_name

    data_points = []
    for i, word in enumerate(words):
        idx = start_idx + i
        data_points.append(
            {
                "x": float(x[idx]),
                "y": float(y[idx]),
                "name": word,
                "dataLabels": {
                    "enabled": True,
                    "format": word,
                    "style": {"fontSize": "24px", "fontWeight": "500", "color": color, "textOutline": f"2px {PAGE_BG}"},
                    "allowOverlap": False,
                },
            }
        )

    series.data = data_points
    series.marker = {"enabled": False}
    series.color = color

    chart.add_series(series)

# Plot options
chart.options.plot_options = {
    "scatter": {"marker": {"enabled": False}, "dataLabels": {"enabled": True, "style": {"fontSize": "24px"}}}
}

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
