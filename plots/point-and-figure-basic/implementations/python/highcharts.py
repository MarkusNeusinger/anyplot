""" pyplots.ai
point-and-figure-basic: Point and Figure Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

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


# Data - Generate realistic stock price data with trends and reversals
np.random.seed(42)
n_days = 300
base_price = 100

# Create price series with multiple trends for interesting P&F patterns
returns = np.zeros(n_days)
# Uptrend phase
returns[:80] = np.random.normal(0.003, 0.015, 80)
# Downtrend phase
returns[80:140] = np.random.normal(-0.004, 0.018, 60)
# Consolidation
returns[140:200] = np.random.normal(0.0, 0.012, 60)
# Strong uptrend
returns[200:260] = np.random.normal(0.005, 0.015, 60)
# Correction
returns[260:] = np.random.normal(-0.003, 0.016, 40)

prices = base_price * np.cumprod(1 + returns)

# P&F parameters
box_size = 2.0  # Each box represents $2
reversal = 3  # 3-box reversal


# Round to box size
def to_box(price):
    return int(np.floor(price / box_size))


# Build P&F chart - track boxes in each column
columns = []  # List of dicts: {'direction': 'X'/'O', 'boxes': set of box indices}
current_col = None
last_box = to_box(prices[0])

for price in prices:
    current_box = to_box(price)

    if current_col is None:
        # Start first column
        if current_box > last_box:
            current_col = {"direction": "X", "boxes": set(range(last_box, current_box + 1))}
            columns.append(current_col)
        elif current_box < last_box:
            current_col = {"direction": "O", "boxes": set(range(current_box, last_box + 1))}
            columns.append(current_col)
        last_box = current_box
        continue

    if current_col["direction"] == "X":
        if current_box > last_box:
            # Continue upward - add all boxes from last to current
            for b in range(last_box + 1, current_box + 1):
                current_col["boxes"].add(b)
            last_box = current_box
        elif current_box <= last_box - reversal:
            # Reversal down - start new O column
            new_col = {"direction": "O", "boxes": set(range(current_box, last_box))}
            columns.append(new_col)
            current_col = new_col
            last_box = current_box
    else:  # direction == 'O'
        if current_box < last_box:
            # Continue downward - add all boxes from current to last
            for b in range(current_box, last_box):
                current_col["boxes"].add(b)
            last_box = current_box
        elif current_box >= last_box + reversal:
            # Reversal up - start new X column
            new_col = {"direction": "X", "boxes": set(range(last_box + 1, current_box + 1))}
            columns.append(new_col)
            current_col = new_col
            last_box = current_box

# Convert to plot points
x_points = []
o_points = []

for col_idx, col in enumerate(columns):
    for box in col["boxes"]:
        price_val = box * box_size
        point = {"x": col_idx, "y": price_val}
        if col["direction"] == "X":
            x_points.append(point)
        else:
            o_points.append(point)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "marginLeft": 200,
    "marginRight": 200,
    "marginTop": 180,
}

# Title
chart.options.title = {
    "text": "point-and-figure-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": f"Box Size: ${box_size:.0f} | {reversal}-Box Reversal | Simulated Stock Data",
    "style": {"fontSize": "36px", "color": "#666666"},
}

# Get ranges
max_col = len(columns) - 1 if columns else 0
all_boxes = set()
for col in columns:
    all_boxes.update(col["boxes"])
min_box = min(all_boxes) if all_boxes else 40
max_box = max(all_boxes) if all_boxes else 70

# X-axis (columns)
chart.options.x_axis = {
    "title": {"text": "Column (Reversal Number)", "style": {"fontSize": "40px", "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "32px"}},
    "tickInterval": 1,
    "min": -0.5,
    "max": max_col + 0.5,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Y-axis (price)
chart.options.y_axis = {
    "title": {"text": "Price ($)", "style": {"fontSize": "40px", "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "32px"}, "format": "${value}"},
    "tickInterval": box_size * 2,
    "min": (min_box - 2) * box_size,
    "max": (max_box + 2) * box_size,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -30,
    "y": 80,
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal"},
    "symbolRadius": 0,
    "symbolHeight": 32,
    "symbolWidth": 32,
}

# X series (bullish/rising) - display X character
x_series = ScatterSeries()
x_series.name = "X (Rising)"
x_series.data = x_points
x_series.color = "#306998"  # Python Blue for bullish
x_series.marker = {"enabled": False}
x_series.data_labels = {
    "enabled": True,
    "format": "X",
    "style": {"fontSize": "36px", "fontWeight": "bold", "color": "#306998", "textOutline": "none"},
    "align": "center",
    "verticalAlign": "middle",
    "y": 0,
}
chart.add_series(x_series)

# O series (bearish/falling) - display O character
o_series = ScatterSeries()
o_series.name = "O (Falling)"
o_series.data = o_points
o_series.color = "#E74C3C"  # Red for bearish
o_series.marker = {"enabled": False}
o_series.data_labels = {
    "enabled": True,
    "format": "O",
    "style": {"fontSize": "36px", "fontWeight": "bold", "color": "#E74C3C", "textOutline": "none"},
    "align": "center",
    "verticalAlign": "middle",
    "y": 0,
}
chart.add_series(o_series)

# Tooltip
chart.options.tooltip = {
    "headerFormat": "<b>Column {point.x}</b><br/>",
    "pointFormat": "Price: ${point.y}",
    "style": {"fontSize": "28px"},
}

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML
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

# Write HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save as plot.html for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    # Use CDN for the standalone HTML file
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(standalone_html)

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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
