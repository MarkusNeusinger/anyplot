"""pyplots.ai
bump-basic: Basic Bump Chart
Library: highcharts 1.10.3 | Python 3.14.3
Quality: /100 | Updated: 2026-02-22
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Sports team rankings over a season (6 teams, 6 match weeks)
teams = ["Eagles", "Wolves", "Tigers", "Bears", "Sharks", "Lions"]
weeks = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"]

# Rankings for each team across weeks (1 = best, 6 = worst)
# Shows various patterns: overtakes, stability, rise, fall, swaps
rankings = {
    "Eagles": [3, 2, 1, 1, 2, 1],
    "Wolves": [1, 1, 2, 3, 3, 2],
    "Tigers": [4, 3, 3, 2, 1, 3],
    "Bears": [2, 4, 5, 4, 4, 4],
    "Sharks": [5, 5, 4, 5, 6, 5],
    "Lions": [6, 6, 6, 6, 5, 6],
}

# Colorblind-safe palette starting with Python Blue
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF", "#E377C2", "#8C564B"]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 200,
    "marginRight": 480,
    "marginBottom": 250,
    "spacingTop": 100,
    "marginTop": 300,
}

# Title
chart.options.title = {
    "text": "bump-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "League Standings Over Season", "style": {"fontSize": "48px", "color": "#666666"}}

# X-axis
chart.options.x_axis = {
    "categories": weeks,
    "labels": {"style": {"fontSize": "40px"}},
    "lineWidth": 2,
    "tickWidth": 0,
    "gridLineWidth": 0,
}

# Y-axis (inverted so rank 1 is at top)
chart.options.y_axis = {
    "title": {"text": None},
    "labels": {"style": {"fontSize": "40px"}, "format": "#{value}"},
    "reversed": True,
    "min": 0.7,
    "max": 6.3,
    "tickInterval": 1,
    "startOnTick": False,
    "endOnTick": False,
    "gridLineWidth": 1,
    "gridLineDashStyle": "Dot",
    "gridLineColor": "#e0e0e0",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "middle",
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal"},
    "itemMarginBottom": 15,
    "symbolWidth": 40,
}

# Tooltip disabled for static output
chart.options.tooltip = {"enabled": False}

# Credits off
chart.options.credits = {"enabled": False}

# Line styling with markers
chart.options.plot_options = {"line": {"lineWidth": 7, "marker": {"enabled": True, "radius": 14, "symbol": "circle"}}}

# Series
series_list = []
for i, team in enumerate(teams):
    series = LineSeries()
    series.name = team
    series.data = rankings[team]
    series.color = colors[i]
    series_list.append(series)

chart.options.series = series_list

# Download Highcharts JS (required for headless Chrome)
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

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive version
Path("plot.html").write_text(html_content, encoding="utf-8")

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
