""" pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: highcharts unknown | Python 3.14.3
Quality: 84/100 | Created: 2026-03-05
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.options.series.spline import SplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data — simulated respiratory illness outbreak over ~90 days
np.random.seed(42)

start_date = pd.Timestamp("2024-01-15")
dates = pd.date_range(start_date, periods=90, freq="D")

# Point-source wave peaking ~day 20, then propagated wave peaking ~day 55
t = np.arange(90)
wave1_rate = 35 * np.exp(-0.5 * ((t - 20) / 6) ** 2)
wave2_rate = 55 * np.exp(-0.5 * ((t - 55) / 10) ** 2)
combined_rate = wave1_rate + wave2_rate + 2

confirmed_cases = np.random.poisson(combined_rate * 0.6).astype(int)
probable_cases = np.random.poisson(combined_rate * 0.25).astype(int)
suspect_cases = np.random.poisson(combined_rate * 0.15).astype(int)

cumulative = np.cumsum(confirmed_cases + probable_cases + suspect_cases)

date_labels = [d.strftime("%b %d") for d in dates]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "marginBottom": 340,
    "marginLeft": 240,
    "marginRight": 240,
    "marginTop": 240,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

chart.options.title = {
    "text": "Respiratory Illness Outbreak \u00b7 histogram-epidemic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "700", "color": "#1a1a2e"},
    "margin": 30,
}

chart.options.subtitle = {
    "text": (
        "Daily new cases by classification, Jan\u2013Apr 2024 \u00a0|\u00a0 Two-wave pattern with intervention markers"
    ),
    "style": {"fontSize": "34px", "color": "#555555", "fontWeight": "400"},
}

# X-axis — date categories with intervention plot lines
chart.options.x_axis = {
    "categories": date_labels,
    "title": {
        "text": "Symptom Onset Date",
        "style": {"fontSize": "42px", "color": "#333333", "fontWeight": "600"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#444444"}, "step": 7},
    "tickInterval": 7,
    "plotLines": [
        {
            "value": 25,
            "color": "#e74c3c",
            "width": 4,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": "Travel Advisory Issued",
                "style": {"fontSize": "28px", "color": "#e74c3c", "fontWeight": "600"},
                "rotation": 0,
                "align": "left",
                "x": 12,
                "y": 50,
            },
        },
        {
            "value": 42,
            "color": "#27ae60",
            "width": 4,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": "Vaccination Campaign",
                "style": {"fontSize": "28px", "color": "#27ae60", "fontWeight": "600"},
                "rotation": 0,
                "align": "left",
                "x": 12,
                "y": 80,
            },
        },
    ],
}

# Y-axes — primary for case counts, secondary for cumulative
chart.options.y_axis = [
    {
        "title": {
            "text": "Daily New Cases",
            "style": {"fontSize": "42px", "color": "#333333", "fontWeight": "600"},
            "margin": 20,
        },
        "labels": {"style": {"fontSize": "34px", "color": "#444444"}},
        "min": 0,
        "tickInterval": 10,
        "gridLineColor": "#e0e0e0",
        "gridLineWidth": 1,
        "gridLineDashStyle": "Dot",
    },
    {
        "title": {
            "text": "Cumulative Cases",
            "style": {"fontSize": "42px", "color": "#7f8c8d", "fontWeight": "600"},
            "margin": 20,
        },
        "labels": {"style": {"fontSize": "34px", "color": "#7f8c8d"}},
        "opposite": True,
        "min": 0,
        "gridLineWidth": 0,
    },
]

chart.options.plot_options = {
    "column": {
        "stacking": "normal",
        "pointPadding": 0,
        "groupPadding": 0.05,
        "borderWidth": 0.5,
        "borderColor": "#ffffff",
    },
    "spline": {"lineWidth": 4, "marker": {"enabled": False}},
}

chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "top",
    "floating": True,
    "y": 100,
    "itemStyle": {"fontSize": "32px", "fontWeight": "500", "color": "#333333"},
    "symbolRadius": 4,
    "symbolHeight": 20,
    "symbolWidth": 20,
}

chart.options.credits = {"enabled": False}

# Stacked bar series by case classification
confirmed_series = ColumnSeries()
confirmed_series.name = "Confirmed"
confirmed_series.data = [int(v) for v in confirmed_cases]
confirmed_series.color = "#306998"

probable_series = ColumnSeries()
probable_series.name = "Probable"
probable_series.data = [int(v) for v in probable_cases]
probable_series.color = "#f39c12"

suspect_series = ColumnSeries()
suspect_series.name = "Suspect"
suspect_series.data = [int(v) for v in suspect_cases]
suspect_series.color = "#95a5a6"

chart.add_series(confirmed_series)
chart.add_series(probable_series)
chart.add_series(suspect_series)

# Cumulative line overlay on secondary y-axis
cumulative_series = SplineSeries()
cumulative_series.name = "Cumulative Total"
cumulative_series.data = [int(v) for v in cumulative]
cumulative_series.color = "#2c3e50"
cumulative_series.y_axis = 1
cumulative_series.dash_style = "ShortDash"

chart.add_series(cumulative_series)

# Download Highcharts JS with fallback CDN
highcharts_js = None
cdn_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
for url in cdn_urls:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
            break
        except urllib.error.HTTPError:
            time.sleep(2 * (attempt + 1))
    if highcharts_js:
        break

# Render
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

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
