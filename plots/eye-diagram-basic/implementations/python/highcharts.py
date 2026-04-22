""" pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: highcharts unknown | Python 3.14.3
Quality: 91/100 | Updated: 2026-03-18
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


# Data - Simulate NRZ eye diagram with 300 overlaid traces
np.random.seed(42)

n_traces = 300
samples_per_ui = 150
n_ui = 2
total_samples = samples_per_ui * n_ui
noise_sigma = 0.05
jitter_sigma = 0.03

time_norm = np.linspace(0, n_ui, total_samples)

# Generate all traces and accumulate into a 2D density histogram
n_voltage_bins = 120
n_time_bins = 200
voltage_range = (-0.3, 1.3)

all_times = []
all_voltages = []

for _ in range(n_traces):
    bits = np.random.randint(0, 2, size=6)

    # Build voltage waveform with smooth transitions (raised cosine)
    signal = np.zeros(total_samples)

    for sample_idx in range(total_samples):
        ui_pos = sample_idx / samples_per_ui
        bit_idx = min(int(ui_pos) + 2, len(bits) - 1)
        frac = ui_pos - int(ui_pos)
        current_bit = bits[bit_idx]
        prev_bit = bits[max(bit_idx - 1, 0)]

        transition_width = 0.2
        if frac < transition_width and prev_bit != current_bit:
            alpha = 0.5 * (1 - np.cos(np.pi * frac / transition_width))
            signal[sample_idx] = prev_bit + alpha * (current_bit - prev_bit)
        else:
            signal[sample_idx] = current_bit

    jitter = np.random.normal(0, jitter_sigma)
    jittered_time = time_norm + jitter
    signal += np.random.normal(0, noise_sigma, total_samples)

    all_times.append(jittered_time)
    all_voltages.append(signal)

# Use np.histogram2d for efficient density binning
all_times_flat = np.concatenate(all_times)
all_voltages_flat = np.concatenate(all_voltages)

density, _, _ = np.histogram2d(
    all_voltages_flat,
    all_times_flat,
    bins=[n_voltage_bins, n_time_bins],
    range=[[voltage_range[0], voltage_range[1]], [0, n_ui]],
)
density_norm = density / density.max()

# Build heatmap data [x_index, y_index, value] - only non-zero cells
nonzero = np.argwhere(density_norm > 0.001)
heatmap_data = [[int(x), int(y), round(float(density_norm[y, x]), 4)] for y, x in nonzero]

# Compute eye metrics for annotations
# Eye center is at 0.5 UI (middle of the first unit interval, where the eye opens)
eye_center_x = n_time_bins // 4  # 0.5 UI = quarter of the 2-UI window
v_mid_bin = int((0.5 - voltage_range[0]) / (voltage_range[1] - voltage_range[0]) * (n_voltage_bins - 1))
v_step = (voltage_range[1] - voltage_range[0]) / n_voltage_bins
t_step = n_ui / n_time_bins

# Eye height: vertical gap in density at center time slice
center_col = density_norm[:, eye_center_x]
eye_bottom = eye_top = v_mid_bin
for i in range(v_mid_bin, 0, -1):
    if center_col[i] > 0.08:
        eye_bottom = i + 1
        break
for i in range(v_mid_bin, n_voltage_bins):
    if center_col[i] > 0.08:
        eye_top = i - 1
        break
eye_height_v = (eye_top - eye_bottom) * v_step

# Eye width: horizontal span of opening at mid-voltage
mid_row = density_norm[v_mid_bin, :]
# Find contiguous low-density region around eye_center_x
eye_left = eye_center_x
eye_right = eye_center_x
for i in range(eye_center_x, 0, -1):
    if mid_row[i] > 0.08:
        eye_left = i + 1
        break
for i in range(eye_center_x, n_time_bins):
    if mid_row[i] > 0.08:
        eye_right = i - 1
        break
eye_width_ui = (eye_right - eye_left) * t_step

# Axis labels
time_categories = [f"{t:.2f}" if i % 25 == 0 else "" for i, t in enumerate(np.linspace(0, 2, n_time_bins))]
voltage_values = np.linspace(voltage_range[0], voltage_range[1], n_voltage_bins)
voltage_categories = [f"{v:.1f}" if i % 20 == 0 else "" for i, v in enumerate(voltage_values)]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#0a0a14",
    "marginTop": 160,
    "marginBottom": 220,
    "marginRight": 280,
    "marginLeft": 220,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "eye-diagram-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "600", "color": "#e0e0e0"},
    "y": 30,
}

chart.options.subtitle = {
    "text": "NRZ Signal \u2014 300 Overlaid Traces with Noise (\u03c3=5%) and Jitter (\u03c3=3%)",
    "style": {"fontSize": "28px", "fontWeight": "normal", "color": "#8e8ea8"},
    "y": 80,
}

# Plot lines to mark UI boundaries and signal levels
ui_boundary = int(n_time_bins / 2)
chart.options.x_axis = {
    "categories": time_categories,
    "title": {
        "text": "Time (Unit Intervals)",
        "style": {"fontSize": "34px", "fontWeight": "600", "color": "#c0c0d0"},
        "margin": 28,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#8e8ea8"}, "step": 1, "y": 40, "rotation": 0},
    "lineWidth": 0,
    "tickLength": 0,
    "gridLineWidth": 0,
    "plotLines": [
        {
            "value": ui_boundary,
            "color": "rgba(255,255,255,0.25)",
            "width": 3,
            "dashStyle": "Dash",
            "label": {
                "text": "1.0 UI",
                "style": {"color": "rgba(255,255,255,0.5)", "fontSize": "22px"},
                "align": "left",
                "x": 8,
                "y": 20,
            },
        }
    ],
}

# Voltage axis - mark 0V and 1V levels
level_0_bin = int((0 - voltage_range[0]) / (voltage_range[1] - voltage_range[0]) * (n_voltage_bins - 1))
level_1_bin = int((1 - voltage_range[0]) / (voltage_range[1] - voltage_range[0]) * (n_voltage_bins - 1))

chart.options.y_axis = {
    "categories": voltage_categories,
    "title": {
        "text": "Voltage (V)",
        "style": {"fontSize": "34px", "fontWeight": "600", "color": "#c0c0d0"},
        "margin": 16,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#8e8ea8"}},
    "reversed": False,
    "lineWidth": 0,
    "gridLineWidth": 0,
    "plotLines": [
        {
            "value": level_0_bin,
            "color": "rgba(255,255,255,0.2)",
            "width": 2,
            "dashStyle": "Dot",
            "label": {
                "text": "0 V",
                "style": {"color": "rgba(255,255,255,0.45)", "fontSize": "20px"},
                "align": "right",
                "x": -8,
            },
        },
        {
            "value": level_1_bin,
            "color": "rgba(255,255,255,0.2)",
            "width": 2,
            "dashStyle": "Dot",
            "label": {
                "text": "1 V",
                "style": {"color": "rgba(255,255,255,0.45)", "fontSize": "20px"},
                "align": "right",
                "x": -8,
            },
        },
    ],
}

chart.options.color_axis = {
    "min": 0,
    "max": 1.0,
    "stops": [
        [0, "#0a0a14"],
        [0.05, "#0d1b3e"],
        [0.12, "#152d6b"],
        [0.2, "#1e4d8c"],
        [0.3, "#306998"],
        [0.4, "#2a9d8f"],
        [0.5, "#52b788"],
        [0.65, "#e9c46a"],
        [0.8, "#f4a261"],
        [0.9, "#e76f51"],
        [1, "#ffffff"],
    ],
    "labels": {"style": {"fontSize": "24px", "color": "#c0c0d0"}},
}

chart.options.legend = {
    "title": {"text": "Trace Density", "style": {"fontSize": "26px", "fontWeight": "600", "color": "#c0c0d0"}},
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 900,
    "symbolWidth": 28,
    "itemStyle": {"fontSize": "22px", "color": "#c0c0d0"},
    "x": -20,
    "margin": 20,
}

chart.options.tooltip = {
    "style": {"fontSize": "24px"},
    "headerFormat": "",
    "pointFormat": "Time: <b>{point.x}</b> UI<br>Voltage: <b>{point.y}</b> V<br>Density: <b>{point.value}</b>",
}

chart.options.credits = {"enabled": False}

chart.options.plot_options = {"heatmap": {"colsize": 1, "rowsize": 1, "borderWidth": 0}}

# Annotations using Highcharts annotations API for eye measurements
chart.options.annotations = [
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": "rgba(10, 10, 20, 0.85)",
            "borderColor": "rgba(255, 255, 255, 0.3)",
            "borderWidth": 2,
            "borderRadius": 8,
            "style": {"color": "#e0e0e0", "fontSize": "26px", "fontWeight": "600"},
            "padding": 14,
        },
        "labels": [
            {
                "point": {"x": eye_center_x, "y": v_mid_bin - 8, "xAxis": 0, "yAxis": 0},
                "text": f"Eye Height: {eye_height_v:.3f} V",
            },
            {
                "point": {"x": eye_center_x + 10, "y": v_mid_bin + 8, "xAxis": 0, "yAxis": 0},
                "text": f"Eye Width: {eye_width_ui:.3f} UI",
            },
        ],
    }
]

# Add heatmap series
series = HeatmapSeries()
series.name = "Eye Diagram"
series.data = heatmap_data
series.border_width = 0
series.data_labels = {"enabled": False}

chart.add_series(series)

# Download Highcharts JS, heatmap module, and annotations module
js_urls = [
    ("https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"),
    ("https://code.highcharts.com/modules/heatmap.js", "https://cdn.jsdelivr.net/npm/highcharts@11/modules/heatmap.js"),
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

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{all_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:#0a0a14;">
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
