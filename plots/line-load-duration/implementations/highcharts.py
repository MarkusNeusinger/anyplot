""" pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: highcharts unknown | Python 3.14.3
Quality: 91/100 | Created: 2026-03-15
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Synthetic annual hourly load profile for a mid-sized utility
np.random.seed(42)
hours_in_year = 8760

# Build realistic load profile with daily/seasonal patterns
hour_of_day = np.arange(hours_in_year) % 24
day_of_year = np.arange(hours_in_year) // 24

base_load = 400
seasonal_component = 250 * np.sin(2 * np.pi * day_of_year / 365 - np.pi / 2) + 250
daily_component = 150 * np.sin(2 * np.pi * (hour_of_day - 6) / 24) + 50
peak_spikes = np.where(
    (hour_of_day >= 14) & (hour_of_day <= 18) & (day_of_year > 150) & (day_of_year < 250),
    np.random.uniform(50, 200, hours_in_year),
    0,
)
noise = np.random.normal(0, 30, hours_in_year)

load_profile = base_load + seasonal_component + daily_component + peak_spikes + noise
load_profile = np.clip(load_profile, 350, 1300)

# Sort descending for load duration curve
load_sorted = np.sort(load_profile)[::-1]
hours_ranked = np.arange(hours_in_year)

# Define capacity tier boundaries
peak_capacity = 1100
intermediate_capacity = 750
base_capacity = 500

# Find hour indices where load crosses each tier
peak_hours = int(np.searchsorted(-load_sorted, -peak_capacity))
intermediate_hours = int(np.searchsorted(-load_sorted, -intermediate_capacity))

# Total energy consumption (area under curve in MWh)
total_energy_gwh = np.trapezoid(load_sorted) / 1000

# Build series data for three regions
peak_data = [[int(h), round(float(load_sorted[h]), 1)] for h in range(peak_hours + 1)]
intermediate_data = [[int(h), round(float(load_sorted[h]), 1)] for h in range(peak_hours, intermediate_hours + 1)]
base_data = [[int(h), round(float(load_sorted[h]), 1)] for h in range(intermediate_hours, hours_in_year)]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafafa",
    "marginBottom": 260,
    "marginLeft": 240,
    "marginRight": 160,
    "marginTop": 200,
}

chart.options.title = {
    "text": "line-load-duration \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "700", "fontFamily": "Georgia, serif", "color": "#1a1a2e"},
}

chart.options.subtitle = {
    "text": f"Annual Load Duration Curve \u2014 Total Energy: {total_energy_gwh:,.0f} GWh",
    "style": {"fontSize": "44px", "color": "#444444", "fontFamily": "Georgia, serif", "fontStyle": "italic"},
}

chart.options.x_axis = {
    "title": {"text": "Hours of Year (Ranked)", "style": {"fontSize": "44px", "color": "#333333"}, "margin": 40},
    "labels": {"style": {"fontSize": "34px", "color": "#333333"}},
    "gridLineWidth": 0,
    "lineColor": "#999999",
    "lineWidth": 2,
    "min": 0,
    "max": 8760,
    "tickInterval": 1000,
    "tickColor": "#999999",
    "plotBands": [
        {
            "from": 0,
            "to": peak_hours,
            "color": "rgba(192, 57, 43, 0.06)",
            "label": {
                "text": f"Peak<br/>{peak_hours} hrs",
                "style": {"fontSize": "34px", "color": "#c0392b", "fontWeight": "bold"},
                "y": -15,
            },
        },
        {
            "from": peak_hours,
            "to": intermediate_hours,
            "color": "rgba(142, 68, 173, 0.06)",
            "label": {
                "text": f"Intermediate<br/>{intermediate_hours - peak_hours:,} hrs",
                "style": {"fontSize": "34px", "color": "#7d3c98", "fontWeight": "bold"},
                "y": -15,
            },
        },
        {
            "from": intermediate_hours,
            "to": 8760,
            "color": "rgba(48, 105, 152, 0.06)",
            "label": {
                "text": f"Base Load<br/>{8760 - intermediate_hours:,} hrs",
                "style": {"fontSize": "34px", "color": "#306998", "fontWeight": "bold"},
                "y": -15,
            },
        },
    ],
}

chart.options.y_axis = {
    "title": {"text": "Power Demand (MW)", "style": {"fontSize": "44px", "color": "#333333"}},
    "labels": {"style": {"fontSize": "34px", "color": "#333333"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.08)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#999999",
    "lineWidth": 2,
    "min": 300,
    "max": 1350,
    "tickInterval": 100,
    "plotLines": [
        {
            "value": peak_capacity,
            "color": "#c0392b",
            "width": 4,
            "dashStyle": "LongDash",
            "zIndex": 5,
            "label": {
                "text": f"Peak Capacity: {peak_capacity} MW",
                "align": "left",
                "x": 20,
                "y": -14,
                "style": {"fontSize": "30px", "color": "#c0392b", "fontWeight": "bold"},
            },
        },
        {
            "value": intermediate_capacity,
            "color": "#7d3c98",
            "width": 4,
            "dashStyle": "LongDash",
            "zIndex": 5,
            "label": {
                "text": f"Intermediate Capacity: {intermediate_capacity} MW",
                "align": "left",
                "x": 20,
                "y": -14,
                "style": {"fontSize": "30px", "color": "#7d3c98", "fontWeight": "bold"},
            },
        },
        {
            "value": base_capacity,
            "color": "#306998",
            "width": 4,
            "dashStyle": "LongDash",
            "zIndex": 5,
            "label": {
                "text": f"Base Capacity: {base_capacity} MW",
                "align": "left",
                "x": 20,
                "y": -14,
                "style": {"fontSize": "30px", "color": "#306998", "fontWeight": "bold"},
            },
        },
    ],
}

chart.options.plot_options = {
    "area": {
        "lineWidth": 3,
        "lineColor": None,
        "marker": {"enabled": False},
        "states": {"hover": {"lineWidthPlus": 0}},
        "threshold": 300,
    }
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px", "fontWeight": "normal", "color": "#333333"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 80,
    "backgroundColor": "rgba(255,255,255,0.85)",
    "borderRadius": 8,
    "padding": 20,
    "symbolRadius": 4,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "style": {"fontSize": "28px"},
    "headerFormat": "<b>Hour {point.x}</b><br/>",
    "pointFormat": "Load: {point.y:.0f} MW",
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderRadius": 8,
}

# Peak load series with gradient fill
peak_series = AreaSeries()
peak_series.data = peak_data
peak_series.name = "Peak Load"
peak_series.color = "#c0392b"
peak_series.fill_color = {
    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
    "stops": [[0, "rgba(192, 57, 43, 0.75)"], [1, "rgba(192, 57, 43, 0.15)"]],
}

# Intermediate load series with gradient fill
intermediate_series = AreaSeries()
intermediate_series.data = intermediate_data
intermediate_series.name = "Intermediate Load"
intermediate_series.color = "#7d3c98"
intermediate_series.fill_color = {
    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
    "stops": [[0, "rgba(125, 60, 152, 0.65)"], [1, "rgba(125, 60, 152, 0.1)"]],
}

# Base load series with gradient fill
base_series = AreaSeries()
base_series.data = base_data
base_series.name = "Base Load"
base_series.color = "#306998"
base_series.fill_color = {
    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
    "stops": [[0, "rgba(48, 105, 152, 0.6)"], [1, "rgba(48, 105, 152, 0.08)"]],
}

chart.add_series(peak_series)
chart.add_series(intermediate_series)
chart.add_series(base_series)

# Save interactive HTML
html_str = chart.to_js_literal()

highcharts_js_path = Path(__file__).resolve().parents[3] / "node_modules" / "highcharts" / "highcharts.js"
if highcharts_js_path.exists():
    highcharts_js = highcharts_js_path.read_text(encoding="utf-8")
else:
    highcharts_url = "https://code.highcharts.com/highcharts.js"
    req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")

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

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with headless Chrome
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
