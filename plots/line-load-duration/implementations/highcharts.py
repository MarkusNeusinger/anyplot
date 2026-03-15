""" pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: highcharts unknown | Python 3.14.3
Quality: 81/100 | Created: 2026-03-15
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
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 250,
    "marginRight": 150,
    "marginTop": 200,
}

chart.options.title = {
    "text": "line-load-duration \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": f"Annual Load Duration Curve \u2014 Total Energy: {total_energy_gwh:,.0f} GWh",
    "style": {"fontSize": "42px", "color": "#555555"},
}

chart.options.x_axis = {
    "title": {"text": "Hours of Year (Ranked)", "style": {"fontSize": "44px"}, "margin": 30},
    "labels": {"style": {"fontSize": "34px"}, "y": 50},
    "gridLineWidth": 0,
    "min": 0,
    "max": 8760,
    "tickInterval": 1000,
    "plotBands": [
        {
            "from": 0,
            "to": peak_hours,
            "color": "rgba(0,0,0,0)",
            "label": {
                "text": "Peak Load",
                "style": {"fontSize": "36px", "color": "#c0392b", "fontWeight": "bold"},
                "y": -20,
            },
        },
        {
            "from": peak_hours,
            "to": intermediate_hours,
            "color": "rgba(0,0,0,0)",
            "label": {
                "text": "Intermediate Load",
                "style": {"fontSize": "36px", "color": "#e67e22", "fontWeight": "bold"},
                "y": -20,
            },
        },
        {
            "from": intermediate_hours,
            "to": 8760,
            "color": "rgba(0,0,0,0)",
            "label": {
                "text": "Base Load",
                "style": {"fontSize": "36px", "color": "#306998", "fontWeight": "bold"},
                "y": -20,
            },
        },
    ],
}

chart.options.y_axis = {
    "title": {"text": "Power Demand (MW)", "style": {"fontSize": "44px"}},
    "labels": {"style": {"fontSize": "34px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.08)",
    "min": 300,
    "max": 1350,
    "plotLines": [
        {
            "value": peak_capacity,
            "color": "#c0392b",
            "width": 4,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": f"Peak Capacity: {peak_capacity} MW",
                "align": "right",
                "x": -20,
                "y": -12,
                "style": {"fontSize": "32px", "color": "#c0392b", "fontWeight": "bold"},
            },
        },
        {
            "value": intermediate_capacity,
            "color": "#e67e22",
            "width": 4,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": f"Intermediate Capacity: {intermediate_capacity} MW",
                "align": "right",
                "x": -20,
                "y": -12,
                "style": {"fontSize": "32px", "color": "#e67e22", "fontWeight": "bold"},
            },
        },
        {
            "value": base_capacity,
            "color": "#306998",
            "width": 4,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": f"Base Capacity: {base_capacity} MW",
                "align": "right",
                "x": -20,
                "y": -12,
                "style": {"fontSize": "32px", "color": "#306998", "fontWeight": "bold"},
            },
        },
    ],
}

chart.options.plot_options = {
    "area": {"lineWidth": 0, "marker": {"enabled": False}, "states": {"hover": {"lineWidthPlus": 0}}, "threshold": 300}
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "34px", "fontWeight": "normal"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -40,
    "y": 100,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "style": {"fontSize": "28px"},
    "headerFormat": "<b>Hour {point.x}</b><br/>",
    "pointFormat": "Load: {point.y:.0f} MW",
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderRadius": 8,
}

# Peak load series
peak_series = AreaSeries()
peak_series.data = peak_data
peak_series.name = "Peak Load"
peak_series.color = "#c0392b"
peak_series.fill_opacity = 0.6

# Intermediate load series
intermediate_series = AreaSeries()
intermediate_series.data = intermediate_data
intermediate_series.name = "Intermediate Load"
intermediate_series.color = "#e67e22"
intermediate_series.fill_opacity = 0.6

# Base load series
base_series = AreaSeries()
base_series.data = base_data
base_series.name = "Base Load"
base_series.color = "#306998"
base_series.fill_opacity = 0.6

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
