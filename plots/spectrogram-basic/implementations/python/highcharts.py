""" pyplots.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from scipy import signal
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Generate chirp signal (frequency increases over time)
np.random.seed(42)
sample_rate = 1000  # 1000 Hz sampling rate
duration = 2.0  # 2 seconds
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Chirp signal: frequency sweeps from 10 Hz to 200 Hz
f0, f1 = 10, 200
chirp_signal = signal.chirp(t, f0=f0, f1=f1, t1=duration, method="linear")

# Add some noise for realism
noise = 0.1 * np.random.randn(len(t))
combined_signal = chirp_signal + noise

# Compute spectrogram using scipy
nperseg = 128
noverlap = 100
frequencies, times, Sxx = signal.spectrogram(combined_signal, fs=sample_rate, nperseg=nperseg, noverlap=noverlap)

# Convert to dB scale for better visualization
Sxx_db = 10 * np.log10(Sxx + 1e-10)

# Get dB range for colorbar (use actual dB values, not normalized)
Sxx_min = float(Sxx_db.min())
Sxx_max = float(Sxx_db.max())

# Downsample for Highcharts heatmap performance
max_time_bins = 80
max_freq_bins = 50

time_step = max(1, len(times) // max_time_bins)
freq_step = max(1, len(frequencies) // max_freq_bins)

times_ds = times[::time_step]
frequencies_ds = frequencies[::freq_step]
Sxx_ds = Sxx_db[::freq_step, ::time_step]

# Create heatmap data points as [x, y, value]
heatmap_data = []
for i, _freq in enumerate(frequencies_ds):
    for j, _t_val in enumerate(times_ds):
        heatmap_data.append([j, i, round(float(Sxx_ds[i, j]), 1)])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "heatmap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginTop": 160,  # Increased for subtitle
    "marginBottom": 250,
    "marginLeft": 200,
    "marginRight": 320,  # Increased for legend title spacing
}

# Title and subtitle
chart.options.title = {
    "text": "spectrogram-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": "Linear chirp signal (10-200 Hz) with linear frequency axis",
    "style": {"fontSize": "32px", "color": "#666666"},
}

# X-axis (time)
time_labels = [f"{t:.2f}" for t in times_ds]
chart.options.x_axis = {
    "categories": time_labels,
    "title": {"text": "Time (seconds)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "24px"}, "step": max(1, len(time_labels) // 10)},
    "tickLength": 10,
}

# Y-axis (frequency)
freq_labels = [f"{f:.0f}" for f in frequencies_ds]
chart.options.y_axis = {
    "categories": freq_labels,
    "title": {"text": "Frequency (Hz)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "24px"}, "step": max(1, len(freq_labels) // 10)},
    "reversed": False,
}

# Color axis (legend for heatmap intensity) - use actual dB values
chart.options.color_axis = {
    "min": Sxx_min,
    "max": Sxx_max,
    "stops": [
        [0, "#440154"],  # viridis dark purple
        [0.25, "#3b528b"],  # blue
        [0.5, "#21918c"],  # teal
        [0.75, "#5ec962"],  # green
        [1, "#fde725"],  # yellow
    ],
    "labels": {"style": {"fontSize": "24px"}, "format": "{value:.0f} dB"},
}

# Legend
chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 800,
    "symbolWidth": 40,
    "x": -20,  # Shift legend left to avoid edge cramping
    "title": {"text": "Power (dB)", "style": {"fontSize": "28px"}},
}

# Tooltip - show actual dB values
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>Time:</b> {point.x_label} s<br><b>Frequency:</b> {point.y_label} Hz<br><b>Power:</b> {point.value:.1f} dB",
    "style": {"fontSize": "20px"},
}

# Series
series = HeatmapSeries()
series.data = heatmap_data
series.name = "Spectrogram"
series.border_width = 0

chart.add_series(series)

# Download Highcharts JS and heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

heatmap_url = "https://code.highcharts.com/modules/heatmap.js"
with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>spectrogram-basic · highcharts · pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/heatmap.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
