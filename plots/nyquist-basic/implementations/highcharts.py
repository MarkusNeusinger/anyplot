"""pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: highcharts unknown | Python 3.14.3
Quality: 79/100 | Created: 2026-03-20
"""

import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Second-order system: G(s) = 2 / (s(s+1)(0.5s+1))
np.random.seed(42)

omega = np.logspace(-2, 2, 600)
s = 1j * omega

K = 2.0
G = K / (s * (s + 1) * (0.5 * s + 1))

real_part = G.real
imag_part = G.imag

# Clip extreme values for display (very low frequencies go to -inf on imaginary)
mask = (np.abs(real_part) < 10) & (np.abs(imag_part) < 10)
real_clipped = real_part[mask]
imag_clipped = imag_part[mask]
omega_clipped = omega[mask]

# Unit circle for reference
theta = np.linspace(0, 2 * np.pi, 200)
circle_real = np.cos(theta)
circle_imag = np.sin(theta)

# Find key frequency points for annotation
# Gain crossover: |G(jw)| = 1
magnitudes = np.abs(G)
gain_crossover_idx = np.argmin(np.abs(magnitudes - 1.0))
gain_crossover_freq = omega[gain_crossover_idx]

# Phase crossover: Im(G) crosses zero (from negative to positive side)
sign_changes = np.where(np.diff(np.sign(imag_part[1:])))[0] + 1
phase_crossover_idx = sign_changes[0] if len(sign_changes) > 0 else 0
phase_crossover_freq = omega[phase_crossover_idx]

# Select annotation frequencies - spread out to avoid crowding near origin
annotation_freqs = [0.5, 0.7, 2.0, 5.0]
annotation_indices = [np.argmin(np.abs(omega - f)) for f in annotation_freqs]
annotation_indices = sorted(set(annotation_indices))

# Build Nyquist curve data (positive frequencies)
nyquist_data = [[round(float(r), 5), round(float(im), 5)] for r, im in zip(real_clipped, imag_clipped, strict=False)]

# Mirror curve (negative frequencies) - reflected across real axis
nyquist_mirror = [
    [round(float(r), 5), round(float(-im), 5)] for r, im in zip(real_clipped[::-1], imag_clipped[::-1], strict=False)
]

# Unit circle data
circle_data = [[round(float(r), 5), round(float(im), 5)] for r, im in zip(circle_real, circle_imag, strict=False)]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#ffffff",
    "marginBottom": 220,
    "marginLeft": 260,
    "marginRight": 180,
    "marginTop": 200,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "nyquist-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "600"},
}

chart.options.subtitle = {
    "text": "G(s) = 2 / [s(s+1)(0.5s+1)] \u2014 Open-Loop Frequency Response",
    "style": {"fontSize": "36px", "color": "#666666"},
}

# Determine axis range for equal scaling
axis_min = -4.0
axis_max = 3.0
y_min = -4.0
y_max = 4.0

