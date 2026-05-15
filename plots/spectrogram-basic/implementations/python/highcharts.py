""" anyplot.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: highcharts unknown | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-15
"""

import os
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from scipy import signal
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data
np.random.seed(42)
sample_rate = 1000  # 1000 Hz sampling rate
duration = 2.0  # 2 seconds
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Chirp signal: frequency sweeps from 10 Hz to 200 Hz
f0, f1 = 10, 200
chirp_signal = signal.chirp(t, f0=f0, f1=f1, t1=duration, method="linear")

# Add noise for realism
noise = 0.1 * np.random.randn(len(t))
combined_signal = chirp_signal + noise

# Compute spectrogram using scipy
nperseg = 128
noverlap = 100
frequencies, times, Sxx = signal.spectrogram(combined_signal, fs=sample_rate, nperseg=nperseg, noverlap=noverlap)

# Convert to dB scale for better visualization
Sxx_db = 10 * np.log10(Sxx + 1e-10)

# Get dB range for colorbar
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
    "backgroundColor": PAGE_BG,
    "marginTop": 160,
    "marginBottom": 250,
    "marginLeft": 200,
    "marginRight": 320,
}

# Title
chart.options.title = {
    "text": "spectrogram-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# Subtitle
chart.options.subtitle = {
    "text": "Linear chirp signal (10-200 Hz) with linear frequency axis",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis (time)
time_labels = [f"{t:.2f}" for t in times_ds]
chart.options.x_axis = {
    "categories": time_labels,
    "title": {"text": "Time (seconds)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "step": max(1, len(time_labels) // 10)},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis (frequency)
freq_labels = [f"{f:.0f}" for f in frequencies_ds]
chart.options.y_axis = {
    "categories": freq_labels,
    "title": {"text": "Frequency (Hz)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "step": max(1, len(freq_labels) // 10)},
    "reversed": False,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
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
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "{value:.0f} dB"},
}

# Legend
chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 800,
    "symbolWidth": 40,
    "x": -20,
    "title": {"text": "Power (dB)", "style": {"fontSize": "22px", "color": INK}},
    "itemStyle": {"color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Tooltip
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>Time:</b> {point.x_label} s<br><b>Frequency:</b> {point.y_label} Hz<br><b>Power:</b> {point.value:.1f} dB",
    "style": {"fontSize": "16px"},
}

# Series
series = HeatmapSeries()
series.data = heatmap_data
series.name = "Spectrogram"
series.border_width = 0

chart.add_series(series)

# Generate chart JavaScript
html_str = chart.to_js_literal()

# HTML with unpkg CDN (Cloudflare-friendly alternative)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://unpkg.com/highcharts@11.4.7/highcharts.js"></script>
    <script src="https://unpkg.com/highcharts@11.4.7/modules/heatmap.js"></script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)


# Start simple HTTP server in background thread to serve HTML
class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


html_dir = Path.cwd()
server = HTTPServer(("127.0.0.1", 0), QuietHTTPRequestHandler)
port = server.server_port
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()

# Take screenshot with Selenium via HTTP
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    driver.get(f"http://127.0.0.1:{port}/plot-{THEME}.html")

    # Wait for container to be visible and chart to render
    time.sleep(20)

    # Additional wait to ensure rendering is complete
    try:
        driver.execute_script("return document.readyState === 'complete' && window.Highcharts !== undefined")
    except Exception:
        pass

    time.sleep(2)
    driver.save_screenshot(f"plot-{THEME}.png")
    driver.quit()
finally:
    server.shutdown()
