""" anyplot.ai
box-notched: Notched Box Plot
Library: highcharts unknown | Python 3.13.13
Quality: 97/100 | Updated: 2026-05-07
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


# Theme tokens (theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - Generate realistic clinical trial data comparing treatments
np.random.seed(42)

categories = ["Placebo", "Low Dose", "Medium Dose", "High Dose"]
n_per_category = 60

# Generate data with different distributions to show notch effectiveness
data_dict = {
    "Placebo": np.random.normal(50, 12, n_per_category),
    "Low Dose": np.random.normal(55, 10, n_per_category),
    "Medium Dose": np.random.normal(62, 11, n_per_category),
    "High Dose": np.random.normal(68, 9, n_per_category),
}

# Add some outliers
data_dict["Placebo"] = np.append(data_dict["Placebo"], [15, 85])
data_dict["Medium Dose"] = np.append(data_dict["Medium Dose"], [30, 95])

# Okabe-Ito palette - first series is always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Calculate box plot statistics inline (KISS - no functions)
box_data = []
errorbar_data = []
outlier_data = []

for i, cat in enumerate(categories):
    data = data_dict[cat]

    # Calculate quartiles and IQR
    q1 = float(np.percentile(data, 25))
    median = float(np.percentile(data, 50))
    q3 = float(np.percentile(data, 75))
    iqr = q3 - q1

    # Whiskers at 1.5*IQR
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    # Actual whisker endpoints (within data range, excluding outliers)
    non_outliers = data[(data >= lower_fence) & (data <= upper_fence)]
    lower_whisker = float(np.min(non_outliers))
    upper_whisker = float(np.max(non_outliers))

    # Notch calculation: ±1.57 × IQR / √n (95% CI for median)
    n = len(data)
    notch_range = 1.57 * iqr / np.sqrt(n)
    notch_low = median - notch_range
    notch_high = median + notch_range

    # Outliers
    outliers = data[(data < lower_fence) | (data > upper_fence)]

    # Box data
    box_data.append(
        {
            "low": round(lower_whisker, 2),
            "q1": round(q1, 2),
            "median": round(median, 2),
            "q3": round(q3, 2),
            "high": round(upper_whisker, 2),
            "color": IMPRINT[i],
        }
    )

    # Error bar data for notch visualization (95% CI around median)
    errorbar_data.append({"x": i, "low": round(notch_low, 2), "high": round(notch_high, 2)})

    # Outlier data
    for outlier in outliers:
        outlier_data.append({"x": i, "y": round(float(outlier), 2)})

# Build chart config
chart_config = {
    "chart": {
        "type": "boxplot",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginBottom": 200,
        "marginLeft": 150,
        "marginRight": 150,
    },
    "title": {
        "text": "box-notched · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
    },
    "subtitle": {
        "text": "Treatment Response by Dose — Error bars indicate 95% CI (notch) for median comparison",
        "style": {"fontSize": "22px", "color": INK_SOFT},
    },
    "xAxis": {
        "categories": categories,
        "title": {"text": "Treatment Group", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
    },
    "yAxis": {
        "title": {"text": "Response Score", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
        "gridLineWidth": 1,
    },
    "legend": {
        "enabled": True,
        "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "x": -80,
        "y": 80,
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "padding": 15,
    },
    "plotOptions": {
        "boxplot": {
            "lineWidth": 4,
            "whiskerLength": "60%",
            "whiskerWidth": 4,
            "stemWidth": 3,
            "medianWidth": 6,
            "medianColor": INK,
            "colorByPoint": True,
            "colors": IMPRINT,
        },
        "errorbar": {"lineWidth": 8, "whiskerLength": "40%", "color": INK, "stemWidth": 0},
    },
    "series": [
        {
            "name": "Response Distribution",
            "type": "boxplot",
            "data": box_data,
            "tooltip": {
                "headerFormat": "<b>{point.key}</b><br/>",
                "pointFormat": "Upper: {point.high}<br/>Q3: {point.q3}<br/>Median: {point.median}<br/>Q1: {point.q1}<br/>Lower: {point.low}",
            },
        },
        {
            "name": "95% CI (Notch)",
            "type": "errorbar",
            "data": errorbar_data,
            "color": INK,
            "lineWidth": 6,
            "whiskerLength": "35%",
            "whiskerWidth": 6,
            "showInLegend": True,
            "tooltip": {"pointFormat": "95% CI: {point.low} - {point.high}"},
        },
        {
            "name": "Outliers",
            "type": "scatter",
            "data": outlier_data,
            "marker": {
                "symbol": "circle",
                "radius": 14,
                "fillColor": IMPRINT[0],
                "lineColor": PAGE_BG,
                "lineWidth": 2,
            },
            "tooltip": {"pointFormat": "Outlier: {point.y}"},
        },
    ],
    "credits": {"enabled": False},
}

chart_json = json.dumps(chart_config)


# Download Highcharts JS files with retry and User-Agent
def download_with_retry(url, max_retries=3):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8")
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(2**attempt)  # Exponential backoff


# Try multiple CDNs
cdns = [
    ("https://code.highcharts.com/highcharts.js", "https://code.highcharts.com/highcharts-more.js"),
    (
        "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js",
        "https://cdn.jsdelivr.net/npm/highcharts/highcharts-more.js",
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.3/highcharts.js",
        "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.3/highcharts-more.js",
    ),
]

highcharts_js = None
highcharts_more_js = None
for hc_url, hc_more_url in cdns:
    try:
        highcharts_js = download_with_retry(hc_url)
        highcharts_more_js = download_with_retry(hc_more_url)
        break
    except Exception:
        continue

if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts from all CDNs")

# Generate HTML with inline scripts
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
        Highcharts.chart('container', {chart_json});
    </script>
</body>
</html>"""

# Write temp HTML and screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save HTML for interactive version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
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
