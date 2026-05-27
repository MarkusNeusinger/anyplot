""" anyplot.ai
spectrum-basic: Frequency Spectrum Plot
Library: highcharts unknown | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-14
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSplineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"
ACCENT = "#C475FD"

# Data - Generate a synthetic audio signal with multiple frequency components
np.random.seed(42)
sample_rate = 8192
duration = 1.0
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Create composite signal: 440 Hz (A4), 880 Hz (A5), 1320 Hz (E6), plus noise
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

# Convert to dB scale
amplitude_db = 20 * np.log10(np.maximum(amplitude, 1e-10))

# Take subset for display (0-2000 Hz)
freq_mask = frequencies <= 2000
frequencies = frequencies[freq_mask]
amplitude_db = amplitude_db[freq_mask]

# Downsample for smoother rendering
step = 4
frequencies = frequencies[::step]
amplitude_db = amplitude_db[::step]

# Find dominant peaks programmatically
peak_freqs = [440, 880, 1320]
peak_indices = []
peak_amplitudes = []

for target_freq in peak_freqs:
    idx = np.argmin(np.abs(frequencies - target_freq))
    peak_indices.append(idx)
    peak_amplitudes.append(amplitude_db[idx])

# Prepare data for Highcharts
data_points = [[float(f), float(a)] for f, a in zip(frequencies, amplitude_db, strict=True)]

# Create Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "areaspline",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 250,
    "marginLeft": 220,
    "marginRight": 120,
    "marginTop": 160,
}

# Title
chart.options.title = {
    "text": "spectrum-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
}

# X-axis (Frequency)
chart.options.x_axis = {
    "title": {"text": "Frequency (Hz)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0,
    "max": 2000,
    "tickInterval": 400,
    "gridLineWidth": 2,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickColor": INK_SOFT,
    "tickWidth": 2,
}

# Y-axis (Amplitude in dB)
chart.options.y_axis = {
    "title": {"text": "Amplitude (dB)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "tickInterval": 20,
    "gridLineWidth": 2,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickColor": INK_SOFT,
    "tickWidth": 2,
}

# Plot options with enhanced styling
chart.options.plot_options = {
    "areaspline": {
        "fillOpacity": 0.35,
        "lineWidth": 4,
        "marker": {"enabled": False},
        "threshold": None,
        "shadow": False,
    },
    "scatter": {"marker": {"radius": 16, "lineWidth": 3, "lineColor": INK, "fillColor": ACCENT}},
}

# Legend
chart.options.legend = {"enabled": False}

# Credits
chart.options.credits = {"enabled": False}

# Tooltip configuration for better interactivity
chart.options.tooltip = {
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 2,
    "style": {"color": INK, "fontSize": "18px"},
    "shared": False,
    "crosshairs": True,
}

# Series 1 - Frequency spectrum (main area chart)
series = AreaSplineSeries()
series.data = data_points
series.name = "Power Spectrum"
series.color = BRAND
series.fill_color = {
    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
    "stops": [[0, "rgba(0, 158, 115, 0.5)"], [1, "rgba(0, 158, 115, 0.08)"]],
}
series.z_index = 2

chart.add_series(series)

# Series 2 - Peak points for visual emphasis (visual hierarchy)
peak_series = ScatterSeries()
peak_data = [[float(frequencies[idx]), float(peak_amplitudes[i])] for i, idx in enumerate(peak_indices)]
peak_series.data = peak_data
peak_series.name = "Dominant Peaks"
peak_series.color = ACCENT
peak_series.marker = {"radius": 16, "lineWidth": 3, "lineColor": INK, "fillColor": ACCENT}
peak_series.z_index = 3

chart.add_series(peak_series)

# Download Highcharts JS for inline embedding
urls = ["https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js", "https://code.highcharts.com/highcharts.js"]
highcharts_js = None
for url in urls:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            highcharts_js = response.read().decode("utf-8")
            break
    except Exception:
        continue

if not highcharts_js:
    highcharts_js = "/* Highcharts JS not available */"

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

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG
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
