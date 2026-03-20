"""pyplots.ai
line-win-probability: Win Probability Chart
Library: highcharts unknown | Python 3.14.3
Quality: 83/100 | Created: 2026-03-20
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries, LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Simulated NFL game win probability (play-by-play)
np.random.seed(42)
n_plays = 120
play_numbers = np.arange(1, n_plays + 1)

# Simulate win probability with momentum shifts (0-100 scale)
win_prob = np.zeros(n_plays)
win_prob[0] = 50.0

# Key scoring events with realistic probability jumps
scoring_events = {
    12: ("Eagles FG 3-0", 8.0),
    28: ("Chiefs TD 7-3", -15.0),
    41: ("Eagles TD 10-7", 12.0),
    55: ("Chiefs FG 10-10", -6.0),
    68: ("Eagles TD 17-10", 14.0),
    82: ("Chiefs TD 17-17", -13.0),
    95: ("Eagles FG 20-17", 10.0),
    108: ("Chiefs FG 20-20", -9.0),
    115: ("Eagles TD 27-20", 18.0),
}

for i in range(1, n_plays):
    if i in scoring_events:
        shift = scoring_events[i][1]
    else:
        shift = np.random.normal(0, 1.2)
    win_prob[i] = np.clip(win_prob[i - 1] + shift, 2, 98)

# Force final plays to 100% (home team wins)
win_prob[-1] = 100.0
win_prob[-2] = 92.0
win_prob[-3] = 88.0

# Team colors (colorblind-safe: dark blue vs orange)
home_color = "#1B4F72"  # Eagles deep blue
away_color = "#E67E22"  # Chiefs orange

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#FAFAFA",
    "marginTop": 200,
    "marginBottom": 280,
    "marginLeft": 280,
    "marginRight": 260,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

chart.options.title = {
    "text": "line-win-probability \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold", "color": "#1a1a2e", "letterSpacing": "1px"},
    "y": 50,
}

chart.options.subtitle = {
    "text": "Eagles 27 \u2013 Chiefs 20  \u2022  Simulated NFL Game Win Probability",
    "style": {"fontSize": "42px", "color": "#555555", "letterSpacing": "0.5px"},
    "y": 125,
}

# X-axis with quarter markers
quarter_lines = []
for q, play in [(1, 30), (2, 60), (3, 90)]:
    quarter_lines.append(
        {
            "value": play,
            "color": "rgba(0,0,0,0.15)",
            "width": 2,
            "dashStyle": "Dash",
            "label": {
                "text": f"Q{q} | Q{q + 1}",
                "align": "center",
                "style": {"fontSize": "26px", "color": "#999999"},
                "rotation": 0,
                "y": 25,
            },
            "zIndex": 3,
        }
    )

chart.options.x_axis = {
    "title": {"text": "Play Number", "style": {"fontSize": "44px", "color": "#333333"}, "margin": 15},
    "labels": {"style": {"fontSize": "34px", "color": "#444444"}, "y": 40},
    "min": 1,
    "max": n_plays,
    "tickInterval": 10,
    "gridLineWidth": 0,
    "lineWidth": 2,
    "lineColor": "#cccccc",
    "tickWidth": 0,
    "plotLines": quarter_lines,
}

# Y-axis with 50% reference line
chart.options.y_axis = {
    "title": {"text": "Win Probability (%)", "style": {"fontSize": "44px", "color": "#333333"}, "margin": 30},
    "labels": {"style": {"fontSize": "34px", "color": "#444444"}, "format": "{value}%"},
    "min": 0,
    "max": 100,
    "tickInterval": 25,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.06)",
    "lineWidth": 2,
    "lineColor": "#cccccc",
    "plotLines": [
        {
            "value": 50,
            "color": "rgba(0,0,0,0.30)",
            "width": 3,
            "zIndex": 4,
            "label": {
                "text": "50%",
                "align": "right",
                "x": -10,
                "style": {"fontSize": "30px", "color": "#666666", "fontWeight": "bold"},
            },
        }
    ],
}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "left",
    "verticalAlign": "top",
    "x": 300,
    "y": 160,
    "floating": True,
    "itemStyle": {"fontSize": "34px", "fontWeight": "normal", "color": "#333333"},
    "symbolWidth": 50,
    "symbolHeight": 18,
    "itemDistance": 60,
    "backgroundColor": "rgba(250,250,250,0.85)",
    "borderRadius": 6,
    "padding": 16,
}

chart.options.tooltip = {"style": {"fontSize": "28px"}, "backgroundColor": "rgba(255,255,255,0.95)", "borderRadius": 8}

chart.options.credits = {"enabled": False}

chart.options.plot_options = {
    "area": {"lineWidth": 0, "marker": {"enabled": False}, "states": {"hover": {"lineWidthPlus": 0}}},
    "line": {"lineWidth": 4, "marker": {"enabled": False}, "states": {"hover": {"lineWidthPlus": 0}}},
    "series": {"animation": False, "turboThreshold": 0},
}

# Single area series with threshold at 50 for dual-color fill
prob_data = [[int(p), round(float(v), 2)] for p, v in zip(play_numbers, win_prob, strict=True)]

# Home team area (fills above 50%)
home_series = AreaSeries()
home_series.data = prob_data
home_series.name = "Eagles (Home)"
home_series.color = home_color
home_series.fill_color = "rgba(27, 79, 114, 0.35)"
home_series.threshold = 50
home_series.negative_color = "transparent"
home_series.negative_fill_color = "transparent"
home_series.line_width = 0
home_series.show_in_legend = True
home_series.enable_mouse_tracking = False
chart.add_series(home_series)

# Away team area (fills below 50%)
away_series = AreaSeries()
away_series.data = prob_data
away_series.name = "Chiefs (Away)"
away_series.color = "transparent"
away_series.fill_color = "transparent"
away_series.threshold = 50
away_series.negative_color = away_color
away_series.negative_fill_color = "rgba(230, 126, 34, 0.35)"
away_series.line_width = 0
away_series.show_in_legend = True
away_series.enable_mouse_tracking = False
chart.add_series(away_series)

# Main probability line on top
main_line = LineSeries()
main_line.data = prob_data
main_line.name = "Win Probability"
main_line.color = "#222222"
main_line.line_width = 4
main_line.show_in_legend = False
main_line.tooltip = {"headerFormat": "<b>Play {point.x:.0f}</b><br/>", "pointFormat": "Win Prob: {point.y:.1f}%"}
chart.add_series(main_line)

# Scoring event annotations - two series (home/away) with per-point labels
home_annotations = []
away_annotations = []
for play in sorted(scoring_events.keys()):
    label, shift = scoring_events[play]
    prob_val = round(float(win_prob[play]), 2)
    is_home = shift > 0
    # Place home labels above, away labels below; larger offset for legibility
    y_off = -35 if is_home else 40
    point = {
        "x": int(play),
        "y": prob_val,
        "dataLabels": {
            "enabled": True,
            "format": label,
            "y": y_off,
            "style": {
                "fontSize": "28px",
                "fontWeight": "bold",
                "color": home_color if is_home else away_color,
                "textOutline": "3px #ffffff",
            },
        },
    }
    if is_home:
        home_annotations.append(point)
    else:
        away_annotations.append(point)

for ann_data, color, name in [
    (home_annotations, home_color, "Home Scores"),
    (away_annotations, away_color, "Away Scores"),
]:
    s = ScatterSeries()
    s.data = ann_data
    s.name = name
    s.color = color
    s.marker = {"radius": 14, "symbol": "circle", "fillColor": "#ffffff", "lineWidth": 4, "lineColor": color}
    s.show_in_legend = False
    s.enable_mouse_tracking = False
    chart.add_series(s)

# Download Highcharts JS
highcharts_js = None
for url in ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts JS")

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

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

with open("plot.html", "w", encoding="utf-8") as fh:
    fh.write(html_content)

# Screenshot
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
