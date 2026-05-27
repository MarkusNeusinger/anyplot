""" anyplot.ai
histogram-overlapping: Overlapping Histograms
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-08
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
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

# Data - Employee performance scores by department
np.random.seed(42)
engineering = np.random.normal(75, 10, 150)
sales = np.random.normal(70, 15, 150)
marketing = np.random.normal(72, 12, 150)

# Compute histogram bins (aligned across all groups)
all_data = np.concatenate([engineering, sales, marketing])
bins = np.linspace(all_data.min() - 5, all_data.max() + 5, 16)
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
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginLeft": 150,
}

# Title
chart.options.title = {
    "text": "histogram-overlapping · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
}

# X-axis
chart.options.x_axis = {
    "categories": bin_labels,
    "title": {"text": "Performance Score", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Frequency (Count)", "style": {"fontSize": "22px", "color": INK}},
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
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -80,
    "y": 120,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 15,
}

# Plot options for overlapping bars
chart.options.plot_options = {
    "column": {
        "grouping": False,
        "shadow": False,
        "borderWidth": 1,
        "borderColor": INK_SOFT,
        "pointPadding": 0.05,
        "groupPadding": 0.1,
    }
}

# Add series with transparency for overlapping effect
# Engineering (Okabe-Ito green) - front layer
chart.add_series(
    {
        "type": "column",
        "name": "Engineering (n=150)",
        "data": eng_counts.tolist(),
        "color": IMPRINT[0],
        "opacity": 0.55,
    }
)

# Sales (Okabe-Ito vermillion) - middle layer
chart.add_series(
    {"type": "column", "name": "Sales (n=150)", "data": sales_counts.tolist(), "color": IMPRINT[1], "opacity": 0.55}
)

# Marketing (Okabe-Ito blue) - back layer
chart.add_series(
    {"type": "column", "name": "Marketing (n=150)", "data": mkt_counts.tolist(), "color": IMPRINT[2], "opacity": 0.55}
)

# Tooltip
chart.options.tooltip = {
    "shared": True,
    "headerFormat": '<span style="font-size:18px">Score: {point.key}</span><br/>',
    "pointFormat": '<span style="color:{point.color}">●</span> {series.name}: <b>{point.y}</b><br/>',
    "style": {"fontSize": "16px"},
}

# Download Highcharts JS for headless Chrome
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.3/highcharts.min.js"
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
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
