""" pyplots.ai
spectrum-basic: Frequency Spectrum Plot
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
from highcharts_core.options.series.area import AreaSplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Generate a synthetic audio signal with multiple frequency components
np.random.seed(42)
sample_rate = 8192  # Hz
duration = 1.0  # seconds
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Create composite signal: 440 Hz (A4 note), 880 Hz (A5 harmonic), 1320 Hz (E6), plus noise
signal = (
    1.0 * np.sin(2 * np.pi * 440 * t)
    + 0.5 * np.sin(2 * np.pi * 880 * t)
    + 0.3 * np.sin(2 * np.pi * 1320 * t)
    + 0.1 * np.random.randn(n_samples)
)

# Compute FFT
fft_result = np.fft.rfft(signal)
frequencies = np.fft.rfftfreq(n_samples, 1 / sample_rate)
amplitude = np.abs(fft_result) / n_samples

# Convert to dB scale (with floor to avoid log(0))
amplitude_db = 20 * np.log10(np.maximum(amplitude, 1e-10))

# Normalize to reasonable range and take subset for display (0-2000 Hz)
freq_mask = frequencies <= 2000
frequencies = frequencies[freq_mask]
amplitude_db = amplitude_db[freq_mask]

# Downsample for smoother rendering (every 4th point)
step = 4
frequencies = frequencies[::step]
amplitude_db = amplitude_db[::step]

# Prepare data for Highcharts (list of [x, y] pairs)
data_points = [[float(f), float(a)] for f, a in zip(frequencies, amplitude_db, strict=True)]

# Create Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "areaspline",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 220,
    "marginRight": 120,
    "marginTop": 160,
}

# Title
chart.options.title = {
    "text": "spectrum-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {
    "text": "Audio Signal Analysis: 440 Hz Fundamental + Harmonics",
    "style": {"fontSize": "32px"},
}

# X-axis (Frequency)
chart.options.x_axis = {
    "title": {"text": "Frequency (Hz)", "style": {"fontSize": "36px"}, "margin": 20},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "max": 2000,
    "tickInterval": 200,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "lineWidth": 2,
}

# Y-axis (Amplitude in dB)
chart.options.y_axis = {
    "title": {"text": "Amplitude (dB)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "lineWidth": 2,
}

# Plot options
chart.options.plot_options = {
    "areaspline": {"fillOpacity": 0.3, "lineWidth": 4, "marker": {"enabled": False}, "threshold": None}
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -40,
    "y": 80,
}

# Credits
chart.options.credits = {"enabled": False}

# Series - Frequency spectrum
series = AreaSplineSeries()
series.data = data_points
series.name = "Power Spectrum"
series.color = "#306998"
series.fill_color = {
    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
    "stops": [[0, "rgba(48, 105, 152, 0.4)"], [1, "rgba(48, 105, 152, 0.05)"]],
}

chart.add_series(series)

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

# Write temp HTML and take screenshot
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

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
