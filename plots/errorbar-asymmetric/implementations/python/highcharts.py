""" anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
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


# Theme configuration
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1 - first categorical series
SECONDARY = "#C475FD"  # Position 2

# Data - Quarterly sales forecast with asymmetric confidence intervals
np.random.seed(42)
categories = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025", "Q2 2025"]
# Central values (point estimates in millions USD)
y_values = [12.5, 14.2, 13.8, 18.5, 15.2, 16.8]
# Asymmetric errors - upside potential typically larger in optimistic forecasts
error_lower = [1.2, 1.5, 2.0, 2.5, 1.8, 2.2]  # Downside risk
error_upper = [2.5, 3.0, 2.8, 4.5, 3.2, 3.8]  # Upside potential

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 canvas
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 280,
    "marginLeft": 280,
    "marginRight": 150,
    "marginTop": 200,
    "style": {"color": INK},
}

# Title
chart.options.title = {
    "text": "errorbar-asymmetric · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": INK},
}

# Subtitle explaining the error bars
chart.options.subtitle = {
    "text": "Quarterly Sales Forecast with 10th-90th Percentile Confidence Intervals",
    "style": {"fontSize": "32px", "color": INK_SOFT},
}

# X-axis configuration
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Quarter", "style": {"fontSize": "36px", "color": INK}},
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Sales Forecast (Million USD)", "style": {"fontSize": "36px", "color": INK}},
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
}

# Legend configuration - positioned closer to the data, inside the plot area
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px", "color": INK_SOFT},
    "symbolRadius": 0,
    "symbolWidth": 40,
    "symbolHeight": 24,
    "align": "right",
    "verticalAlign": "top",
    "x": -80,
    "y": 120,
    "layout": "vertical",
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 16,
}

# Plot options - configure errorbar series with visible caps
chart.options.plot_options = {
    "errorbar": {"stemWidth": 6, "whiskerLength": 40, "whiskerWidth": 6},
    "scatter": {"marker": {"radius": 18, "symbol": "circle"}},
}

# Create errorbar data with asymmetric errors: [low, high] format
errorbar_data = []
for y, el, eu in zip(y_values, error_lower, error_upper, strict=True):
    errorbar_data.append([y - el, y + eu])

# Create series data for central points
scatter_data = []
for i, y in enumerate(y_values):
    scatter_data.append({"x": i, "y": y})

# Add series - use native errorbar series type for authentic error bars with caps
chart.options.series = [
    {
        "name": "Point Estimate",
        "type": "scatter",
        "data": scatter_data,
        "color": BRAND,
        "marker": {"radius": 20, "symbol": "diamond", "lineColor": INK_SOFT, "lineWidth": 3},
        "zIndex": 5,
    },
    {
        "name": "10th-90th Percentile Range",
        "type": "errorbar",
        "data": errorbar_data,
        "color": SECONDARY,
        "stemColor": SECONDARY,
        "whiskerColor": SECONDARY,
        "showInLegend": True,
    },
]


# Download Highcharts JS and highcharts-more.js (needed for errorbar)
def download_js(url):
    """Download JS with User-Agent header to avoid 403 errors."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


highcharts_js = download_js("https://cdn.jsdelivr.net/npm/highcharts@11.4.3/highcharts.js")
highcharts_more_js = download_js("https://cdn.jsdelivr.net/npm/highcharts@11.4.3/highcharts-more.js")

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

# Write HTML for interactive viewing
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
