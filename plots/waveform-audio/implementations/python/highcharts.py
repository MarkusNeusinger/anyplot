""" anyplot.ai
waveform-audio: Audio Waveform Plot
Library: highcharts unknown | Python 3.13.13
Quality: 84/100 | Created: 2026-06-03
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette, see prompts/default-style-guide.md
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # Imprint palette position 1 — ALWAYS first series

# Data — synthetic speech waveform (two voiced syllables, 2 s at 44 100 Hz)
np.random.seed(42)
SAMPLE_RATE = 44100
DURATION = 2.0
n_samples = int(SAMPLE_RATE * DURATION)
t_full = np.linspace(0, DURATION, n_samples)

# Voiced source: fundamental (130 Hz) + harmonics → vowel-like timbre
f0 = 130
raw = (
    0.50 * np.sin(2 * np.pi * 1 * f0 * t_full)
    + 0.25 * np.sin(2 * np.pi * 2 * f0 * t_full)
    + 0.15 * np.sin(2 * np.pi * 3 * f0 * t_full)
    + 0.07 * np.sin(2 * np.pi * 4 * f0 * t_full)
    + 0.03 * np.sin(2 * np.pi * 5 * f0 * t_full)
)

# Amplitude envelope: two syllables separated by a brief pause
envelope = np.zeros(n_samples)
mask1 = (t_full >= 0.15) & (t_full <= 0.65)
envelope[mask1] = np.hanning(mask1.sum())
mask2 = (t_full >= 0.85) & (t_full <= 1.55)
envelope[mask2] = np.hanning(mask2.sum()) * 0.80

raw = raw * envelope + 0.005 * np.random.randn(n_samples)
raw = np.clip(raw, -1.0, 1.0)

# Downsample to 3 000 display points
n_display = 3000
step = n_samples // n_display
t_disp = t_full[::step][:n_display]
amp_disp = raw[::step][:n_display]

data_points = [[round(float(tv), 6), round(float(av), 5)] for tv, av in zip(t_disp, amp_disp, strict=True)]

# Title — font size scaled to prevent overflow at 3200 px width
title = "Speech Waveform · waveform-audio · python · highcharts · anyplot.ai"
title_px = max(44, round(66 * 67 / len(title)))

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "area",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
    "marginBottom": 130,
    "marginLeft": 155,
    "marginRight": 60,
    "marginTop": 90,
}

chart.options.title = {"text": title, "style": {"fontSize": f"{title_px}px", "color": INK, "fontWeight": "600"}}

chart.options.x_axis = {
    "title": {"text": "Time (seconds)", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "tickInterval": 0.25,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
}

chart.options.y_axis = {
    "title": {"text": "Amplitude", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": -1.2,
    "max": 1.2,
    "tickInterval": 0.5,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "plotLines": [{"value": 0, "color": INK_SOFT, "width": 2, "zIndex": 5}],
}

chart.options.colors = [BRAND]

chart.options.plot_options = {
    "area": {
        "marker": {"enabled": False},
        "fillOpacity": 0.35,
        "threshold": 0,
        "lineWidth": 1.5,
        "states": {"hover": {"lineWidth": 1.5}},
    }
}

chart.options.legend = {"enabled": False}

chart.options.tooltip = {
    "backgroundColor": ELEVATED_BG,
    "style": {"color": INK, "fontSize": "36px"},
    "borderColor": INK_SOFT,
    "valueDecimals": 4,
}

# Series
waveform = AreaSeries()
waveform.name = "Amplitude"
waveform.data = data_points
chart.add_series(waveform)

# Download Highcharts JS — CDN unavailable from file:// in headless Chrome
req = urllib.request.Request(
    "https://code.highcharts.com/highcharts.js",
    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"},
)
with urllib.request.urlopen(req, timeout=30) as resp:
    highcharts_js = resp.read().decode("utf-8")

js_literal = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:3200px; height:1800px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome with authoritative CDP viewport override
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

# Pin to exact 3200×1800 — belt-and-braces against ±1-2 px rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
