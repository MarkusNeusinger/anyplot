""" pyplots.ai
histogram-overlapping: Overlapping Histograms
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Employee performance scores by department
np.random.seed(42)
engineering = np.random.normal(75, 10, 150)  # Higher mean, moderate spread
sales = np.random.normal(70, 15, 150)  # Lower mean, wider spread
marketing = np.random.normal(72, 12, 150)  # Middle ground

# Compute histogram bins (aligned across all groups)
all_data = np.concatenate([engineering, sales, marketing])
bins = np.linspace(all_data.min() - 5, all_data.max() + 5, 16)  # 15 bins for clarity
bin_width = bins[1] - bins[0]

# Calculate histogram counts for each group
eng_counts, _ = np.histogram(engineering, bins=bins)
sales_counts, _ = np.histogram(sales, bins=bins)
mkt_counts, _ = np.histogram(marketing, bins=bins)

# Create bin labels showing ranges
bin_labels = [f"{bins[i]:.0f}" for i in range(len(bins) - 1)]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "marginLeft": 150,
}

# Title
chart.options.title = {
    "text": "histogram-overlapping · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {
    "text": "Employee Performance Score Distribution by Department",
    "style": {"fontSize": "36px", "color": "#666666"},
}

# X-axis
chart.options.x_axis = {
    "categories": bin_labels,
    "title": {"text": "Performance Score", "style": {"fontSize": "40px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "lineWidth": 2,
    "lineColor": "#333333",
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Frequency (Count)", "style": {"fontSize": "40px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "lineWidth": 2,
    "lineColor": "#333333",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -80,
    "y": 120,
    "backgroundColor": "rgba(255, 255, 255, 0.9)",
    "borderWidth": 1,
    "borderColor": "#cccccc",
    "padding": 15,
}

# Plot options for overlapping bars - all same width, same position
chart.options.plot_options = {
    "column": {
        "grouping": False,  # Disable grouping so bars overlap
        "shadow": False,
        "borderWidth": 2,
        "borderColor": "#333333",
        "pointPadding": 0.05,  # Same padding for all
        "groupPadding": 0.1,
    }
}

# Add series with transparency for overlapping effect
# Order matters for z-index - first is behind, last is in front

# Sales (Python Yellow) - back layer (widest distribution)
chart.add_series(
    {
        "type": "column",
        "name": "Sales (n=150)",
        "data": sales_counts.tolist(),
        "color": "rgba(255, 212, 59, 0.55)",
        "borderColor": "#b39400",
    }
)

# Marketing (Purple - colorblind safe) - middle layer
chart.add_series(
    {
        "type": "column",
        "name": "Marketing (n=150)",
        "data": mkt_counts.tolist(),
        "color": "rgba(148, 103, 189, 0.55)",
        "borderColor": "#6b3fa0",
    }
)

# Engineering (Python Blue) - front layer
chart.add_series(
    {
        "type": "column",
        "name": "Engineering (n=150)",
        "data": eng_counts.tolist(),
        "color": "rgba(48, 105, 152, 0.55)",
        "borderColor": "#1a4a6e",
    }
)

# Tooltip
chart.options.tooltip = {
    "shared": True,
    "headerFormat": '<span style="font-size:24px">Score: {point.key}</span><br/>',
    "pointFormat": '<span style="color:{point.color}">\u25cf</span> {series.name}: <b>{point.y}</b><br/>',
    "style": {"fontSize": "22px"},
}

# Download Highcharts JS for headless Chrome
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

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
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
