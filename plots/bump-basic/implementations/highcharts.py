""" pyplots.ai
bump-basic: Basic Bump Chart
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 87/100 | Updated: 2026-02-22
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.spline import SplineSeries
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
# Replaced cyan→orange and pink→crimson for better perceptual distance
colors = ["#306998", "#FFD43B", "#9467BD", "#FF7F0E", "#D62728", "#8C564B"]

# Visual hierarchy: thicker lines for teams with dramatic rank changes
line_widths = {
    "Eagles": 9,  # rises to #1 — protagonist
    "Wolves": 6,
    "Tigers": 9,  # dramatic arc #4→#1→#3
    "Bears": 5,
    "Sharks": 4,  # minor fluctuation
    "Lions": 4,  # mostly stable at bottom
}

marker_radii = {"Eagles": 16, "Wolves": 12, "Tigers": 16, "Bears": 10, "Sharks": 9, "Lions": 9}

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "spline",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 200,
    "marginRight": 380,
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
    "title": {"text": "Rank", "style": {"fontSize": "40px", "color": "#444444"}},
    "labels": {"style": {"fontSize": "40px"}, "format": "#{value}"},
    "reversed": True,
    "min": 0.5,
    "max": 6.5,
    "tickInterval": 1,
    "startOnTick": False,
    "endOnTick": False,
    "gridLineWidth": 1,
    "gridLineDashStyle": "Dot",
    "gridLineColor": "#e0e0e0",
    "plotBands": [
        {
            "from": 0.5,
            "to": 1.5,
            "color": "rgba(255, 215, 0, 0.06)",
            "label": {
                "text": "\u2605",
                "align": "left",
                "x": -60,
                "style": {"fontSize": "36px", "color": "rgba(200, 170, 0, 0.35)"},
            },
        }
    ],
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

# Default plot options for spline
chart.options.plot_options = {"spline": {"marker": {"enabled": True, "symbol": "circle"}}}

# Series with data labels at endpoints and visual hierarchy
series_list = []
for i, team in enumerate(teams):
    ranks = rankings[team]
    data_points = []
    for j, rank in enumerate(ranks):
        point = {"y": rank}
        if j == len(ranks) - 1:
            # Data label at end point showing team name
            point["dataLabels"] = {
                "enabled": True,
                "format": "{series.name}",
                "align": "left",
                "verticalAlign": "middle",
                "x": 20,
                "style": {"fontSize": "32px", "fontWeight": "bold", "color": colors[i], "textOutline": "3px white"},
            }
        data_points.append(point)

    series = SplineSeries()
    series.name = team
    series.data = data_points
    series.color = colors[i]
    series.line_width = line_widths[team]
    series.marker = {"radius": marker_radii[team], "symbol": "circle"}
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
