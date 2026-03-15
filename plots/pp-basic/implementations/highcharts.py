"""pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: highcharts unknown | Python 3.14.3
Quality: 79/100 | Created: 2026-03-15
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from scipy.stats import norm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - slightly skewed sample to show P-P plot deviation from diagonal
np.random.seed(42)
n = 200
sample = np.concatenate([np.random.normal(0, 1, 160), np.random.exponential(0.8, 40)])
np.random.shuffle(sample)

# Compute P-P values
sample_sorted = np.sort(sample)
mu, sigma = norm.fit(sample)
empirical_cdf = (np.arange(1, n + 1)) / (n + 1)
theoretical_cdf = norm.cdf(sample_sorted, loc=mu, scale=sigma)

# Compute deviation from diagonal for color coding
deviation = np.abs(empirical_cdf - theoretical_cdf)
max_dev = deviation.max()

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#fafbfc",
    "borderWidth": 0,
    "plotBorderWidth": 2,
    "plotBorderColor": "#d0d7de",
    "spacing": [60, 80, 80, 80],
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "pp-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "600", "color": "#1a1a2e"},
    "margin": 50,
}

chart.options.subtitle = {
    "text": "Mixed Normal + Exponential vs. Normal Reference \u2014 Deviation Highlights Distributional Mismatch",
    "style": {"fontSize": "34px", "color": "#57606a"},
}

# Confidence band as plotBand on y-axis
confidence_band_color = "rgba(48, 105, 152, 0.06)"

chart.options.x_axis = {
    "title": {
        "text": "Theoretical CDF (Normal)",
        "style": {"fontSize": "44px", "color": "#1a1a2e", "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "34px", "color": "#57606a"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.08)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#d0d7de",
    "lineWidth": 1,
    "tickColor": "#d0d7de",
    "min": 0,
    "max": 1,
    "tickInterval": 0.2,
    "plotLines": [{"value": 0.5, "color": "rgba(0, 0, 0, 0.12)", "width": 2, "dashStyle": "LongDash", "zIndex": 1}],
    "plotBands": [
        {
            "from": 0.3,
            "to": 0.7,
            "color": confidence_band_color,
            "label": {
                "text": "Central region",
                "style": {"fontSize": "28px", "color": "rgba(48, 105, 152, 0.4)"},
                "align": "left",
                "x": 20,
                "y": -15,
            },
        }
    ],
}

chart.options.y_axis = {
    "title": {
        "text": "Empirical CDF",
        "style": {"fontSize": "44px", "color": "#1a1a2e", "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "34px", "color": "#57606a"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.08)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#d0d7de",
    "lineWidth": 1,
    "tickColor": "#d0d7de",
    "min": 0,
    "max": 1,
    "tickInterval": 0.2,
    "plotLines": [{"value": 0.5, "color": "rgba(0, 0, 0, 0.12)", "width": 2, "dashStyle": "LongDash", "zIndex": 1}],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px", "fontWeight": "normal", "color": "#1a1a2e"},
    "itemHoverStyle": {"color": "#306998"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -40,
    "y": 80,
    "backgroundColor": "rgba(255, 255, 255, 0.85)",
    "borderColor": "#d0d7de",
    "borderWidth": 1,
    "borderRadius": 8,
    "padding": 16,
    "shadow": False,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:28px;color:{point.color}">\u25cf</span> '
        '<span style="font-size:28px"><b>Point {point.index}</b></span><br/>'
        '<span style="font-size:26px">Theoretical: <b>{point.x:.3f}</b></span><br/>'
        '<span style="font-size:26px">Empirical: <b>{point.y:.3f}</b></span><br/>'
        '<span style="font-size:26px">Deviation: <b>{point.dev:.3f}</b></span>'
    ),
    "backgroundColor": "rgba(255, 255, 255, 0.96)",
    "borderColor": "#d0d7de",
    "borderRadius": 8,
    "shadow": {"color": "rgba(0,0,0,0.1)", "offsetX": 2, "offsetY": 2, "width": 4},
    "style": {"fontSize": "26px"},
}

# Reference line (perfect fit diagonal)
line_series = LineSeries()
line_series.data = [[0.0, 0.0], [1.0, 1.0]]
line_series.name = "Perfect Fit (y=x)"
line_series.color = "#2da44e"
line_series.line_width = 5
line_series.marker = {"enabled": False}
line_series.enable_mouse_tracking = False
line_series.dash_style = "LongDash"
line_series.z_index = 0

chart.add_series(line_series)

# P-P scatter points with deviation-based coloring
scatter_data = []
for t, e, d in zip(theoretical_cdf, empirical_cdf, deviation, strict=True):
    ratio = d / max_dev if max_dev > 0 else 0
    # Interpolate from Python Blue (close to diagonal) to warm coral (far from diagonal)
    r = int(48 + ratio * (207 - 48))
    g = int(105 + ratio * (72 - 105))
    b = int(152 + ratio * (65 - 152))
    alpha = 0.55 + ratio * 0.35
    scatter_data.append(
        {"x": float(t), "y": float(e), "dev": round(float(d), 4), "color": f"rgba({r},{g},{b},{alpha})"}
    )

scatter_series = ScatterSeries()
scatter_series.data = scatter_data
scatter_series.name = "P-P Points (N=200)"
scatter_series.color = "#306998"
scatter_series.marker = {"radius": 9, "symbol": "circle", "lineWidth": 1, "lineColor": "rgba(0,0,0,0.15)"}
scatter_series.z_index = 2

chart.add_series(scatter_series)

# Load Highcharts JS for inline embedding
highcharts_js_path = Path(__file__).resolve().parents[3] / "node_modules" / "highcharts" / "highcharts.js"
if highcharts_js_path.exists():
    highcharts_js = highcharts_js_path.read_text(encoding="utf-8")
else:
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
    <div id="container" style="width: 3600px; height: 3600px;"></div>
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
chrome_options.add_argument("--window-size=3600,3700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
