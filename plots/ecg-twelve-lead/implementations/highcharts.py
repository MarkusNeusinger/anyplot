""" pyplots.ai
ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
Library: highcharts unknown | Python 3.14.3
Quality: 91/100 | Created: 2026-03-19
"""

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


# Data - Synthetic ECG with realistic P-QRS-T morphology
np.random.seed(42)

sampling_rate = 1000
duration = 2.5
n_samples = int(sampling_rate * duration)
t = np.linspace(0, duration, n_samples)

heart_rate = 72
beat_interval = 60.0 / heart_rate
n_beats = int(duration / beat_interval) + 1

# Lead morphology parameters: (scale, invert)
lead_params = {
    "I": (0.8, False),
    "II": (1.0, False),
    "III": (0.6, False),
    "aVR": (0.7, True),
    "aVL": (0.4, False),
    "aVF": (0.85, False),
    "V1": (0.5, False),
    "V2": (0.7, False),
    "V3": (0.9, False),
    "V4": (1.1, False),
    "V5": (1.0, False),
    "V6": (0.8, False),
}

# Generate all lead signals inline (flat KISS structure)
leads_data = {}
for name, (scale, invert) in lead_params.items():
    signal = np.zeros_like(t)
    for i in range(n_beats + 1):
        bc = 0.3 + i * beat_interval
        # P-wave
        signal += 0.15 * np.exp(-((t - (bc - 0.16)) ** 2) / (2 * 0.025**2))
        # Q-wave
        signal += -0.12 * np.exp(-((t - (bc - 0.04)) ** 2) / (2 * 0.008**2))
        # R-wave
        signal += 1.2 * np.exp(-((t - bc) ** 2) / (2 * 0.006**2))
        # S-wave
        signal += -0.25 * np.exp(-((t - (bc + 0.025)) ** 2) / (2 * 0.008**2))
        # T-wave
        signal += 0.3 * np.exp(-((t - (bc + 0.22)) ** 2) / (2 * 0.045**2))
    signal *= scale
    if invert:
        signal *= -1
    signal += np.random.normal(0, 0.005, len(t))
    leads_data[name] = signal

# V1-V2: make S-wave more prominent (rS pattern) for R-wave progression
for name in ["V1", "V2"]:
    for i in range(n_beats + 1):
        center = 0.3 + i * beat_interval
        leads_data[name] += -0.6 * np.exp(-((t - (center + 0.025)) ** 2) / (2 * 0.01**2))
        leads_data[name] += -0.5 * np.exp(-((t - center) ** 2) / (2 * 0.006**2))

# Clinical 3x4 grid layout
# Columns: (I, aVR, V1, V4), (II, aVL, V2, V5), (III, aVF, V3, V6)
grid_layout = [["I", "II", "III"], ["aVR", "aVL", "aVF"], ["V1", "V2", "V3"], ["V4", "V5", "V6"]]

# Spacing
col_width = 2.5
row_height = 2.0
n_rows = 4
n_cols = 3
total_time = col_width * n_cols
total_voltage = row_height * n_rows

# Build all series data with offsets
# Downsample for performance (every 4th sample)
step = 4
t_down = t[::step]

all_series = []
label_annotations = []

for row_idx, row_leads in enumerate(grid_layout):
    y_offset = (n_rows - 1 - row_idx) * row_height + row_height / 2
    for col_idx, lead_name in enumerate(row_leads):
        x_offset = col_idx * col_width
        signal = leads_data[lead_name][::step]

        data_points = []
        for i in range(len(t_down)):
            x_val = round(float(t_down[i] + x_offset), 4)
            y_val = round(float(signal[i] + y_offset), 4)
            data_points.append([x_val, y_val])

        series_obj = LineSeries()
        series_obj.data = data_points
        series_obj.name = lead_name
        series_obj.color = "#1a1a2e"
        series_obj.line_width = 2
        series_obj.marker = {"enabled": False}
        series_obj.enable_mouse_tracking = False
        series_obj.show_in_legend = False
        all_series.append(series_obj)

        # Lead label position
        label_annotations.append(
            {
                "point": {"x": x_offset + 0.05, "y": y_offset + 0.75, "xAxis": 0, "yAxis": 0},
                "text": lead_name,
                "style": {"fontSize": "32px", "fontWeight": "bold", "color": "#1a1a2e"},
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shape": "rect",
                "padding": 4,
            }
        )

# Lead II rhythm strip at the bottom
rhythm_t = np.linspace(0, total_time, int(sampling_rate * total_time))[::step]
rhythm_signal = np.tile(leads_data["II"], n_cols)[: len(rhythm_t) * step][::step]
if len(rhythm_signal) > len(rhythm_t):
    rhythm_signal = rhythm_signal[: len(rhythm_t)]
elif len(rhythm_signal) < len(rhythm_t):
    rhythm_t = rhythm_t[: len(rhythm_signal)]

rhythm_y_offset = -1.0
rhythm_data = []
for i in range(len(rhythm_t)):
    rhythm_data.append([round(float(rhythm_t[i]), 4), round(float(rhythm_signal[i] + rhythm_y_offset), 4)])

rhythm_series = LineSeries()
rhythm_series.data = rhythm_data
rhythm_series.name = "Lead II (rhythm)"
rhythm_series.color = "#1a1a2e"
rhythm_series.line_width = 2
rhythm_series.marker = {"enabled": False}
rhythm_series.enable_mouse_tracking = False
rhythm_series.show_in_legend = False
all_series.append(rhythm_series)

