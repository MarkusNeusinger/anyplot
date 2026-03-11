""" pyplots.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: highcharts unknown | Python 3.14.3
Quality: 83/100 | Created: 2026-03-11
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from scipy.signal import spectrogram
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Synthesize audio with speech-like frequency components
np.random.seed(42)
sample_rate = 22050
duration = 4.0
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Combine multiple frequency components to simulate a musical phrase
# Fundamental with vibrato
vibrato = 5 * np.sin(2 * np.pi * 5.5 * t)
signal = 0.6 * np.sin(2 * np.pi * (220 + vibrato) * t)

# Harmonics that fade in and out
signal += 0.4 * np.sin(2 * np.pi * 440 * t) * np.clip(np.sin(2 * np.pi * 0.8 * t), 0, 1)
signal += 0.25 * np.sin(2 * np.pi * 660 * t) * np.clip(np.sin(2 * np.pi * 0.5 * t), 0, 1)
signal += 0.15 * np.sin(2 * np.pi * 880 * t) * np.clip(np.cos(2 * np.pi * 0.3 * t), 0, 1)

# High-frequency transient bursts (percussive elements)
for onset in [0.5, 1.3, 2.1, 2.9, 3.5]:
    burst_env = np.exp(-30 * np.clip(t - onset, 0, None))
    signal += 0.3 * burst_env * np.sin(2 * np.pi * 3200 * t)

# Add gentle noise floor
signal += 0.02 * np.random.randn(n_samples)

# Compute spectrogram
n_fft = 2048
hop_length = 512
freqs, times, Sxx = spectrogram(signal, fs=sample_rate, nperseg=n_fft, noverlap=n_fft - hop_length)

# Convert to mel scale using mel filter bank
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

# Prepare heatmap data for Highcharts: [time_idx, mel_idx, dB_value]
# Downsample time axis for performance if needed
time_step = max(1, len(times) // 200)
mel_step = max(1, n_mels // 128)
time_indices = list(range(0, len(times), time_step))
mel_indices = list(range(0, n_mels, mel_step))

heatmap_data = []
for mi, mel_idx in enumerate(mel_indices):
    for ti, time_idx in enumerate(time_indices):
        heatmap_data.append([ti, mi, round(float(mel_spec_db[mel_idx, time_idx]), 1)])

# Create time and frequency labels
time_labels = [f"{times[i]:.2f}" for i in time_indices]
freq_labels = [f"{int(hz_points[i + 1])}" for i in mel_indices]

# Thin out axis tick labels for readability
time_tick_interval = max(1, len(time_labels) // 10)
freq_tick_interval = max(1, len(freq_labels) // 12)

# Chart configuration
chart_options = {
    "chart": {
        "type": "heatmap",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#1a1a2e",
        "marginTop": 160,
        "marginBottom": 200,
        "marginRight": 360,
        "marginLeft": 280,
        "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
    },
    "title": {
        "text": "spectrogram-mel \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "52px", "fontWeight": "600", "color": "#e0e0e0"},
        "y": 50,
    },
    "subtitle": {
        "text": "Mel-scaled power spectrum of synthesized audio (dB)",
        "style": {"fontSize": "30px", "fontWeight": "normal", "color": "#9e9e9e"},
        "y": 100,
    },
    "xAxis": {
        "categories": time_labels,
        "title": {
            "text": "Time (s)",
            "style": {"fontSize": "34px", "fontWeight": "600", "color": "#b0b0b0"},
            "margin": 20,
        },
        "labels": {"style": {"fontSize": "26px", "color": "#b0b0b0"}, "step": time_tick_interval, "y": 36},
        "lineWidth": 0,
        "tickLength": 0,
        "gridLineWidth": 0,
    },
    "yAxis": {
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
    },
    "colorAxis": {
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
    },
    "legend": {
        "title": {"text": "Power (dB)", "style": {"fontSize": "28px", "fontWeight": "600", "color": "#b0b0b0"}},
        "align": "right",
        "layout": "vertical",
        "verticalAlign": "middle",
        "symbolHeight": 900,
        "symbolWidth": 36,
        "itemStyle": {"fontSize": "24px", "color": "#b0b0b0"},
        "x": -40,
        "margin": 40,
    },
    "tooltip": {
        "style": {"fontSize": "28px"},
        "headerFormat": "",
        "pointFormat": (
            "Time: <b>{series.xAxis.categories.(point.x)} s</b><br>"
            "Freq: <b>{series.yAxis.categories.(point.y)} Hz</b><br>"
            "Power: <b>{point.value} dB</b>"
        ),
    },
    "credits": {"enabled": False},
    "plotOptions": {"heatmap": {"colsize": 1, "rowsize": 1, "borderWidth": 0, "nullColor": "#000004"}},
    "series": [
        {
            "type": "heatmap",
            "name": "Mel Spectrogram",
            "data": heatmap_data,
            "borderWidth": 0,
            "dataLabels": {"enabled": False},
        }
    ],
}

# Download Highcharts JS and heatmap module
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/heatmap.js"

headers = {"User-Agent": "Mozilla/5.0"}

req = urllib.request.Request(highcharts_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request(heatmap_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Convert options to JSON
options_json = json.dumps(chart_options)

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:#1a1a2e;">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>
        Highcharts.chart('container', {options_json});
    </script>
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
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
