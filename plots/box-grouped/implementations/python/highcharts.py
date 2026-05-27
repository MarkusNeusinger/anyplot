""" anyplot.ai
box-grouped: Grouped Box Plot
Library: highcharts unknown | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-08
"""

import os
import tempfile
import time
from pathlib import Path

import numpy as np
import requests
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.boxplot import BoxPlotSeries
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
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Employee performance scores by department and experience level
np.random.seed(42)

categories = ["Engineering", "Sales", "Marketing", "Finance"]
subcategories = ["Junior", "Mid-Level", "Senior"]

data = {}
for cat in categories:
    data[cat] = {}
    for i, subcat in enumerate(subcategories):
        if cat == "Engineering":
            base = 70 + i * 8
            spread = 12 - i * 2
        elif cat == "Sales":
            base = 65 + i * 10
            spread = 15 - i * 3
        elif cat == "Marketing":
            base = 72 + i * 6
            spread = 10
        else:
            base = 75 + i * 5
            spread = 8

        n_points = np.random.randint(30, 50)
        values = np.random.normal(base, spread, n_points)
        if np.random.random() > 0.5:
            outliers_count = np.random.randint(1, 4)
            outlier_vals = np.random.choice([base - spread * 3, base + spread * 3], outliers_count)
            values = np.concatenate([values, outlier_vals])
        data[cat][subcat] = np.clip(values, 20, 100)

# Prepare series data for each subcategory
series_list = []
for idx, subcat in enumerate(subcategories):
    box_data = []
    outliers_data = []

    for cat_idx, cat in enumerate(categories):
        values = data[cat][subcat]
        q1 = np.percentile(values, 25)
        median = np.percentile(values, 50)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        whisker_low = max(np.min(values), q1 - 1.5 * iqr)
        whisker_high = min(np.max(values), q3 + 1.5 * iqr)

        box_data.append([float(whisker_low), float(q1), float(median), float(q3), float(whisker_high)])

        outliers = values[(values < whisker_low) | (values > whisker_high)]
        for outlier in outliers:
            outliers_data.append([cat_idx, float(outlier)])

    # Add box plot series
    series = BoxPlotSeries()
    series.name = subcat
    series.data = box_data
    series.color = IMPRINT[idx]
    series.fill_color = IMPRINT[idx]
    series.median_color = INK
    series.stem_color = IMPRINT[idx]
    series.whisker_color = IMPRINT[idx]
    series_list.append(series)

    # Add outliers as scatter points if any exist
    if outliers_data:
        scatter = ScatterSeries()
        scatter.name = f"{subcat} (outliers)"
        scatter.data = outliers_data
        scatter.color = IMPRINT[idx]
        scatter.marker = {"radius": 6}
        scatter.show_in_legend = False
        series_list.append(scatter)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "boxplot",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 150,
    "marginLeft": 200,
    "spacingTop": 60,
}

chart.options.title = {
    "text": "box-grouped · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "normal"},
}

chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Department", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

chart.options.y_axis = {
    "title": {"text": "Performance Score", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 20,
    "max": 100,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

chart.options.plot_options = {
    "boxplot": {
        "lineWidth": 3,
        "medianWidth": 4,
        "stemWidth": 3,
        "whiskerWidth": 4,
        "whiskerLength": "60%",
        "groupPadding": 0.1,
        "pointPadding": 0.05,
    },
    "scatter": {"marker": {"radius": 6}},
}

for series in series_list:
    chart.add_series(series)

# Download Highcharts JS libraries
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36", "Accept": "*/*"})

highcharts_js = None
for attempt in range(3):
    try:
        response = session.get("https://code.highcharts.com/highcharts.js", timeout=30)
        response.raise_for_status()
        highcharts_js = response.text
        break
    except requests.exceptions.RequestException:
        if attempt < 2:
            time.sleep(2**attempt)
            continue
        try:
            response = session.get("https://cdn.jsdelivr.net/npm/highcharts/highcharts.js", timeout=30)
            response.raise_for_status()
            highcharts_js = response.text
        except requests.exceptions.RequestException as e:
            raise RuntimeError("Failed to fetch highcharts.js") from e

highcharts_more_js = None
for attempt in range(3):
    try:
        response = session.get("https://code.highcharts.com/highcharts-more.js", timeout=30)
        response.raise_for_status()
        highcharts_more_js = response.text
        break
    except requests.exceptions.RequestException:
        if attempt < 2:
            time.sleep(2**attempt)
            continue
        try:
            response = session.get("https://cdn.jsdelivr.net/npm/highcharts/highcharts-more.js", timeout=30)
            response.raise_for_status()
            highcharts_more_js = response.text
        except requests.exceptions.RequestException as e:
            raise RuntimeError("Failed to fetch highcharts-more.js") from e

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot for PNG artifact
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
