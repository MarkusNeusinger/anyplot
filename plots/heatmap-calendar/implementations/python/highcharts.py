""" anyplot.ai
heatmap-calendar: Basic Calendar Heatmap
Library: highcharts unknown | Python 3.14.4
Quality: 82/100 | Updated: 2026-04-27
"""

import os
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
CELL_EMPTY = "#E8E5DC" if THEME == "light" else "#2D2D2A"
CELL_BORDER = "#FAF8F1" if THEME == "light" else "#1A1A17"

# Data — one year of daily GitHub-style activity
np.random.seed(42)
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)
num_days = (end_date - start_date).days + 1

dates = [start_date + timedelta(days=i) for i in range(num_days)]
values = []
for d in dates:
    if d.weekday() >= 5:
        base = np.random.choice([0, 0, 0, 1, 2, 3], p=[0.4, 0.2, 0.15, 0.1, 0.1, 0.05])
    else:
        base = np.random.choice(
            [0, 1, 2, 3, 4, 5, 6, 8, 10, 15], p=[0.1, 0.15, 0.2, 0.15, 0.1, 0.1, 0.08, 0.07, 0.03, 0.02]
        )
    month = d.month
    if month in [3, 4, 5, 9, 10, 11]:
        base = int(base * 1.3)
    values.append(base)

# Build calendar grid: x = week index, y = weekday (0=Mon … 6=Sun)
first_day_weekday = start_date.weekday()
heatmap_data = []
month_markers = []

for d, v in zip(dates, values, strict=True):
    days_from_start = (d - start_date).days
    week_num = (days_from_start + first_day_weekday) // 7
    day_of_week = d.weekday()
    heatmap_data.append([int(week_num), int(day_of_week), int(v)])
    if d.day == 1:
        month_markers.append({"week": week_num, "month": d.strftime("%b")})

num_weeks = max(item[0] for item in heatmap_data) + 1
weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

x_axis_categories = [""] * num_weeks
for marker in month_markers:
    if marker["week"] < num_weeks:
        x_axis_categories[marker["week"]] = marker["month"]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginTop": 200,
    "marginBottom": 150,
    "marginLeft": 200,
    "marginRight": 450,
    "style": {"color": INK},
}

chart.options.title = {
    "text": "Daily Activity 2024 · heatmap-calendar · highcharts · anyplot.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold", "color": INK},
    "y": 80,
}

chart.options.x_axis = {
    "categories": x_axis_categories,
    "title": None,
    "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}, "rotation": 0},
    "tickLength": 0,
    "lineWidth": 0,
    "gridLineColor": GRID,
    "opposite": True,
}

chart.options.y_axis = {
    "categories": weekday_labels,
    "title": None,
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "reversed": False,
    "gridLineWidth": 0,
    "lineColor": INK_SOFT,
}

chart.options.color_axis = {
    "min": 0,
    "max": 15,
    "stops": [
        [0, CELL_EMPTY],
        [0.01, CELL_EMPTY],
        [0.02, "#9be9a8"],
        [0.25, "#40c463"],
        [0.5, "#30a14e"],
        [1, "#216e39"],
    ],
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}},
}

chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "margin": 40,
    "verticalAlign": "middle",
    "symbolHeight": 600,
    "itemStyle": {"fontSize": "30px", "color": INK_SOFT},
    "title": {"text": "Commits", "style": {"fontSize": "34px", "color": INK}},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

chart.options.tooltip = {
    "style": {"fontSize": "28px"},
    "formatter": """function() {
        var weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        var weekday = weekdays[this.point.y];
        var value = this.point.value;
        if (value === 0) {
            return '<b>No contributions</b> on ' + weekday;
        } else if (value === 1) {
            return '<b>1 contribution</b> on ' + weekday;
        } else {
            return '<b>' + value + ' contributions</b> on ' + weekday;
        }
    }""",
    "useHTML": True,
}

chart.options.series = [
    {
        "name": "Commits",
        "type": "heatmap",
        "data": heatmap_data,
        "borderWidth": 3,
        "borderColor": CELL_BORDER,
        "borderRadius": 4,
        "colsize": 1,
        "rowsize": 1,
        "dataLabels": {"enabled": False},
    }
]

# Download Highcharts JS + heatmap module (inline for headless Chrome)
_HC_URLS = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
_HM_URLS = [
    "https://code.highcharts.com/modules/heatmap.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/modules/heatmap.js",
]

highcharts_js = None
for url in _HC_URLS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS")

heatmap_js = None
for url in _HM_URLS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            heatmap_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if heatmap_js is None:
    raise RuntimeError("Failed to download Highcharts heatmap module")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact (theme-suffixed, uses CDN for interactivity)
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/heatmap.js"></script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Screenshot via headless Chrome
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
