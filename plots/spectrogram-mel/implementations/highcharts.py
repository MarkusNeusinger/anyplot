"""pyplots.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: highcharts unknown | Python 3.14.3
Quality: 88/100 | Created: 2026-03-11
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from scipy.signal import spectrogram
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Synthesize audio with distinct musical phrases
np.random.seed(42)
sample_rate = 22050
duration = 4.0
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Create an ascending melodic phrase with distinct temporal sections
# Section 1 (0-1s): Low fundamental with vibrato
# Section 2 (1-2s): Rising pitch with added harmonics
# Section 3 (2-3s): Peak intensity with rich harmonic content
# Section 4 (3-4s): Fade out with descending pitch

# Envelope shapes for each section
env1 = np.clip(1 - np.abs(t - 0.5) / 0.5, 0, 1) * (t < 1.0)
env2 = np.clip(1 - np.abs(t - 1.5) / 0.5, 0, 1) * ((t >= 1.0) & (t < 2.0))
env3 = np.clip(1 - np.abs(t - 2.5) / 0.5, 0, 1) * ((t >= 2.0) & (t < 3.0))
env4 = np.clip(1 - np.abs(t - 3.5) / 0.5, 0, 1) * (t >= 3.0)

# Ascending fundamental frequencies per section
vibrato = 5 * np.sin(2 * np.pi * 5.5 * t)
f0_1, f0_2, f0_3, f0_4 = 196, 262, 330, 262  # G3, C4, E4, C4

signal = np.zeros(n_samples)
signal += 0.6 * env1 * np.sin(2 * np.pi * (f0_1 + vibrato) * t)
signal += 0.6 * env2 * np.sin(2 * np.pi * (f0_2 + vibrato) * t)
signal += 0.6 * env3 * np.sin(2 * np.pi * (f0_3 + vibrato) * t)
signal += 0.5 * env4 * np.sin(2 * np.pi * (f0_4 + vibrato) * t)

# Harmonics that build up in intensity across sections
signal += 0.3 * env1 * np.sin(2 * np.pi * (f0_1 * 2) * t)
signal += 0.4 * env2 * np.sin(2 * np.pi * (f0_2 * 2) * t)
signal += 0.5 * env3 * np.sin(2 * np.pi * (f0_3 * 2) * t)
signal += 0.3 * env3 * np.sin(2 * np.pi * (f0_3 * 3) * t)
signal += 0.35 * env4 * np.sin(2 * np.pi * (f0_4 * 2) * t)

# Sharp percussive transient bursts with very fast decay
for onset in [0.5, 1.3, 2.1, 2.9, 3.5]:
    burst_env = np.exp(-120 * np.clip(t - onset, 0, None))
    burst_env *= (t >= onset).astype(float)
    signal += 0.25 * burst_env * np.sin(2 * np.pi * 3200 * t)

# Gentle noise floor
signal += 0.02 * np.random.randn(n_samples)

# Compute spectrogram
n_fft = 2048
hop_length = 512
freqs, times, Sxx = spectrogram(signal, fs=sample_rate, nperseg=n_fft, noverlap=n_fft - hop_length)

# Mel filter bank
n_mels = 128
mel_low = 0
mel_high = 2595 * np.log10(1 + (sample_rate / 2) / 700)
mel_points = np.linspace(mel_low, mel_high, n_mels + 2)
hz_points = 700 * (10 ** (mel_points / 2595) - 1)
bin_indices = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

mel_filterbank = np.zeros((n_mels, len(freqs)))
for i in range(n_mels):
    left = bin_indices[i]
    center = bin_indices[i + 1]
    right = bin_indices[i + 2]
    for j in range(left, min(center, len(freqs))):
        mel_filterbank[i, j] = (j - left) / max(center - left, 1)
    for j in range(center, min(right, len(freqs))):
        mel_filterbank[i, j] = (right - j) / max(right - center, 1)

# Apply mel filterbank and convert to dB
mel_spec = mel_filterbank @ Sxx
mel_spec = np.maximum(mel_spec, 1e-10)
mel_spec_db = 10 * np.log10(mel_spec)
ref_db = mel_spec_db.max()
mel_spec_db = mel_spec_db - ref_db
mel_spec_db = np.clip(mel_spec_db, -80, 0)

# Trim upper mel bins that are mostly empty (above ~5000 Hz)
# Find the mel bin closest to 5000 Hz
max_display_hz = 5000
max_mel_bin = n_mels
for i in range(n_mels):
    if hz_points[i + 1] > max_display_hz:
        max_mel_bin = i
        break
# Keep a few bins above to show transient tails
max_mel_bin = min(max_mel_bin + 8, n_mels)

# Prepare heatmap data for Highcharts: [time_idx, mel_idx, dB_value]
time_step = max(1, len(times) // 300)
mel_step = 1
time_indices = list(range(0, len(times), time_step))
mel_indices = list(range(0, max_mel_bin, mel_step))

heatmap_data = []
for mi, mel_idx in enumerate(mel_indices):
    for ti, time_idx in enumerate(time_indices):
        heatmap_data.append([ti, mi, round(float(mel_spec_db[mel_idx, time_idx]), 1)])

# Create axis labels
time_labels = [f"{times[i]:.2f}" for i in time_indices]
freq_labels = [f"{int(hz_points[i + 1])}" for i in mel_indices]

time_tick_interval = max(1, len(time_labels) // 10)
freq_tick_interval = max(1, len(freq_labels) // 14)

# Build chart using highcharts-core API
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#1a1a2e",
    "marginTop": 160,
    "marginBottom": 200,
    "marginRight": 280,
    "marginLeft": 280,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "spectrogram-mel \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "52px", "fontWeight": "600", "color": "#e0e0e0"},
    "y": 50,
}

chart.options.subtitle = {
    "text": (
        "Mel-scaled power spectrum \u2014 ascending melodic phrase "
        "G3\u2192C4\u2192E4\u2192C4 with percussive transients"
    ),
    "style": {"fontSize": "30px", "fontWeight": "normal", "color": "#9e9e9e"},
    "y": 100,
}

# Section boundary positions (in category indices)
section_boundaries = [len(time_labels) * 0.25 - 0.5, len(time_labels) * 0.5 - 0.5, len(time_labels) * 0.75 - 0.5]

# Section label positions (centered in each section)
section_labels = [
    {"text": "G3 phrase", "x": len(time_labels) * 0.125},
    {"text": "C4 transition", "x": len(time_labels) * 0.375},
    {"text": "E4 peak", "x": len(time_labels) * 0.625},
    {"text": "C4 fadeout", "x": len(time_labels) * 0.875},
]

chart.options.x_axis = {
    "categories": time_labels,
    "title": {"text": "Time (s)", "style": {"fontSize": "34px", "fontWeight": "600", "color": "#b0b0b0"}, "margin": 20},
    "labels": {"style": {"fontSize": "26px", "color": "#b0b0b0"}, "step": time_tick_interval, "y": 36},
    "lineWidth": 0,
    "tickLength": 0,
    "gridLineWidth": 0,
}

chart.options.y_axis = {
    "categories": freq_labels,
    "title": {
        "text": "Frequency (Hz, mel-scaled)",
        "style": {"fontSize": "34px", "fontWeight": "600", "color": "#b0b0b0"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "26px", "color": "#b0b0b0"}, "step": freq_tick_interval},
    "reversed": False,
    "lineWidth": 0,
    "gridLineWidth": 0,
}

chart.options.color_axis = {
    "min": -80,
    "max": 0,
    "stops": [
        [0.0, "#000004"],
        [0.15, "#1b0c41"],
        [0.30, "#4a0c6b"],
        [0.45, "#781c6d"],
        [0.55, "#a52c60"],
        [0.65, "#cf4446"],
        [0.75, "#ed6925"],
        [0.85, "#fb9b06"],
        [0.95, "#f7d13d"],
        [1.0, "#fcffa4"],
    ],
    "labels": {"style": {"fontSize": "26px", "color": "#b0b0b0"}, "format": "{value} dB"},
}

chart.options.legend = {
    "title": {"text": "Power (dB)", "style": {"fontSize": "28px", "fontWeight": "600", "color": "#b0b0b0"}},
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 1000,
    "symbolWidth": 36,
    "itemStyle": {"fontSize": "24px", "color": "#b0b0b0"},
    "x": -20,
    "margin": 20,
}

chart.options.tooltip = {
    "style": {"fontSize": "28px"},
    "headerFormat": "",
    "pointFormat": (
        "Time: <b>{series.xAxis.categories.(point.x)} s</b><br>"
        "Freq: <b>{series.yAxis.categories.(point.y)} Hz</b><br>"
        "Power: <b>{point.value} dB</b>"
    ),
}

chart.options.credits = {"enabled": False}

chart.options.plot_options = {"heatmap": {"colsize": 1, "rowsize": 1, "borderWidth": 0, "nullColor": "#000004"}}

# Add heatmap series using highcharts-core API
series = HeatmapSeries()
series.name = "Mel Spectrogram"
series.data = heatmap_data
series.border_width = 0
series.data_labels = {"enabled": False}
chart.add_series(series)

# Download Highcharts JS and heatmap module
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/heatmap.js"
annotations_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/annotations.js"

headers = {"User-Agent": "Mozilla/5.0"}

req = urllib.request.Request(highcharts_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request(heatmap_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

req = urllib.request.Request(annotations_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

# Build renderer overlay script for section labels and dividers
# Uses Highcharts renderer API to draw on top of the heatmap
overlay_labels = []
for lbl in section_labels:
    overlay_labels.append(f'{{text:"{lbl["text"]}",x:{lbl["x"]:.1f}}}')
overlay_bounds = ",".join(f"{b:.1f}" for b in section_boundaries)

renderer_script = f"""
setTimeout(function() {{
  var chart = Highcharts.charts[0];
  if (!chart) return;
  var xAxis = chart.xAxis[0];
  var labels = [{",".join(overlay_labels)}];
  var bounds = [{overlay_bounds}];
  var plotTop = chart.plotTop;
  var plotHeight = chart.plotHeight;

  // Draw dashed vertical divider lines
  bounds.forEach(function(val) {{
    var px = xAxis.toPixels(val);
    chart.renderer.path(['M', px, plotTop, 'L', px, plotTop + plotHeight])
      .attr({{stroke: 'rgba(255,255,255,0.35)', 'stroke-width': 3, dashstyle: 'Dash', zIndex: 10}})
      .add();
  }});

  // Draw section labels at top of plot area
  labels.forEach(function(lbl) {{
    var px = xAxis.toPixels(lbl.x);
    chart.renderer.text(lbl.text, px, plotTop + 45)
      .css({{color: '#ddd', fontSize: '34px', fontWeight: '600'}})
      .attr({{align: 'center', zIndex: 11}})
      .add();
  }});
}}, 500);
"""

# Generate HTML with inline scripts
js_literal = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:#1a1a2e;">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>{js_literal}</script>
    <script>{renderer_script}</script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot using headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2840")
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--hide-scrollbars")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4800, 2840)
driver.get(f"file://{temp_path}")
time.sleep(7)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
