"""pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: highcharts unknown | Python 3.14.3
Quality: 89/100 | Created: 2026-03-16
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Retention rates for 5 monthly signup cohorts over 12 weeks
np.random.seed(42)
weeks = list(range(13))
week_labels = [f"Week {w}" for w in weeks]

cohorts = {
    "Jan 2025": {"size": 1245, "decay": 0.22},
    "Feb 2025": {"size": 1102, "decay": 0.17},
    "Mar 2025": {"size": 1380, "decay": 0.13},
    "Apr 2025": {"size": 1510, "decay": 0.09},
    "May 2025": {"size": 1625, "decay": 0.06},
}

retention_data = {}
for cohort, info in cohorts.items():
    rates = [100.0]
    for w in range(1, 13):
        drop = info["decay"] * np.exp(-0.08 * w) + 0.02
        noise = np.random.uniform(-0.015, 0.015)
        rates.append(round(max(rates[-1] * (1 - drop - noise), 5), 1))
    retention_data[cohort] = rates

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": {
        "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
        "stops": [[0, "#ffffff"], [1, "#f4f4f8"]],
    },
    "marginBottom": 260,
    "marginLeft": 220,
    "marginRight": 380,
    "marginTop": 180,
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "line-retention-cohort \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "700", "color": "#1a1a2e"},
    "margin": 30,
}

chart.options.subtitle = {
    "text": "User Retention by Monthly Signup Cohort \u2014 Newer cohorts show improving retention trends",
    "style": {"fontSize": "30px", "color": "#6c6c80", "fontWeight": "400"},
}

# X-axis
chart.options.x_axis = {
    "categories": week_labels,
    "title": {"text": "Weeks Since Signup", "style": {"fontSize": "36px", "color": "#3a3a4a", "fontWeight": "500"}},
    "labels": {"style": {"fontSize": "28px", "color": "#555566"}},
    "gridLineWidth": 0,
    "lineColor": "rgba(100, 100, 140, 0.15)",
    "lineWidth": 1,
    "tickWidth": 0,
    "crosshair": {"width": 2, "color": "rgba(100, 100, 140, 0.15)", "dashStyle": "ShortDot"},
}

# Y-axis - start at 10% to reduce empty space below threshold
chart.options.y_axis = {
    "title": {"text": "Retained Users (%)", "style": {"fontSize": "36px", "color": "#3a3a4a", "fontWeight": "500"}},
    "labels": {"style": {"fontSize": "28px", "color": "#555566"}, "format": "{value}%"},
    "min": 10,
    "max": 100,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(100, 100, 140, 0.08)",
    "gridLineDashStyle": "Dash",
    "lineWidth": 0,
    "plotLines": [
        {
            "value": 20,
            "color": "#b0413e",
            "dashStyle": "LongDash",
            "width": 4,
            "zIndex": 3,
            "label": {
                "text": "\u26a0 20% Retention Target",
                "align": "left",
                "style": {"fontSize": "26px", "color": "#b0413e", "fontWeight": "600"},
                "x": 10,
                "y": -16,
            },
        }
    ],
    "plotBands": [
        {
            "from": 10,
            "to": 20,
            "color": "rgba(176, 65, 62, 0.04)",
            "label": {
                "text": "Below Target",
                "align": "right",
                "style": {"fontSize": "22px", "color": "rgba(176, 65, 62, 0.35)"},
                "x": -15,
            },
        }
    ],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px", "fontWeight": "normal", "color": "#3a3a4a"},
    "itemHoverStyle": {"color": "#1a1a2e"},
    "symbolWidth": 70,
    "symbolHeight": 18,
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "middle",
    "x": -20,
    "itemMarginBottom": 14,
    "title": {"text": "Signup Cohort", "style": {"fontSize": "26px", "fontWeight": "600", "color": "#3a3a4a"}},
}

# Tooltip - distinctive Highcharts feature
chart.options.tooltip = {
    "shared": True,
    "valueSuffix": "%",
    "headerFormat": '<span style="font-size:24px;font-weight:bold">{point.key}</span><br/>',
    "pointFormat": '<span style="color:{series.color}">\u25cf</span> {series.name}: <b>{point.y}%</b><br/>',
    "style": {"fontSize": "20px"},
}

# Plot options
chart.options.plot_options = {
    "line": {
        "lineWidth": 5,
        "marker": {"enabled": True, "radius": 9, "lineWidth": 3, "lineColor": "#ffffff", "symbol": "circle"},
        "animation": False,
        "shadow": {"color": "rgba(0,0,0,0.06)", "offsetX": 1, "offsetY": 2, "width": 4},
        "connectNulls": True,
    }
}

# Colors - colorblind-safe palette starting with Python Blue
colors = ["#306998", "#e07b39", "#8c564b", "#7b4f8a", "#d4a84b"]

# Add series - older cohorts first (thinner, more transparent), newest last (thickest, opaque)
opacities = [0.55, 0.65, 0.75, 0.88, 1.0]
line_widths = [3, 4, 5, 6, 8]
marker_radii = [5, 6, 8, 10, 12]

for i, (cohort, rates) in enumerate(retention_data.items()):
    series = LineSeries()
    series.name = f"{cohort} (n={cohorts[cohort]['size']:,})"
    series.data = rates
    series.color = colors[i]
    series.opacity = opacities[i]
    series.line_width = line_widths[i]
    series.marker = {"radius": marker_radii[i]}
    # Zones: dash line below 20% retention target (distinctive Highcharts feature)
    series.zone_axis = "y"
    series.zones = [{"value": 20, "dashStyle": "Dot"}, {"dashStyle": "Solid"}]
    chart.add_series(series)

# Export
highcharts_url = "https://code.highcharts.com/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
