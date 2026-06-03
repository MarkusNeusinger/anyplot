"""anyplot.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Updated: 2026-06-03
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from PIL import Image
from scipy.signal import spectrogram
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data — synthesized audio with distinct musical phrases
np.random.seed(42)
sample_rate = 22050
duration = 4.0
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Envelope shapes for each 1-second section
env1 = np.clip(1 - np.abs(t - 0.5) / 0.5, 0, 1) * (t < 1.0)
env2 = np.clip(1 - np.abs(t - 1.5) / 0.5, 0, 1) * ((t >= 1.0) & (t < 2.0))
env3 = np.clip(1 - np.abs(t - 2.5) / 0.5, 0, 1) * ((t >= 2.0) & (t < 3.0))
env4 = np.clip(1 - np.abs(t - 3.5) / 0.5, 0, 1) * (t >= 3.0)

vibrato = 5 * np.sin(2 * np.pi * 5.5 * t)
f0_1, f0_2, f0_3, f0_4 = 196, 262, 330, 262  # G3, C4, E4, C4

signal = np.zeros(n_samples)
signal += 0.6 * env1 * np.sin(2 * np.pi * (f0_1 + vibrato) * t)
signal += 0.6 * env2 * np.sin(2 * np.pi * (f0_2 + vibrato) * t)
signal += 0.6 * env3 * np.sin(2 * np.pi * (f0_3 + vibrato) * t)
signal += 0.5 * env4 * np.sin(2 * np.pi * (f0_4 + vibrato) * t)

signal += 0.3 * env1 * np.sin(2 * np.pi * (f0_1 * 2) * t)
signal += 0.4 * env2 * np.sin(2 * np.pi * (f0_2 * 2) * t)
signal += 0.5 * env3 * np.sin(2 * np.pi * (f0_3 * 2) * t)
signal += 0.3 * env3 * np.sin(2 * np.pi * (f0_3 * 3) * t)
signal += 0.35 * env4 * np.sin(2 * np.pi * (f0_4 * 2) * t)

for onset in [0.5, 1.3, 2.1, 2.9, 3.5]:
    burst_env = np.exp(-120 * np.clip(t - onset, 0, None))
    burst_env *= (t >= onset).astype(float)
    signal += 0.25 * burst_env * np.sin(2 * np.pi * 3200 * t)

signal += 0.02 * np.random.randn(n_samples)

# Spectrogram
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

mel_spec = mel_filterbank @ Sxx
mel_spec = np.maximum(mel_spec, 1e-10)
mel_spec_db = 10 * np.log10(mel_spec)
ref_db = mel_spec_db.max()
mel_spec_db = mel_spec_db - ref_db
mel_spec_db = np.clip(mel_spec_db, -60, 0)

# Trim mel bins above ~5000 Hz
max_display_hz = 5000
max_mel_bin = n_mels
for i in range(n_mels):
    if hz_points[i + 1] > max_display_hz:
        max_mel_bin = i
        break
max_mel_bin = min(max_mel_bin + 8, n_mels)

# Prepare heatmap data: [time_idx, mel_idx, dB_value]
time_step = max(1, len(times) // 300)
time_indices = list(range(0, len(times), time_step))
mel_indices = list(range(0, max_mel_bin))

heatmap_data = []
for mi, mel_idx in enumerate(mel_indices):
    for ti, time_idx in enumerate(time_indices):
        heatmap_data.append([ti, mi, round(float(mel_spec_db[mel_idx, time_idx]), 1)])

time_labels = [f"{times[i]:.2f}" for i in time_indices]
freq_labels = [f"{int(hz_points[i + 1])}" for i in mel_indices]

time_tick_interval = max(1, len(time_labels) // 10)
freq_tick_interval = max(1, len(freq_labels) // 14)

# Section boundaries and labels for the musical phrase narrative
section_boundaries = [len(time_labels) * 0.25 - 0.5, len(time_labels) * 0.5 - 0.5, len(time_labels) * 0.75 - 0.5]
section_labels_data = [
    {"text": "G3 phrase", "x": len(time_labels) * 0.125},
    {"text": "C4 transition", "x": len(time_labels) * 0.375},
    {"text": "E4 peak", "x": len(time_labels) * 0.625},
    {"text": "C4 fadeout", "x": len(time_labels) * 0.875},
]

# Plot
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginTop": 175,
    "marginBottom": 150,
    "marginRight": 255,
    "marginLeft": 215,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

title_text = "spectrogram-mel · python · highcharts · anyplot.ai"
n_chars = len(title_text)
ratio = 67 / n_chars if n_chars > 67 else 1.0
title_fontsize = max(44, round(66 * ratio))

chart.options.title = {
    "text": title_text,
    "style": {"fontSize": f"{title_fontsize}px", "fontWeight": "600", "color": INK},
    "y": 48,
}

chart.options.subtitle = {
    "text": ("Mel-scaled power spectrum — ascending melodic phrase G3→C4→E4→C4 with percussive transients"),
    "style": {"fontSize": "38px", "fontWeight": "normal", "color": INK_SOFT},
    "y": 108,
}

chart.options.x_axis = {
    "categories": time_labels,
    "title": {"text": "Time (s)", "style": {"fontSize": "56px", "fontWeight": "600", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "step": time_tick_interval, "y": 36},
    "lineWidth": 0,
    "tickLength": 0,
    "gridLineWidth": 0,
}

chart.options.y_axis = {
    "categories": freq_labels,
    "title": {
        "text": "Frequency (Hz, mel-scaled)",
        "style": {"fontSize": "56px", "fontWeight": "600", "color": INK},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "step": freq_tick_interval},
    "reversed": False,
    "lineWidth": 0,
    "gridLineWidth": 0,
}

# Imprint sequential colormap: green (#009E73) → blue (#4467A3) for single-polarity power data
chart.options.color_axis = {
    "min": -60,
    "max": 0,
    "minColor": "#009E73",
    "maxColor": "#4467A3",
    "stops": [[0, "#009E73"], [1, "#4467A3"]],
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "{value} dB"},
}

chart.options.legend = {
    "title": {"text": "Power (dB)", "style": {"fontSize": "44px", "fontWeight": "600", "color": INK_SOFT}},
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 800,
    "symbolWidth": 34,
    "itemStyle": {"fontSize": "44px", "color": INK_SOFT},
    "x": -20,
    "margin": 20,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

chart.options.tooltip = {
    "style": {"fontSize": "36px"},
    "headerFormat": "",
    "pointFormat": "Power: <b>{point.value} dB</b>",
}

chart.options.credits = {"enabled": False}

chart.options.plot_options = {"heatmap": {"colsize": 1, "rowsize": 1, "borderWidth": 0, "nullColor": PAGE_BG}}

series = HeatmapSeries()
series.name = "Mel Spectrogram"
series.data = heatmap_data
series.border_width = 0
series.data_labels = {"enabled": False}
chart.add_series(series)

# Download Highcharts JS modules inline (CDN blocked in headless Chrome file:// context)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/heatmap.js"

req_headers = {"User-Agent": "Mozilla/5.0"}

req = urllib.request.Request(highcharts_url, headers=req_headers)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request(heatmap_url, headers=req_headers)
with urllib.request.urlopen(req, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Renderer overlay: section labels and dashed vertical dividers
divider_color = "rgba(26,26,23,0.35)" if THEME == "light" else "rgba(240,239,232,0.35)"
label_color = INK_SOFT

overlay_labels_js = ",".join(f'{{text:"{lbl["text"]}",x:{lbl["x"]:.1f}}}' for lbl in section_labels_data)
overlay_bounds_js = ",".join(f"{b:.1f}" for b in section_boundaries)

renderer_script = f"""
setTimeout(function() {{
  var chart = Highcharts.charts[0];
  if (!chart) return;
  var xAxis = chart.xAxis[0];
  var labels = [{overlay_labels_js}];
  var bounds = [{overlay_bounds_js}];
  var plotTop = chart.plotTop;
  var plotHeight = chart.plotHeight;

  bounds.forEach(function(val) {{
    var px = xAxis.toPixels(val);
    chart.renderer.path(['M', px, plotTop, 'L', px, plotTop + plotHeight])
      .attr({{stroke: '{divider_color}', 'stroke-width': 3, dashstyle: 'Dash', zIndex: 10}})
      .add();
  }});

  labels.forEach(function(lbl) {{
    var px = xAxis.toPixels(lbl.x);
    chart.renderer.text(lbl.text, px, plotTop - 20)
      .css({{color: '{label_color}', fontSize: '38px', fontWeight: '600'}})
      .attr({{align: 'center', zIndex: 11}})
      .add();
  }});
}}, 500);
"""

# Save
js_literal = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:{PAGE_BG};">
    <div id="container" style="width:3200px; height:1800px;"></div>
    <script>{js_literal}</script>
    <script>{renderer_script}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 3200×1800 — guards against ±1–2 px rounding in headless Chrome
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
