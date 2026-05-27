""" anyplot.ai
bar-spine: Spine Plot for Two-Variable Proportions
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Created: 2026-05-08
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Annual customer satisfaction survey (n=5,000) across industry sectors
sectors = ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing"]
ratings = ["Excellent", "Good", "Fair", "Poor"]

counts = np.array(
    [
        [380, 520, 210, 90],  # Technology  — 1,200 respondents
        [290, 380, 250, 180],  # Healthcare  — 1,100 respondents
        [160, 290, 270, 180],  # Finance     — 900 respondents
        [140, 310, 300, 250],  # Retail      — 1,000 respondents
        [100, 220, 320, 160],  # Manufacturing — 800 respondents
    ],
    dtype=float,
)

marginal = counts.sum(axis=1)
total = marginal.sum()
widths = marginal / total
cum = np.concatenate([[0.0], np.cumsum(widths)])
centers = (cum[:-1] + cum[1:]) / 2.0
cond_props = np.round(counts / marginal[:, np.newaxis] * 100.0, 2)

# Plot area width: chart 4800px minus margins
MARGIN_LEFT = 160
MARGIN_RIGHT = 80
PLOT_WIDTH = float(4800 - MARGIN_LEFT - MARGIN_RIGHT)

# Build sector labels via x-axis plotLines (no JS formatter needed)
plot_lines = []
for j, sector in enumerate(sectors):
    plot_lines.append(
        {
            "value": float(centers[j]),
            "color": "rgba(0,0,0,0)",
            "width": 0,
            "label": {
                "text": f"{sector} (n={int(marginal[j]):,})",
                "align": "center",
                "verticalAlign": "bottom",
                "rotation": 0,
                "y": 30,
                "style": {"fontSize": "20px", "color": INK_SOFT},
            },
        }
    )

# Build chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginLeft": MARGIN_LEFT,
    "marginRight": MARGIN_RIGHT,
    "marginBottom": 220,
    "marginTop": 100,
}

chart.options.title = {
    "text": "Customer Satisfaction by Industry · bar-spine · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "bold"},
}

chart.options.x_axis = {
    "type": "linear",
    "min": 0,
    "max": 1,
    "startOnTick": False,
    "endOnTick": False,
    "minPadding": 0,
    "maxPadding": 0,
    "tickLength": 0,
    "labels": {"enabled": False},
    "title": {
        "text": "Industry Sector  (bar width proportional to survey count)",
        "style": {"fontSize": "22px", "color": INK},
        "margin": 80,
    },
    "lineColor": INK_SOFT,
    "gridLineWidth": 0,
    "plotLines": plot_lines,
}

chart.options.y_axis = {
    "min": 0,
    "max": 100,
    "endOnTick": False,
    "maxPadding": 0,
    "tickInterval": 20,
    "title": {"text": "Proportion of Respondents (%)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"format": "{value}%", "style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

chart.options.plot_options = {
    "column": {
        "stacking": "normal",
        "grouping": False,
        "pointPadding": 0,
        "groupPadding": 0,
        "borderWidth": 1,
        "borderColor": PAGE_BG,
    }
}

chart.options.legend = {
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -40,
    "y": 80,
    "itemStyle": {"fontSize": "18px", "fontWeight": "normal", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 20,
    "itemMarginBottom": 10,
    "title": {"text": "Satisfaction Level", "style": {"fontSize": "18px", "fontWeight": "bold", "color": INK}},
}

chart.options.tooltip = {
    "shared": False,
    "headerFormat": "<b>{point.key}</b><br/>",
    "pointFormat": '<span style="color:{point.color}">●</span> {series.name}: <b>{point.y:.1f}%</b><br/>',
    "style": {"fontSize": "16px"},
}

# Add one series per satisfaction rating (stacked bottom-to-top: best first)
for i, (rating, color) in enumerate(zip(ratings, IMPRINT, strict=True)):
    series = ColumnSeries()
    series.name = rating
    series.color = color
    series.data = [
        {
            "x": float(centers[j]),
            "y": float(cond_props[j, i]),
            "name": sectors[j],
            "pointWidth": round(float(widths[j] * PLOT_WIDTH), 1),
        }
        for j in range(len(sectors))
    ]
    chart.add_series(series)

# Download Highcharts JS (must be inline for headless Chrome file:// loading)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
