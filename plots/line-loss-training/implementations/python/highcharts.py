""" anyplot.ai
line-loss-training: Training Loss Curve
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-14
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"  # Training loss (first series)
SECONDARY = "#C475FD"  # Validation loss

# Data - Simulate training and validation loss over epochs
np.random.seed(42)
epochs = list(range(1, 51))

# Training loss: exponential decay with small noise
train_loss = [2.5 * np.exp(-0.08 * e) + 0.15 + np.random.randn() * 0.015 for e in epochs]

# Validation loss: decays similarly but starts overfitting after epoch 28
val_base = [2.5 * np.exp(-0.065 * e) + 0.30 for e in epochs]
noise = [np.random.randn() * 0.02 for _ in epochs]
val_loss = [v + n for v, n in zip(val_base, noise, strict=True)]
for i in range(28, 50):
    val_loss[i] = val_loss[27] + (i - 27) * 0.35 / 22 + np.random.randn() * 0.015

# Find minimum validation loss epoch
min_val_idx = val_loss.index(min(val_loss))
min_val_epoch = epochs[min_val_idx]
min_val_loss_value = val_loss[min_val_idx]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "Arial, sans-serif"},
    "marginBottom": 100,
    "spacingBottom": 50,
    "spacingTop": 50,
}

# Title
chart.options.title = {
    "text": "line-loss-training · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "medium", "color": INK},
}

# Subtitle indicating optimal stopping point
chart.options.subtitle = {
    "text": f"Optimal stopping: Epoch {min_val_epoch} (Val Loss: {min_val_loss_value:.3f})",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis configuration
chart.options.x_axis = {
    "title": {"text": "Epoch", "style": {"fontSize": "22px", "color": INK}, "margin": 15},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "tickInterval": 5,
    "min": 1,
    "max": 50,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Cross-Entropy Loss", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "min": 0,
    "max": 2.8,
}

# Legend configuration - moved to bottom for better layout
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "y": -40,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "backgroundColor": ELEVATED_BG,
    "padding": 12,
    "itemMarginRight": 30,
}

# Plot options with appropriate line width for visibility
chart.options.plot_options = {
    "line": {"lineWidth": 3, "marker": {"enabled": True, "radius": 8, "lineWidth": 2, "lineColor": PAGE_BG}}
}

# Add Training Loss series (first = brand color)
series1 = LineSeries()
series1.name = "Training Loss"
series1.data = [[e, t] for e, t in zip(epochs, train_loss, strict=True)]
series1.color = BRAND
series1.marker = {"symbol": "circle"}
chart.add_series(series1)

# Add Validation Loss series
series2 = LineSeries()
series2.name = "Validation Loss"
series2.data = [[e, v] for e, v in zip(epochs, val_loss, strict=True)]
series2.color = SECONDARY
series2.marker = {"symbol": "square"}
chart.add_series(series2)

# Download Highcharts JS for inline embedding (required for file:// headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
try:
    req = urllib.request.Request(
        highcharts_url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        highcharts_js = response.read().decode("utf-8")
except Exception as e:
    raise RuntimeError(f"Failed to download Highcharts JS from {highcharts_url}: {e}") from e

# Generate HTML with INLINE scripts (critical for file:// headless Chrome)
html_str = chart.to_js_literal()
script_tag = f"<script>{highcharts_js}</script>"
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    {script_tag}
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML version with theme suffix
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(10)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
