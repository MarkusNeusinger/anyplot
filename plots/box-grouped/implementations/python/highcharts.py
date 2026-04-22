""" pyplots.ai
box-grouped: Grouped Box Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.boxplot import BoxPlotSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Employee performance scores by department and experience level
np.random.seed(42)

categories = ["Engineering", "Sales", "Marketing", "Finance"]
subcategories = ["Junior", "Mid-Level", "Senior"]

# Generate realistic performance data with varying distributions
data = {}
for cat in categories:
    data[cat] = {}
    for i, subcat in enumerate(subcategories):
        # Create different distributions by department and experience level
        if cat == "Engineering":
            base = 70 + i * 8
            spread = 12 - i * 2
        elif cat == "Sales":
            base = 65 + i * 10
            spread = 15 - i * 3
        elif cat == "Marketing":
            base = 72 + i * 6
            spread = 10
        else:  # Finance
            base = 75 + i * 5
            spread = 8

        n_points = np.random.randint(30, 50)
        values = np.random.normal(base, spread, n_points)
        # Add some outliers
        if np.random.random() > 0.5:
            outliers_count = np.random.randint(1, 4)
            outlier_vals = np.random.choice([base - spread * 3, base + spread * 3], outliers_count)
            values = np.concatenate([values, outlier_vals])
        data[cat][subcat] = np.clip(values, 20, 100)


# Calculate box plot statistics
def calc_boxplot_stats(values):
    q1 = np.percentile(values, 25)
    median = np.percentile(values, 50)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    whisker_low = max(np.min(values), q1 - 1.5 * iqr)
    whisker_high = min(np.max(values), q3 + 1.5 * iqr)
    outliers = values[(values < whisker_low) | (values > whisker_high)]
    return {
        "low": float(whisker_low),
        "q1": float(q1),
        "median": float(median),
        "q3": float(q3),
        "high": float(whisker_high),
        "outliers": [float(o) for o in outliers],
    }


# Prepare series data for each subcategory
colors = ["#306998", "#FFD43B", "#9467BD"]  # Python Blue, Python Yellow, Purple

series_list = []
for idx, subcat in enumerate(subcategories):
    box_data = []
    for cat in categories:
        stats = calc_boxplot_stats(data[cat][subcat])
        box_data.append([stats["low"], stats["q1"], stats["median"], stats["q3"], stats["high"]])

    series = BoxPlotSeries()
    series.name = subcat
    series.data = box_data
    series.color = colors[idx]
    series.fill_color = colors[idx]
    series.median_color = "#333333"
    series.stem_color = colors[idx]
    series.whisker_color = colors[idx]
    series_list.append(series)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "boxplot",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 300,
    "marginLeft": 200,
    "spacingTop": 60,
}

chart.options.title = {
    "text": "box-grouped \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": "Employee Performance Scores by Department and Experience Level",
    "style": {"fontSize": "32px"},
}

chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Department", "style": {"fontSize": "36px"}, "margin": 30},
    "labels": {"style": {"fontSize": "32px"}, "y": 40},
}

chart.options.y_axis = {
    "title": {"text": "Performance Score", "style": {"fontSize": "36px"}, "margin": 30},
    "labels": {"style": {"fontSize": "32px"}},
    "min": 20,
    "max": 100,
    "gridLineColor": "#e0e0e0",
    "gridLineWidth": 1,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
    "itemStyle": {"fontSize": "32px"},
    "symbolRadius": 0,
    "symbolHeight": 24,
    "symbolWidth": 50,
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
    }
}

for series in series_list:
    chart.add_series(series)

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
