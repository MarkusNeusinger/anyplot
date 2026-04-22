""" pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: highcharts unknown | Python 3.14.3
Quality: 87/100 | Created: 2026-03-14
"""

import re
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
from statsmodels.tsa.stattools import acf, pacf


# Data - Generate an AR(2) process for clear ACF/PACF patterns
np.random.seed(42)
n_obs = 200
noise = np.random.normal(0, 1, n_obs)
series = np.zeros(n_obs)
series[0] = noise[0]
series[1] = noise[1]
for i in range(2, n_obs):
    series[i] = 0.6 * series[i - 1] - 0.3 * series[i - 2] + noise[i]

# Compute ACF and PACF
n_lags = 35
acf_values = acf(series, nlags=n_lags, fft=True)
pacf_values = pacf(series, nlags=n_lags, method="ywm")
confidence_bound = 1.96 / np.sqrt(n_obs)
lags = list(range(n_lags + 1))
pacf_lags = list(range(1, n_lags + 1))

# Colors - colorblind-friendly blue/orange
COLOR_NONSIG = "#306998"
COLOR_SIG = "#e67e22"
COLOR_LAG0 = "#1a4971"
COLOR_CONF = "#d35400"

# Build chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginTop": 140,
    "marginBottom": 310,
    "marginLeft": 280,
    "marginRight": 180,
    "style": {"fontFamily": "Arial, Helvetica, sans-serif"},
    "animation": {"duration": 800, "easing": "easeOutBounce"},
}

# Title
chart.options.title = {
    "text": "acf-pacf \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "52px", "fontWeight": "bold", "color": "#2c3e50"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "AR(2) Process \u2014 Exponential ACF Decay with PACF Cutoff at Lag 2",
    "style": {"fontSize": "32px", "color": "#7f8c8d", "fontWeight": "normal"},
}

# Tighter y-axis ranges, reduced gap between panels
acf_min_val = float(np.min(acf_values))
acf_max_val = float(np.max(acf_values))
pacf_min_val = float(np.min(pacf_values[1:]))
pacf_max_val = float(np.max(pacf_values[1:]))

chart.options.y_axis = [
    {
        "title": {"text": "ACF", "style": {"fontSize": "34px", "color": "#306998", "fontWeight": "bold"}, "margin": 20},
        "labels": {"style": {"fontSize": "24px", "color": "#555555"}, "format": "{value:.1f}"},
        "top": "5%",
        "height": "43%",
        "offset": 0,
        "min": round(min(acf_min_val, -confidence_bound) - 0.08, 1),
        "max": 1.05,
        "endOnTick": False,
        "startOnTick": False,
        "tickInterval": 0.2,
        "gridLineColor": "#eeeeee",
        "gridLineWidth": 1,
        "plotLines": [
            {"value": 0, "color": "#999999", "width": 2, "zIndex": 3},
            {
                "value": confidence_bound,
                "color": COLOR_CONF,
                "width": 3,
                "dashStyle": "Dash",
                "zIndex": 3,
                "label": {
                    "text": "95% CI",
                    "align": "left",
                    "style": {"fontSize": "20px", "color": COLOR_CONF, "fontWeight": "bold"},
                    "x": 100,
                    "y": -8,
                },
            },
            {"value": -confidence_bound, "color": COLOR_CONF, "width": 3, "dashStyle": "Dash", "zIndex": 3},
        ],
    },
    {
        "title": {
            "text": "PACF",
            "style": {"fontSize": "34px", "color": "#306998", "fontWeight": "bold"},
            "margin": 20,
        },
        "labels": {"style": {"fontSize": "24px", "color": "#555555"}, "format": "{value:.1f}"},
        "top": "52%",
        "height": "43%",
        "offset": 0,
        "min": round(min(pacf_min_val, -confidence_bound) - 0.08, 1),
        "max": round(max(pacf_max_val, confidence_bound) + 0.1, 1),
        "endOnTick": False,
        "startOnTick": False,
        "tickInterval": 0.2,
        "gridLineColor": "#eeeeee",
        "gridLineWidth": 1,
        "plotLines": [
            {"value": 0, "color": "#999999", "width": 2, "zIndex": 3},
            {"value": confidence_bound, "color": COLOR_CONF, "width": 3, "dashStyle": "Dash", "zIndex": 3},
            {"value": -confidence_bound, "color": COLOR_CONF, "width": 3, "dashStyle": "Dash", "zIndex": 3},
        ],
    },
]

# X-axes: top panel hides labels, bottom panel shows Lag labels
chart.options.x_axis = [
    {
        "title": {"text": None},
        "labels": {"enabled": False},
        "lineColor": "#cccccc",
        "lineWidth": 1,
        "tickInterval": 5,
        "min": -0.5,
        "max": n_lags + 0.5,
    },
    {
        "title": {"text": "Lag", "style": {"fontSize": "36px", "color": "#555555"}, "margin": 25},
        "labels": {"style": {"fontSize": "28px", "color": "#555555"}},
        "lineColor": "#cccccc",
        "lineWidth": 1,
        "tickInterval": 5,
        "min": -0.5,
        "max": n_lags + 0.5,
    },
]

