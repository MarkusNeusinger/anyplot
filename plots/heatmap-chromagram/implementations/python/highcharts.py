""" pyplots.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: highcharts unknown | Python 3.14.3
Quality: 92/100 | Created: 2026-03-17
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Chromagram: energy of 12 pitch classes over 80 time frames
np.random.seed(42)

pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_frames = 80
frame_duration = 0.1  # seconds per frame
time_seconds = np.arange(n_frames) * frame_duration

# Simulate realistic harmonic patterns: C major → G major → A minor → F major progression
chord_profiles = {
    "C_major": {"C": 0.9, "E": 0.7, "G": 0.6, "D": 0.1, "F": 0.1},
    "G_major": {"G": 0.9, "B": 0.7, "D": 0.65, "F#": 0.15, "A": 0.1},
    "A_minor": {"A": 0.85, "C": 0.7, "E": 0.65, "G": 0.1, "B": 0.05},
    "F_major": {"F": 0.9, "A": 0.7, "C": 0.65, "E": 0.1, "G": 0.05},
}

chroma = np.random.uniform(0.02, 0.08, size=(12, n_frames))

chord_sequence = ["C_major"] * 20 + ["G_major"] * 20 + ["A_minor"] * 20 + ["F_major"] * 20
for frame_idx, chord_name in enumerate(chord_sequence):
    profile = chord_profiles[chord_name]
    for pitch, energy in profile.items():
        pitch_idx = pitch_classes.index(pitch)
        chroma[pitch_idx, frame_idx] += energy + np.random.normal(0, 0.06)

chroma = np.clip(chroma, 0, 1.0)

# Build heatmap data: [x_index, y_index, value]
heatmap_data = []
for y_idx in range(12):
    for x_idx in range(n_frames):
        heatmap_data.append([x_idx, y_idx, round(float(chroma[y_idx, x_idx]), 3)])

# Time labels (show every 10th frame for clarity)
time_labels = [f"{t:.1f}s" if i % 10 == 0 else "" for i, t in enumerate(time_seconds)]

# Build chart using highcharts_core Python API
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#1a1a2e",
    "marginTop": 160,
    "marginBottom": 220,
    "marginRight": 340,
    "marginLeft": 200,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "heatmap-chromagram \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "600", "color": "#e0e0e0"},
    "y": 30,
}

chart.options.subtitle = {
    "text": "Pitch class energy over time \u2014 C\u2192G\u2192Am\u2192F chord progression",
    "style": {"fontSize": "28px", "fontWeight": "normal", "color": "#9e9eb8"},
    "y": 80,
}

# Chord boundary plot lines and plot bands for data storytelling
chord_boundaries = [
    {"value": 19.5, "color": "rgba(255,255,255,0.35)", "width": 3, "dashStyle": "Dash"},
    {"value": 39.5, "color": "rgba(255,255,255,0.35)", "width": 3, "dashStyle": "Dash"},
    {"value": 59.5, "color": "rgba(255,255,255,0.35)", "width": 3, "dashStyle": "Dash"},
]

chord_labels = [
    {
        "from": 0,
        "to": 19.5,
        "color": "transparent",
        "label": {
            "text": "C major",
            "style": {"color": "rgba(255,255,255,0.55)", "fontSize": "26px", "fontWeight": "600"},
            "y": -20,
        },
    },
    {
        "from": 19.5,
        "to": 39.5,
        "color": "transparent",
        "label": {
            "text": "G major",
            "style": {"color": "rgba(255,255,255,0.55)", "fontSize": "26px", "fontWeight": "600"},
            "y": -20,
        },
    },
    {
        "from": 39.5,
        "to": 59.5,
        "color": "transparent",
        "label": {
            "text": "A minor",
            "style": {"color": "rgba(255,255,255,0.55)", "fontSize": "26px", "fontWeight": "600"},
            "y": -20,
        },
    },
    {
        "from": 59.5,
        "to": 79,
        "color": "transparent",
        "label": {
            "text": "F major",
            "style": {"color": "rgba(255,255,255,0.55)", "fontSize": "26px", "fontWeight": "600"},
            "y": -20,
        },
    },
]

chart.options.x_axis = {
    "categories": time_labels,
    "title": {
        "text": "Time (seconds)",
        "style": {"fontSize": "34px", "fontWeight": "600", "color": "#c0c0d0"},
        "margin": 28,
    },
    "labels": {"style": {"fontSize": "30px", "color": "#9e9eb8"}, "step": 1, "y": 40},
    "lineWidth": 0,
    "tickLength": 0,
    "gridLineWidth": 0,
    "plotLines": chord_boundaries,
    "plotBands": chord_labels,
}

chart.options.y_axis = {
    "categories": pitch_classes,
    "title": {
        "text": "Pitch Class",
        "style": {"fontSize": "34px", "fontWeight": "600", "color": "#c0c0d0"},
        "margin": 16,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#c0c0d0", "fontWeight": "600"}},
    "reversed": False,
    "lineWidth": 0,
    "gridLineWidth": 0,
}

chart.options.color_axis = {
    "min": 0,
    "max": 1.0,
    "stops": [
        [0, "#0d0221"],
        [0.15, "#1a0533"],
        [0.25, "#3c096c"],
        [0.35, "#5a189a"],
        [0.45, "#7b2cbf"],
        [0.55, "#9d4edd"],
        [0.65, "#c77dff"],
        [0.75, "#e0aaff"],
        [0.85, "#ffd166"],
        [0.95, "#ffbe0b"],
        [1, "#ffffff"],
    ],
    "labels": {"style": {"fontSize": "24px", "color": "#c0c0d0"}},
}

chart.options.legend = {
    "title": {"text": "Energy", "style": {"fontSize": "26px", "fontWeight": "600", "color": "#c0c0d0"}},
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 900,
    "symbolWidth": 32,
    "itemStyle": {"fontSize": "22px", "color": "#c0c0d0"},
    "x": -40,
    "margin": 30,
}

chart.options.tooltip = {
    "style": {"fontSize": "28px"},
    "headerFormat": "",
    "pointFormat": (
        "<b>{series.yAxis.categories.(point.y)}</b><br>"
        "Time: <b>{series.xAxis.categories.(point.x)}</b><br>"
        "Energy: <b>{point.value}</b>"
    ),
}

chart.options.credits = {"enabled": False}

chart.options.plot_options = {"heatmap": {"colsize": 1, "rowsize": 1, "borderWidth": 0}}

# Add heatmap series
series = HeatmapSeries()
series.name = "Chromagram"
series.data = heatmap_data
series.border_width = 0
series.data_labels = {"enabled": False}

chart.add_series(series)

# Download Highcharts JS and heatmap module
js_urls = [
    ("https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"),
    ("https://code.highcharts.com/modules/heatmap.js", "https://cdn.jsdelivr.net/npm/highcharts@11/modules/heatmap.js"),
]
js_parts = []
for primary, fallback in js_urls:
    for url in (primary, fallback):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                js_parts.append(response.read().decode("utf-8"))
            break
        except Exception:
            continue
all_js = "\n".join(js_parts)

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{all_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:#1a1a2e;">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>{html_str}</script>
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