chart.options.x_axis = {
    "title": {"text": "Real", "style": {"fontSize": "42px", "fontWeight": "600"}, "margin": 24},
    "labels": {"style": {"fontSize": "32px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.08)",
    "min": axis_min,
    "max": axis_max,
    "tickInterval": 1.0,
    "plotLines": [{"value": 0, "color": "rgba(0, 0, 0, 0.25)", "width": 2, "zIndex": 1}],
}

chart.options.y_axis = {
    "title": {"text": "Imaginary", "style": {"fontSize": "42px", "fontWeight": "600"}},
    "labels": {"style": {"fontSize": "32px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.08)",
    "min": y_min,
    "max": y_max,
    "tickInterval": 1.0,
    "plotLines": [{"value": 0, "color": "rgba(0, 0, 0, 0.25)", "width": 2, "zIndex": 1}],
}

chart.options.plot_options = {
    "line": {"lineWidth": 4, "marker": {"enabled": False}, "states": {"hover": {"lineWidthPlus": 1}}},
    "scatter": {"marker": {"radius": 10}},
    "series": {"animation": False},
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "30px", "fontWeight": "normal"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -40,
    "y": 100,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "style": {"fontSize": "26px"},
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderRadius": 8,
    "headerFormat": "",
    "pointFormat": "Real: {point.x:.3f}<br/>Imag: {point.y:.3f}",
}

# Annotations for frequency labels and critical point
annotation_labels = []

# Add frequency annotations along the curve with alternating offsets
label_offsets = [(-30, -40), (25, 30), (-25, -35), (30, 25)]
for i, idx in enumerate(annotation_indices):
    if idx < len(real_part) and mask[idx]:
        freq = omega[idx]
        r = float(real_part[idx])
        im = float(imag_part[idx])
        if abs(r) < 10 and abs(im) < 10:
            freq_text = f"\u03c9={freq:.1f}" if freq >= 0.1 else f"\u03c9={freq:.2f}"
            x_off, y_off = label_offsets[i % len(label_offsets)]
            annotation_labels.append(
                {
                    "point": {"x": round(r, 3), "y": round(im, 3), "xAxis": 0, "yAxis": 0},
                    "text": freq_text,
                    "style": {"fontSize": "28px", "fontWeight": "600", "color": "#306998"},
                    "backgroundColor": "rgba(255, 255, 255, 0.92)",
                    "borderColor": "#306998",
                    "borderWidth": 2,
                    "borderRadius": 6,
                    "padding": 10,
                    "shape": "rect",
                    "distance": 30,
                    "x": x_off,
                    "y": y_off,
                }
            )

# Critical point label
annotation_labels.append(
    {
        "point": {"x": -1.0, "y": 0.0, "xAxis": 0, "yAxis": 0},
        "text": "Critical Point (-1, 0)",
        "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#c0392b"},
        "backgroundColor": "rgba(255, 255, 255, 0.92)",
        "borderColor": "#c0392b",
        "borderWidth": 2,
        "borderRadius": 6,
        "padding": 10,
        "shape": "rect",
        "distance": 30,
        "y": -30,
    }
)

chart.options.annotations = [
    {"draggable": "", "labels": annotation_labels, "labelOptions": {"overflow": "none", "crop": False}}
]

# Nyquist curve (positive frequencies)
main_series = LineSeries()
main_series.data = nyquist_data
main_series.name = "G(j\u03c9) — \u03c9 > 0"
main_series.color = "#306998"
main_series.line_width = 5
main_series.marker = {"enabled": False}
main_series.z_index = 4
chart.add_series(main_series)

# Mirror curve (negative frequencies)
mirror_series = LineSeries()
mirror_series.data = nyquist_mirror
mirror_series.name = "G(j\u03c9) — \u03c9 < 0"
mirror_series.color = "#306998"
mirror_series.line_width = 4
mirror_series.dash_style = "Dash"
mirror_series.marker = {"enabled": False}
mirror_series.z_index = 3
chart.add_series(mirror_series)

# Unit circle
circle_series = LineSeries()
circle_series.data = circle_data
circle_series.name = "Unit Circle"
circle_series.color = "rgba(100, 100, 100, 0.4)"
circle_series.line_width = 3
circle_series.dash_style = "ShortDot"
circle_series.marker = {"enabled": False}
circle_series.z_index = 1
circle_series.enable_mouse_tracking = False
chart.add_series(circle_series)

# Critical point (-1, 0) marker
critical_series = ScatterSeries()
critical_series.data = [[-1.0, 0.0]]
critical_series.name = "Critical Point (-1, 0)"
critical_series.color = "#c0392b"
critical_series.marker = {
    "symbol": "diamond",
    "radius": 18,
    "fillColor": "#c0392b",
    "lineWidth": 4,
    "lineColor": "#ffffff",
}
critical_series.z_index = 6
chart.add_series(critical_series)

# Direction arrows - place small triangle markers at intervals along the curve
arrow_indices_pos = [
    np.argmin(np.abs(omega_clipped - 0.3)),
    np.argmin(np.abs(omega_clipped - 1.0)),
    np.argmin(np.abs(omega_clipped - 3.0)),
]
arrow_data = []
for ai in arrow_indices_pos:
    if ai < len(real_clipped) - 1:
        arrow_data.append([round(float(real_clipped[ai]), 4), round(float(imag_clipped[ai]), 4)])

arrow_series = ScatterSeries()
arrow_series.data = arrow_data
arrow_series.name = "Direction (\u03c9 increasing)"
arrow_series.color = "#306998"
arrow_series.marker = {
    "symbol": "triangle",
    "radius": 14,
    "fillColor": "#306998",
    "lineWidth": 2,
    "lineColor": "#ffffff",
}
arrow_series.z_index = 5
arrow_series.show_in_legend = False
chart.add_series(arrow_series)

# Save HTML
html_str = chart.to_js_literal()

hc_dir = Path(tempfile.mkdtemp())
subprocess.run(["npm", "pack", "highcharts", "--pack-destination", str(hc_dir)], capture_output=True, check=True)
hc_tgz = next(hc_dir.glob("highcharts-*.tgz"))
subprocess.run(["tar", "xzf", str(hc_tgz), "-C", str(hc_dir)], capture_output=True, check=True)
highcharts_js = (hc_dir / "package" / "highcharts.src.js").read_text(encoding="utf-8")
annotations_js_path = hc_dir / "package" / "modules" / "annotations.src.js"
annotations_js = annotations_js_path.read_text(encoding="utf-8") if annotations_js_path.exists() else ""

html_content = (
    '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="utf-8">\n'
    "    <script>" + highcharts_js + "</script>\n"
    "    <script>" + annotations_js + "</script>\n"
    '</head>\n<body style="margin:0;">\n'
    '    <div id="container" style="width: 3600px; height: 3600px;"></div>\n'
    "    <script>" + html_str + "</script>\n"
    "</body>\n</html>"
)

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
