""" pyplots.ai
lift-curve: Model Lift Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-27
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Simulated customer response prediction
np.random.seed(42)
n_samples = 1000

# Generate realistic model scores and outcomes
# Good model: higher scores correlate with positive outcomes
scores = np.random.beta(2, 5, n_samples)  # Model probability scores
noise = np.random.random(n_samples)
# True positives more likely for higher scores
y_true = (scores + 0.3 * noise > 0.35).astype(int)

# Calculate lift curve data
sorted_indices = np.argsort(scores)[::-1]  # Sort by score descending
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative lift at each percentile
n_positive = y_true.sum()
baseline_rate = n_positive / n_samples
cumulative_positives = np.cumsum(y_true_sorted)
population_pct = np.arange(1, n_samples + 1) / n_samples * 100

# Lift = (cumulative response rate) / (baseline response rate)
cumulative_response_rate = cumulative_positives / np.arange(1, n_samples + 1)
lift = cumulative_response_rate / baseline_rate

# Sample at regular intervals for smooth curve (every 1%)
sample_points = list(range(0, n_samples, max(1, n_samples // 100)))
if sample_points[-1] != n_samples - 1:
    sample_points.append(n_samples - 1)

pct_sampled = [population_pct[i] for i in sample_points]
lift_sampled = [float(lift[i]) for i in sample_points]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration with proper margins
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "marginLeft": 220,
    "marginRight": 150,
    "marginTop": 180,
    "spacingBottom": 50,
}

# Title
chart.options.title = {
    "text": "lift-curve \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
    "y": 60,
}

# Subtitle with model info
chart.options.subtitle = {
    "text": f"Customer Response Model | Baseline Rate: {baseline_rate:.1%}",
    "style": {"fontSize": "36px", "color": "#666666"},
    "y": 110,
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Population Targeted (%)", "style": {"fontSize": "40px", "fontWeight": "bold"}, "margin": 30},
    "labels": {"style": {"fontSize": "32px"}},
    "min": 0,
    "max": 100,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "lineWidth": 2,
}

# Y-axis - start from 0.9 to better show the lift curve variation
chart.options.y_axis = {
    "title": {"text": "Cumulative Lift", "style": {"fontSize": "40px", "fontWeight": "bold"}, "margin": 30},
    "labels": {"style": {"fontSize": "32px"}},
    "min": 0.9,
    "max": 1.6,
    "tickInterval": 0.1,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "plotLines": [
        {
            "value": 1,
            "color": "#888888",
            "width": 4,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": "Random Selection (Lift = 1)",
                "style": {"fontSize": "28px", "color": "#666666", "fontWeight": "bold"},
                "align": "right",
                "x": -20,
                "y": 20,
            },
        }
    ],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -30,
    "y": 100,
    "symbolRadius": 6,
    "symbolWidth": 30,
    "symbolHeight": 16,
}

# Plot options
chart.options.plot_options = {"line": {"lineWidth": 6, "marker": {"enabled": False}}, "series": {"animation": False}}

# Create lift curve series
lift_series = LineSeries()
lift_series.name = "Model Lift"
lift_series.data = [[pct_sampled[i], lift_sampled[i]] for i in range(len(pct_sampled))]
lift_series.color = "#306998"  # Python Blue
lift_series.marker = {"enabled": True, "radius": 8, "symbol": "circle"}
lift_series.lineWidth = 6

chart.add_series(lift_series)

# Add key decile annotations as a single series with data labels
decile_points = [10, 20, 30, 50]
annotation_data = []
for pct in decile_points:
    idx = min(int(pct * n_samples / 100) - 1, n_samples - 1)
    lift_val = lift[idx]
    annotation_data.append(
        {
            "x": pct,
            "y": float(lift_val),
            "dataLabels": {
                "enabled": True,
                "format": f"{lift_val:.2f}x",
                "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#306998"},
                "y": -30,
                "backgroundColor": "rgba(255, 255, 255, 0.8)",
                "borderRadius": 5,
                "padding": 8,
            },
        }
    )

annotation_series = ScatterSeries()
annotation_series.name = "Key Percentiles"
annotation_series.data = annotation_data
annotation_series.color = "#FFD43B"  # Python Yellow
annotation_series.marker = {
    "enabled": True,
    "radius": 14,
    "symbol": "diamond",
    "fillColor": "#FFD43B",
    "lineColor": "#306998",
    "lineWidth": 3,
}

chart.add_series(annotation_series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Get the chart options as JS - avoid DOMContentLoaded wrapper issue
js_literal = chart.to_js_literal()
# Remove the DOMContentLoaded wrapper if present
if "DOMContentLoaded" in js_literal:
    # Extract just the Highcharts.chart(...) call
    import re

    match = re.search(r"(Highcharts\.chart\([^;]+\));", js_literal, re.DOTALL)
    if match:
        js_literal = match.group(1) + ";"

# Generate HTML with inline scripts - use window.onload for reliable rendering
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    window.onload = function() {{
        {js_literal}
    }};
    </script>
</body>
</html>"""

# Save HTML version
with open("plot.html", "w", encoding="utf-8") as f:
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
