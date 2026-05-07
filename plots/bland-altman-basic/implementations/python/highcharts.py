""" anyplot.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: highcharts unknown | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-07
"""

import base64
import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data: Simulated blood pressure readings from two sphygmomanometers
np.random.seed(42)
n_subjects = 80

# True blood pressure values (systolic, mmHg)
true_bp = np.random.normal(130, 15, n_subjects)

# Method 1: Reference device (small measurement error)
method1 = true_bp + np.random.normal(0, 3, n_subjects)

# Method 2: New device being validated (slightly higher readings with more variability)
method2 = true_bp + np.random.normal(2, 5, n_subjects)

# Bland-Altman calculations
mean_values = (method1 + method2) / 2
differences = method1 - method2
mean_diff = np.mean(differences)
std_diff = np.std(differences, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# X-axis range for reference lines
x_min = np.min(mean_values)
x_max = np.max(mean_values)
x_padding = (x_max - x_min) * 0.05
line_x_min = x_min - x_padding
line_x_max = x_max + x_padding

# Prepare data for JSON
data_points = [[float(x), float(y)] for x, y in zip(mean_values, differences, strict=True)]

# Chart configuration as JSON
chart_config = {
    "chart": {
        "type": "scatter",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginRight": 250,
        "marginBottom": 200,
        "spacingBottom": 50,
    },
    "title": {
        "text": "bland-altman-basic · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
    },
    "xAxis": {
        "title": {"text": "Mean of Two Methods (mmHg)", "style": {"fontSize": "22px", "color": INK}, "offset": 20},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineWidth": 1,
        "gridLineColor": "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)",
        "min": line_x_min,
        "max": line_x_max,
    },
    "yAxis": {
        "title": {"text": "Difference (Method 1 - Method 2) (mmHg)", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineWidth": 1,
        "gridLineColor": "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)",
        "plotLines": [
            {
                "value": mean_diff,
                "color": BRAND,
                "width": 4,
                "zIndex": 3,
                "label": {
                    "text": f"Mean: {mean_diff:.2f}",
                    "align": "right",
                    "style": {"fontSize": "18px", "fontWeight": "normal", "color": INK},
                },
            },
            {
                "value": upper_loa,
                "color": INK_SOFT,
                "width": 2,
                "dashStyle": "Dash",
                "zIndex": 3,
                "label": {
                    "text": f"+1.96 SD: {upper_loa:.2f}",
                    "align": "right",
                    "style": {"fontSize": "18px", "color": INK_SOFT},
                },
            },
            {
                "value": lower_loa,
                "color": INK_SOFT,
                "width": 2,
                "dashStyle": "Dash",
                "zIndex": 3,
                "label": {
                    "text": f"−1.96 SD: {lower_loa:.2f}",
                    "align": "right",
                    "style": {"fontSize": "18px", "color": INK_SOFT},
                },
            },
        ],
    },
    "legend": {"enabled": False},
    "plotOptions": {"scatter": {"marker": {"radius": 8, "fillColor": BRAND, "lineWidth": 0, "opacity": 0.7}}},
    "series": [{"name": "Paired Observations", "data": data_points, "color": BRAND}],
}

# Download Highcharts JS for inline embedding
urls = [
    "https://code.highcharts.com/highcharts.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js",
    "https://unpkg.com/highcharts@11/highcharts.js",
]
highcharts_js = None
for url in urls:
    for attempt in range(2):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                highcharts_js = response.read().decode("utf-8")
            break
        except Exception:
            if attempt < 1:
                time.sleep(1)
    if highcharts_js:
        break
if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts from all CDNs")

# Convert config to JSON
config_json = json.dumps(chart_config)

# Generate HTML with inline Highcharts JS
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {config_json});
    </script>
</body>
</html>"""

# Save interactive HTML
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome using CDP
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Use CDP for high-quality screenshot
screenshot_config = {"captureBeyondViewport": True, "clip": {"x": 0, "y": 0, "width": 4800, "height": 2700, "scale": 1}}
result = driver.execute_cdp_cmd("Page.captureScreenshot", screenshot_config)
with open(f"plot-{THEME}.png", "wb") as f:
    f.write(base64.b64decode(result["data"]))
driver.quit()

Path(temp_path).unlink()
