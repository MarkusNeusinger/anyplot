""" anyplot.ai
lift-curve: Model Lift Chart
Library: highcharts unknown | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-10
"""

import os
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


# Theme-adaptive colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data: Simulated customer churn prediction
np.random.seed(42)
n_samples = 1000

# Generate realistic model scores with better variation
# Scores follow a mixture of two distributions for more realistic separation
scores = np.concatenate(
    [
        np.random.beta(2.5, 4, n_samples // 2),  # Better model scores
        np.random.beta(1, 4, n_samples // 2),  # Weaker model scores
    ]
)
np.random.shuffle(scores)

# True outcomes correlate with scores (but not perfectly)
noise = np.random.random(n_samples)
y_true = (scores > (0.4 - 0.15 * noise)).astype(int)

# Calculate lift curve data
sorted_indices = np.argsort(scores)[::-1]
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative lift at each percentile
n_positive = y_true.sum()
baseline_rate = n_positive / n_samples
cumulative_positives = np.cumsum(y_true_sorted)
population_pct = np.arange(1, n_samples + 1) / n_samples * 100

# Lift = (cumulative response rate) / (baseline response rate)
cumulative_response_rate = cumulative_positives / np.arange(1, n_samples + 1)
lift = cumulative_response_rate / baseline_rate

# Sample at regular intervals for smooth curve
sample_points = list(range(0, n_samples, max(1, n_samples // 100)))
if sample_points[-1] != n_samples - 1:
    sample_points.append(n_samples - 1)

pct_sampled = [population_pct[i] for i in sample_points]
lift_sampled = [float(lift[i]) for i in sample_points]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginLeft": 220,
    "marginRight": 200,
    "marginTop": 200,
}

# Title
chart.options.title = {
    "text": "lift-curve · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "600"},
    "y": 30,
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Population Targeted (%)", "style": {"fontSize": "22px", "color": INK, "fontWeight": "600"}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0,
    "max": 100,
    "tickInterval": 10,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": RULE,
    "gridLineWidth": 0,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Cumulative Lift", "style": {"fontSize": "22px", "color": INK, "fontWeight": "600"}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0.9,
    "max": 1.8,
    "tickInterval": 0.2,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": RULE,
    "gridLineWidth": 1,
    "plotLines": [
        {
            "value": 1,
            "color": INK_SOFT,
            "width": 2,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": "Random Selection",
                "style": {"fontSize": "18px", "color": INK_SOFT},
                "align": "left",
                "x": 10,
                "y": -8,
            },
        }
    ],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 4,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -30,
    "y": 50,
}

# Plot options
chart.options.plot_options = {"line": {"lineWidth": 5, "marker": {"enabled": False}}, "series": {"animation": False}}

# Create lift curve series (Okabe-Ito brand color)
lift_series = LineSeries()
lift_series.name = "Model Lift"
lift_series.data = [[pct_sampled[i], lift_sampled[i]] for i in range(len(pct_sampled))]
lift_series.color = BRAND
lift_series.lineWidth = 5

chart.add_series(lift_series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://code.highcharts.com/"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Export to PNG via Selenium
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