label_annotations.append(
    {
        "point": {"x": 0.05, "y": rhythm_y_offset + 0.75, "xAxis": 0, "yAxis": 0},
        "text": "II",
        "style": {"fontSize": "32px", "fontWeight": "bold", "color": "#1a1a2e"},
        "backgroundColor": "transparent",
        "borderWidth": 0,
        "shape": "rect",
        "padding": 4,
    }
)

# 1mV calibration pulse - drawn as a square wave series at the left margin
cal_y_base = (n_rows - 1) * row_height + row_height / 2
cal_x = -0.3
cal_data = [
    [cal_x, cal_y_base],
    [cal_x, cal_y_base],
    [cal_x, cal_y_base + 1.0],
    [cal_x + 0.15, cal_y_base + 1.0],
    [cal_x + 0.15, cal_y_base],
    [cal_x + 0.15, cal_y_base],
]
cal_series = LineSeries()
cal_series.data = [[round(float(x), 4), round(float(y), 4)] for x, y in cal_data]
cal_series.name = "1 mV cal"
cal_series.color = "#1a1a2e"
cal_series.line_width = 3
cal_series.marker = {"enabled": False}
cal_series.enable_mouse_tracking = False
cal_series.show_in_legend = False
all_series.append(cal_series)

# Calibration text label next to the pulse
label_annotations.append(
    {
        "point": {"x": cal_x + 0.07, "y": cal_y_base + 1.15, "xAxis": 0, "yAxis": 0},
        "text": "1 mV",
        "style": {"fontSize": "24px", "fontWeight": "600", "color": "#555"},
        "backgroundColor": "transparent",
        "borderWidth": 0,
        "shape": "rect",
        "padding": 2,
    }
)

# Grid lines for ECG paper effect
# Major grid: every 0.2s horizontal, every 0.5mV vertical
# Minor grid: every 0.04s horizontal, every 0.1mV vertical
x_minor_lines = []
x_major_lines = []
for x_val in np.arange(0, total_time + 0.01, 0.04):
    x_val_r = round(float(x_val), 4)
    is_major = abs(x_val % 0.2) < 0.001 or abs(x_val % 0.2 - 0.2) < 0.001
    if is_major:
        x_major_lines.append({"value": x_val_r, "color": "rgba(200, 80, 80, 0.35)", "width": 1.5})
    else:
        x_minor_lines.append({"value": x_val_r, "color": "rgba(200, 80, 80, 0.15)", "width": 0.5})

y_minor_lines = []
y_major_lines = []
y_min = rhythm_y_offset - 1.0
y_max = n_rows * row_height + 0.5
for y_val in np.arange(y_min, y_max + 0.01, 0.1):
    y_val_r = round(float(y_val), 4)
    is_major = abs(y_val % 0.5) < 0.001 or abs(y_val % 0.5 - 0.5) < 0.001
    if is_major:
        y_major_lines.append({"value": y_val_r, "color": "rgba(200, 80, 80, 0.35)", "width": 1.5})
    else:
        y_minor_lines.append({"value": y_val_r, "color": "rgba(200, 80, 80, 0.15)", "width": 0.5})

# Column separator lines
col_separators = []
for c in range(1, n_cols):
    col_separators.append({"value": c * col_width, "color": "rgba(100, 40, 40, 0.5)", "width": 2, "dashStyle": "Solid"})

# Row separator lines
row_separators = []
for r in range(n_rows + 1):
    y_val = r * row_height - 0.5
    row_separators.append(
        {"value": round(float(y_val), 4), "color": "rgba(100, 40, 40, 0.5)", "width": 2, "dashStyle": "Solid"}
    )
# Separator above rhythm strip
row_separators.append({"value": round(float(rhythm_y_offset - 0.5), 4), "color": "rgba(100, 40, 40, 0.5)", "width": 2})

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#FFF5F0",
    "marginTop": 120,
    "marginBottom": 80,
    "marginLeft": 120,
    "marginRight": 60,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "ecg-twelve-lead \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "42px", "fontWeight": "600", "color": "#1a1a2e"},
    "y": 30,
}

chart.options.subtitle = {
    "text": "Normal Sinus Rhythm \u2014 25 mm/s, 10 mm/mV",
    "style": {"fontSize": "26px", "fontWeight": "normal", "color": "#666"},
    "y": 72,
}

chart.options.x_axis = {
    "min": -0.5,
    "max": total_time + 0.1,
    "title": {"text": None},
    "labels": {"enabled": False},
    "lineWidth": 0,
    "tickLength": 0,
    "gridLineWidth": 0,
    "plotLines": x_major_lines + x_minor_lines + col_separators,
}

chart.options.y_axis = {
    "min": rhythm_y_offset - 1.0,
    "max": n_rows * row_height + 0.5,
    "title": {"text": None},
    "labels": {"enabled": False},
    "lineWidth": 0,
    "gridLineWidth": 0,
    "plotLines": y_major_lines + y_minor_lines + row_separators,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.tooltip = {"enabled": False}

chart.options.plot_options = {"line": {"animation": False, "lineWidth": 2, "states": {"hover": {"enabled": False}}}}

chart.options.annotations = [
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": "transparent",
            "borderWidth": 0,
            "style": {"fontSize": "32px", "fontWeight": "bold", "color": "#1a1a2e"},
        },
        "labels": label_annotations,
    }
]

for s in all_series:
    chart.add_series(s)

# Download Highcharts JS and annotations module
js_urls = [
    ("https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"),
    (
        "https://code.highcharts.com/modules/annotations.js",
        "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js",
    ),
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

# Generate HTML
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{all_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:#FFF5F0;">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with headless Chrome
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
