""" pyplots.ai
line-loss-training: Training Loss Curve
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
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


# Data - Simulate training and validation loss over epochs
np.random.seed(42)
epochs = list(range(1, 51))

# Training loss: exponential decay with small noise
train_loss = [2.5 * np.exp(-0.08 * e) + 0.15 + np.random.randn() * 0.015 for e in epochs]

# Validation loss: decays similarly but starts overfitting after epoch 28
val_base = [2.5 * np.exp(-0.065 * e) + 0.30 for e in epochs]
noise = [np.random.randn() * 0.02 for _ in epochs]
val_loss = [v + n for v, n in zip(val_base, noise, strict=True)]
# Clear overfitting after epoch 28: validation loss increases while training keeps dropping
for i in range(28, 50):
    val_loss[i] = val_loss[27] + (i - 27) * 0.35 / 22 + np.random.randn() * 0.015

# Find minimum validation loss epoch for annotation
min_val_idx = val_loss.index(min(val_loss))
min_val_epoch = epochs[min_val_idx]
min_val_loss_value = val_loss[min_val_idx]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 px with increased bottom margin for x-axis labels
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "style": {"fontFamily": "Arial, sans-serif"},
    "marginBottom": 280,
    "spacingBottom": 100,
    "spacingTop": 50,
}

# Title with larger font size for high resolution
chart.options.title = {
    "text": "line-loss-training · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle indicating optimal stopping point
chart.options.subtitle = {
    "text": f"Optimal stopping: Epoch {min_val_epoch} (Val Loss: {min_val_loss_value:.3f})",
    "style": {"fontSize": "48px"},
}

# X-axis configuration with larger fonts
chart.options.x_axis = {
    "title": {"text": "Epoch", "style": {"fontSize": "48px"}, "margin": 30},
    "labels": {"style": {"fontSize": "36px"}},
    "lineWidth": 2,
    "tickWidth": 2,
    "tickInterval": 5,
    "min": 1,
    "max": 50,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Cross-Entropy Loss", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "min": 0,
    "max": 2.8,
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "42px"},
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "top",
    "x": -50,
    "y": 150,
    "borderWidth": 1,
    "borderColor": "#e0e0e0",
    "backgroundColor": "#ffffff",
    "padding": 20,
    "itemMarginTop": 10,
    "itemMarginBottom": 10,
}

# Plot options with increased line width for visibility at high resolution
chart.options.plot_options = {
    "line": {"lineWidth": 6, "marker": {"enabled": True, "radius": 12, "lineWidth": 3, "lineColor": "#ffffff"}}
}

# Colorblind-safe colors (blue for training, yellow/gold for validation as per spec)
colors = ["#306998", "#FFD43B"]

# Add Training Loss series
series1 = LineSeries()
series1.name = "Training Loss"
series1.data = [[e, t] for e, t in zip(epochs, train_loss, strict=True)]
series1.color = colors[0]
series1.marker = {"symbol": "circle"}
chart.add_series(series1)

# Add Validation Loss series
series2 = LineSeries()
series2.name = "Validation Loss"
series2.data = [[e, v] for e, v in zip(epochs, val_loss, strict=True)]
series2.color = colors[1]
series2.marker = {"symbol": "square"}
chart.add_series(series2)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
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

# Save HTML version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Create PNG via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4800, 2700)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
