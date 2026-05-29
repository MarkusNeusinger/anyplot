"""anyplot.ai
bump-basic: Basic Bump Chart
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-22
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.spline import SplineSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint categorical palette — positions 1-6
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data: Sports team rankings over a season (6 teams, 6 match weeks)
teams = ["Eagles", "Wolves", "Tigers", "Bears", "Sharks", "Lions"]
weeks = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"]

# Rankings per team (1 = best, 6 = worst) — overtakes, rises, falls, stability
rankings = {
    "Eagles": [3, 2, 1, 1, 2, 1],
    "Wolves": [1, 1, 2, 3, 3, 2],
    "Tigers": [4, 3, 3, 2, 1, 3],
    "Bears": [2, 4, 5, 4, 4, 4],
    "Sharks": [5, 5, 4, 5, 6, 5],
    "Lions": [6, 6, 6, 6, 5, 6],
}

# Visual hierarchy: thicker lines / larger markers for protagonists (most dramatic arcs)
line_widths = {"Eagles": 9, "Wolves": 6, "Tigers": 9, "Bears": 5, "Sharks": 4, "Lions": 4}
marker_radii = {"Eagles": 16, "Wolves": 12, "Tigers": 16, "Bears": 10, "Sharks": 9, "Lions": 9}

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "spline",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginLeft": 180,
    "marginRight": 210,
    "marginBottom": 190,
    "spacingTop": 60,
    "marginTop": 230,
}

chart.options.title = {
    "text": "bump-basic · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {"text": "League Standings Over Season", "style": {"fontSize": "44px", "color": INK_SOFT}}

chart.options.x_axis = {
    "categories": weeks,
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineWidth": 0,
    "tickWidth": 0,
    "gridLineWidth": 0,
}

# Y-axis inverted so rank 1 is at top; plotBand highlights #1 zone, plotLine marks podium boundary
chart.options.y_axis = {
    "title": {"text": "Rank", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "#{value}"},
    "reversed": True,
    "lineWidth": 0,
    "min": 0.5,
    "max": 6.5,
    "tickInterval": 1,
    "startOnTick": False,
    "endOnTick": False,
    "gridLineWidth": 1,
    "gridLineDashStyle": "Dot",
    "gridLineColor": GRID,
    "plotBands": [
        {
            "from": 0.5,
            "to": 1.5,
            "color": "rgba(0, 158, 115, 0.07)",
            "label": {
                "text": "★",
                "align": "left",
                "x": -48,
                "style": {"fontSize": "36px", "color": "rgba(0, 158, 115, 0.45)"},
            },
        }
    ],
    # plotLine is a Highcharts-specific feature: dashed separator at the podium boundary
    "plotLines": [
        {
            "value": 3.5,
            "color": INK_MUTED,
            "width": 2,
            "dashStyle": "ShortDash",
            "label": {
                "text": "Podium cutoff",
                "align": "right",
                "x": -10,
                "style": {"fontSize": "30px", "color": INK_MUTED},
            },
        }
    ],
}

chart.options.legend = {"enabled": False}
chart.options.tooltip = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.plot_options = {"spline": {"marker": {"enabled": True, "symbol": "circle"}}}

# Build series with endpoint labels and storytelling annotations at key moments
series_list = []
for i, team in enumerate(teams):
    ranks = rankings[team]
    data_points = []
    for j, rank in enumerate(ranks):
        point = {"y": rank}
        if j == len(ranks) - 1:
            # Endpoint label identifying the team
            point["dataLabels"] = {
                "enabled": True,
                "format": "{series.name}",
                "align": "left",
                "verticalAlign": "middle",
                "x": 20,
                "style": {
                    "fontSize": "36px",
                    "fontWeight": "bold",
                    "color": IMPRINT_PALETTE[i],
                    "textOutline": f"3px {PAGE_BG}",
                },
            }
        elif team == "Eagles" and j == 2:
            point["dataLabels"] = {
                "enabled": True,
                "format": "↑ Takes lead",
                "align": "center",
                "y": -42,
                "style": {
                    "fontSize": "36px",
                    "fontWeight": "normal",
                    "color": INK_SOFT,
                    "textOutline": f"2px {PAGE_BG}",
                },
            }
        elif team == "Tigers" and j == 4:
            point["dataLabels"] = {
                "enabled": True,
                "format": "↑ Peak",
                "align": "center",
                "y": -42,
                "style": {
                    "fontSize": "36px",
                    "fontWeight": "normal",
                    "color": INK_SOFT,
                    "textOutline": f"2px {PAGE_BG}",
                },
            }
        data_points.append(point)

    series = SplineSeries()
    series.name = team
    series.data = data_points
    series.color = IMPRINT_PALETTE[i]
    series.line_width = line_widths[team]
    series.marker = {"radius": marker_radii[team], "symbol": "circle"}
    series_list.append(series)

chart.options.series = series_list

# Download Highcharts JS (required — inline scripts only, CDN blocked in headless Chrome)
req = urllib.request.Request(
    "https://code.highcharts.com/highcharts.js",
    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"},
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
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

Path(f"plot-{THEME}.html").write_text(html_content, encoding="utf-8")

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative — --window-size alone loses ~139 px to Chrome chrome in headless mode
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 3200×1800 — guards against ±1-2 px CDP rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