# Color bars based on significance, add data labels on significant bars
acf_data = []
for i, val in enumerate(acf_values):
    is_sig = abs(val) > confidence_bound and i > 0
    color = COLOR_SIG if is_sig else COLOR_NONSIG
    point = {"x": i, "y": round(float(val), 4), "color": color}
    if i == 0:
        point["color"] = COLOR_LAG0
        point["dataLabels"] = {
            "enabled": True,
            "format": "r=1.0",
            "style": {"fontSize": "18px", "color": COLOR_LAG0, "fontWeight": "bold", "textOutline": "none"},
        }
    elif is_sig:
        point["dataLabels"] = {
            "enabled": True,
            "format": "{y:.2f}",
            "style": {"fontSize": "18px", "color": COLOR_SIG, "fontWeight": "bold", "textOutline": "none"},
        }
    acf_data.append(point)

pacf_data = []
for i, val in enumerate(pacf_values[1:], start=1):
    is_sig = abs(val) > confidence_bound
    color = COLOR_SIG if is_sig else COLOR_NONSIG
    point = {"x": i, "y": round(float(val), 4), "color": color}
    if is_sig:
        point["dataLabels"] = {
            "enabled": True,
            "format": "{y:.2f}",
            "style": {"fontSize": "18px", "color": COLOR_SIG, "fontWeight": "bold", "textOutline": "none"},
        }
    pacf_data.append(point)

# ACF series (top panel, yAxis 0, xAxis 0)
acf_series = ColumnSeries.from_dict(
    {
        "data": acf_data,
        "name": "ACF",
        "type": "column",
        "yAxis": 0,
        "xAxis": 0,
        "pointWidth": 22,
        "borderWidth": 0,
        "groupPadding": 0,
        "pointPadding": 0,
        "showInLegend": False,
        "animation": {"duration": 1000},
        "states": {"hover": {"brightness": 0.15, "borderWidth": 2, "borderColor": "#2c3e50"}},
    }
)
chart.add_series(acf_series)

# PACF series (bottom panel, yAxis 1, xAxis 1)
pacf_series = ColumnSeries.from_dict(
    {
        "data": pacf_data,
        "name": "PACF",
        "type": "column",
        "yAxis": 1,
        "xAxis": 1,
        "pointWidth": 22,
        "borderWidth": 0,
        "groupPadding": 0,
        "pointPadding": 0,
        "showInLegend": False,
        "animation": {"duration": 1000},
        "states": {"hover": {"brightness": 0.15, "borderWidth": 2, "borderColor": "#2c3e50"}},
    }
)
chart.add_series(pacf_series)

# Rich HTML tooltip - distinctive Highcharts feature
chart.options.tooltip = {
    "useHTML": True,
    "headerFormat": '<table style="font-size:20px;min-width:200px;">',
    "pointFormat": '<tr><td style="padding:4px 8px;color:{point.color};font-weight:bold;">'
    "Lag {point.x}</td>"
    '<td style="padding:4px 8px;text-align:right;"><b>{point.y:.4f}</b></td></tr>',
    "footerFormat": "</table>",
    "backgroundColor": "rgba(255, 255, 255, 0.96)",
    "borderColor": "#306998",
    "borderRadius": 10,
    "borderWidth": 2,
    "shadow": {"color": "rgba(0,0,0,0.15)", "offsetX": 2, "offsetY": 2, "width": 5},
    "style": {"fontSize": "20px"},
}

# Plot options with animation
chart.options.plot_options = {
    "column": {
        "borderRadius": 3,
        "animation": {"duration": 1000},
        "dataLabels": {"allowOverlap": False, "crop": False, "overflow": "allow"},
    }
}

# Legend explaining significance colors
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "horizontal",
    "floating": True,
    "x": -40,
    "y": 70,
    "itemStyle": {"fontSize": "22px", "fontWeight": "normal", "color": "#555555"},
    "symbolRadius": 4,
    "symbolHeight": 16,
    "symbolWidth": 16,
    "itemDistance": 40,
}

# Add invisible series for legend entries
sig_legend = ColumnSeries.from_dict(
    {"name": "Significant (|r| > 95% CI)", "data": [], "color": COLOR_SIG, "showInLegend": True, "type": "column"}
)
chart.add_series(sig_legend)

nonsig_legend = ColumnSeries.from_dict(
    {"name": "Non-significant", "data": [], "color": COLOR_NONSIG, "showInLegend": True, "type": "column"}
)
chart.add_series(nonsig_legend)

chart.options.credits = {"enabled": False}

# Download Highcharts JS (try multiple CDNs, fall back to local npm)
highcharts_js = None
for url in ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
            break
    except Exception:
        continue
if highcharts_js is None:
    local_paths = [
        Path(__file__).resolve().parent.parent.parent.parent / "node_modules" / "highcharts" / "highcharts.js",
        Path("node_modules/highcharts/highcharts.js"),
    ]
    for p in local_paths:
        if p.exists():
            highcharts_js = p.read_text(encoding="utf-8")
            break
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS from CDN or find local copy")

# Generate JS and fix format strings
chart_js = chart.to_js_literal()
chart_js = re.sub(r"format: (\{[^}]+\})", r"format: '\1'", chart_js)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Write temp HTML
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML for interactive viewing (uses CDN for portability)
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>acf-pacf \u00b7 highcharts \u00b7 pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <style>
        body {{ margin: 0; padding: 20px; font-family: sans-serif; background: #fff; }}
        #container {{ width: 100%; height: 90vh; min-height: 600px; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script>{chart_js}</script>
</body>
</html>""")

# Take screenshot with headless Chrome
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

# Clean up
Path(temp_path).unlink()
