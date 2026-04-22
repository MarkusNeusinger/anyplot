""" pyplots.ai
heatmap-calendar: Basic Calendar Heatmap
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Generate one year of daily data (GitHub-style activity data)
np.random.seed(42)
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)
num_days = (end_date - start_date).days + 1

# Generate realistic commit/activity data with patterns
dates = [start_date + timedelta(days=i) for i in range(num_days)]
values = []
for d in dates:
    # Base activity varies by day of week (less on weekends)
    if d.weekday() >= 5:  # Weekend
        base = np.random.choice([0, 0, 0, 1, 2, 3], p=[0.4, 0.2, 0.15, 0.1, 0.1, 0.05])
    else:  # Weekday
        base = np.random.choice(
            [0, 1, 2, 3, 4, 5, 6, 8, 10, 15], p=[0.1, 0.15, 0.2, 0.15, 0.1, 0.1, 0.08, 0.07, 0.03, 0.02]
        )
    # Add seasonal variation (more active in spring/fall)
    month = d.month
    if month in [3, 4, 5, 9, 10, 11]:
        base = int(base * 1.3)
    values.append(base)

# Create data grouped by week for calendar heatmap
# Highcharts heatmap: x = week number (0-52), y = day of week (0-6)
first_day_weekday = start_date.weekday()  # Monday = 0, Sunday = 6

heatmap_data = []
month_markers = []

for d, v in zip(dates, values, strict=True):
    # Calculate week number (0-indexed from start of year)
    days_from_start = (d - start_date).days
    week_num = (days_from_start + first_day_weekday) // 7
    day_of_week = d.weekday()  # Monday = 0, Sunday = 6

    # Store data point (convert numpy int to Python int)
    heatmap_data.append([int(week_num), int(day_of_week), int(v)])

    # Track month boundaries for labels
    if d.day == 1:
        month_markers.append({"week": week_num, "month": d.strftime("%b")})

# Calculate number of weeks
num_weeks = max(item[0] for item in heatmap_data) + 1

# Weekday labels
weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "heatmap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginTop": 180,
    "marginBottom": 150,
    "marginLeft": 200,
    "marginRight": 400,
}

# Title
chart.options.title = {
    "text": "Daily Activity 2024 · heatmap-calendar · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
    "y": 60,
}

# X-axis (weeks) with month labels
x_axis_categories = [""] * num_weeks
for marker in month_markers:
    if marker["week"] < num_weeks:
        x_axis_categories[marker["week"]] = marker["month"]

chart.options.x_axis = {
    "categories": x_axis_categories,
    "title": None,
    "labels": {"style": {"fontSize": "32px"}, "rotation": 0},
    "tickLength": 0,
    "lineWidth": 0,
    "opposite": True,
}

# Y-axis (days of week)
chart.options.y_axis = {
    "categories": weekday_labels,
    "title": None,
    "labels": {"style": {"fontSize": "36px"}},
    "reversed": False,
    "gridLineWidth": 0,
}

# Color axis - GitHub-style green gradient
chart.options.color_axis = {
    "min": 0,
    "max": 15,
    "stops": [
        [0, "#ebedf0"],  # No activity - light gray
        [0.01, "#ebedf0"],  # No activity
        [0.02, "#9be9a8"],  # Low activity - light green
        [0.25, "#40c463"],  # Medium activity
        [0.5, "#30a14e"],  # Higher activity
        [1, "#216e39"],  # Max activity - dark green
    ],
    "labels": {"style": {"fontSize": "32px"}},
}

# Legend configuration
chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "margin": 40,
    "verticalAlign": "middle",
    "symbolHeight": 600,
    "itemStyle": {"fontSize": "32px"},
    "title": {"text": "Commits", "style": {"fontSize": "36px"}},
}

# Tooltip
chart.options.tooltip = {
    "style": {"fontSize": "32px"},
    "formatter": """function() {
        var weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        var weekday = weekdays[this.point.y];
        var value = this.point.value;
        if (value === 0) {
            return '<b>No contributions</b>';
        } else if (value === 1) {
            return '<b>1 contribution</b> on ' + weekday;
        } else {
            return '<b>' + value + ' contributions</b> on ' + weekday;
        }
    }""",
    "useHTML": True,
}

# Add heatmap series
series_config = {
    "name": "Commits",
    "type": "heatmap",
    "data": heatmap_data,
    "borderWidth": 3,
    "borderColor": "#ffffff",
    "borderRadius": 4,
    "colsize": 1,
    "rowsize": 1,
    "dataLabels": {"enabled": False},
}

chart.options.series = [series_config]

# Download Highcharts JS and heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
heatmap_url = "https://code.highcharts.com/modules/heatmap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/heatmap.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(standalone_html)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

# Take screenshot of the container element for exact dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
