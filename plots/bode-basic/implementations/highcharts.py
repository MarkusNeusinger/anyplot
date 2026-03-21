""" pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: highcharts unknown | Python 3.14.3
Quality: 89/100 | Created: 2026-03-21
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


# Data - Open-loop transfer function: G(s) = 10 / ((s/1+1)(s/5+1)(s/20+1))
# Three-pole system with clear gain and phase margins
omega = np.logspace(-2, 3, 600)
s = 1j * omega

K = 10.0
G = K / ((s / 1 + 1) * (s / 5 + 1) * (s / 20 + 1))

magnitude_db = 20 * np.log10(np.abs(G))
phase_deg = np.degrees(np.unwrap(np.angle(G)))

# Frequency in Hz for display
frequency_hz = omega / (2 * np.pi)

# Find gain crossover frequency (|G| crosses 0 dB from above)
sign_changes_mag = np.where(np.diff(np.sign(magnitude_db)))[0]
gain_crossover_idx = sign_changes_mag[0] if len(sign_changes_mag) > 0 else np.argmin(np.abs(magnitude_db))
gain_crossover_hz = frequency_hz[gain_crossover_idx]
phase_at_gain_crossover = phase_deg[gain_crossover_idx]
phase_margin = 180 + phase_at_gain_crossover

# Find phase crossover frequency (phase crosses -180 deg)
sign_changes_phase = np.where(np.diff(np.sign(phase_deg + 180)))[0]
phase_crossover_idx = sign_changes_phase[0] if len(sign_changes_phase) > 0 else np.argmin(np.abs(phase_deg + 180))
phase_crossover_hz = frequency_hz[phase_crossover_idx]
mag_at_phase_crossover = magnitude_db[phase_crossover_idx]
gain_margin = -mag_at_phase_crossover

# Build chart data
mag_data = [[round(float(f), 6), round(float(m), 3)] for f, m in zip(frequency_hz, magnitude_db, strict=True)]
phase_data = [[round(float(f), 6), round(float(p), 3)] for f, p in zip(frequency_hz, phase_deg, strict=True)]

# Chart layout
chart_width = 4800
chart_height = 2700
margin_top = 180
margin_bottom = 180
margin_left = 300
margin_right = 160
panel_gap = 100

plot_area_height = chart_height - margin_top - margin_bottom - panel_gap
panel_height = plot_area_height / 2

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": chart_width,
    "height": chart_height,
    "backgroundColor": "#fafbfc",
    "plotBackgroundColor": "#ffffff",
    "plotBorderWidth": 1,
    "plotBorderColor": "rgba(0, 0, 0, 0.12)",
    "marginTop": margin_top,
    "marginBottom": margin_bottom,
    "marginLeft": margin_left,
    "marginRight": margin_right,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "bode-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "700", "color": "#1a1a2e", "letterSpacing": "0.5px"},
    "y": 60,
}

chart.options.subtitle = {
    "text": "G(s) = 10 / [(s+1)(s/5+1)(s/20+1)] \u2014 Open-Loop Frequency Response",
    "style": {"fontSize": "32px", "color": "#555555", "fontStyle": "italic"},
    "y": 115,
}

chart.options.credits = {"enabled": False}

# Panel positioning as percentages
top_pct = round(margin_top / chart_height * 100, 1)
panel_pct = round(panel_height / chart_height * 100, 1)
bottom_panel_top_pct = round((margin_top + panel_height + panel_gap) / chart_height * 100, 1)

chart.options.x_axis = [
    {
        "id": "x-mag",
        "type": "logarithmic",
        "title": {"text": None},
        "labels": {"style": {"fontSize": "26px", "color": "#555555"}},
        "tickInterval": 1,
        "minorTickInterval": None,
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.08)",
        "lineWidth": 2,
        "lineColor": "#333333",
        "tickWidth": 0,
        "crosshair": {"width": 2, "color": "rgba(0, 0, 0, 0.15)", "dashStyle": "Dot", "snap": False},
        "top": f"{top_pct}%",
        "height": f"{panel_pct}%",
        "offset": 0,
        "plotLines": [
            {
                "value": float(gain_crossover_hz),
                "color": "rgba(48, 105, 152, 0.25)",
                "width": 2,
                "dashStyle": "LongDash",
                "zIndex": 2,
            },
            {
                "value": float(phase_crossover_hz),
                "color": "rgba(211, 84, 0, 0.25)",
                "width": 2,
                "dashStyle": "LongDash",
                "zIndex": 2,
            },
        ],
    },
    {
        "id": "x-phase",
        "type": "logarithmic",
        "title": {
            "text": "Frequency (Hz)",
            "style": {"fontSize": "34px", "fontWeight": "600", "color": "#333333"},
            "margin": 20,
        },
        "labels": {"style": {"fontSize": "26px", "color": "#555555"}},
        "tickInterval": 1,
        "minorTickInterval": None,
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.08)",
        "lineWidth": 2,
        "lineColor": "#333333",
        "tickWidth": 0,
        "crosshair": {"width": 2, "color": "rgba(0, 0, 0, 0.15)", "dashStyle": "Dot", "snap": False},
        "top": f"{bottom_panel_top_pct}%",
        "height": f"{panel_pct}%",
        "offset": 0,
        "plotLines": [
            {
                "value": float(gain_crossover_hz),
                "color": "rgba(48, 105, 152, 0.25)",
                "width": 2,
                "dashStyle": "LongDash",
                "zIndex": 2,
            },
            {
                "value": float(phase_crossover_hz),
                "color": "rgba(211, 84, 0, 0.25)",
                "width": 2,
                "dashStyle": "LongDash",
                "zIndex": 2,
            },
        ],
    },
]

chart.options.y_axis = [
    {
        "id": "y-mag",
        "title": {"text": "Magnitude (dB)", "style": {"fontSize": "34px", "fontWeight": "600", "color": "#306998"}},
        "labels": {"style": {"fontSize": "26px", "color": "#555555"}},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.08)",
        "lineWidth": 2,
        "lineColor": "#333333",
        "plotLines": [
            {
                "value": 0,
                "color": "#95a5a6",
                "width": 3,
                "dashStyle": "Dash",
                "zIndex": 3,
                "label": {
                    "text": "0 dB",
                    "style": {"fontSize": "26px", "color": "#95a5a6", "fontWeight": "600"},
                    "align": "right",
                    "x": -10,
                },
            }
        ],
        "top": f"{top_pct}%",
        "height": f"{panel_pct}%",
        "offset": 0,
    },
    {
        "id": "y-phase",
        "title": {"text": "Phase (degrees)", "style": {"fontSize": "34px", "fontWeight": "600", "color": "#e67e22"}},
        "labels": {"style": {"fontSize": "26px", "color": "#555555"}},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.08)",
        "lineWidth": 2,
        "lineColor": "#333333",
        "plotLines": [
            {
                "value": -180,
                "color": "#95a5a6",
                "width": 3,
                "dashStyle": "Dash",
                "zIndex": 3,
                "label": {
                    "text": "-180\u00b0",
                    "style": {"fontSize": "26px", "color": "#95a5a6", "fontWeight": "600"},
                    "align": "right",
                    "x": -10,
                },
            }
        ],
        "top": f"{bottom_panel_top_pct}%",
        "height": f"{panel_pct}%",
        "offset": 0,
    },
]

chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"lineWidthPlus": 1}}},
    "scatter": {"marker": {"radius": 14}},
    "series": {"animation": False},
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px", "fontWeight": "normal"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -20,
    "y": 140,
    "itemMarginBottom": 8,
    "backgroundColor": "rgba(255, 255, 255, 0.85)",
    "borderRadius": 6,
    "padding": 16,
}

chart.options.tooltip = {
    "style": {"fontSize": "24px"},
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderRadius": 8,
    "shadow": {"color": "rgba(0, 0, 0, 0.1)", "offsetX": 2, "offsetY": 2, "width": 4},
    "headerFormat": '<span style="font-size: 22px; color: #666;">f = {point.x:.4f} Hz</span><br/>',
    "pointFormat": '<span style="color:{series.color};">\u25cf</span> {series.name}: <b>{point.y:.2f}</b><br/>',
}

# Magnitude series
mag_series = LineSeries()
mag_series.data = mag_data
mag_series.name = "Magnitude"
mag_series.color = "#306998"
mag_series.x_axis = 0
mag_series.y_axis = 0
mag_series.z_index = 4
chart.add_series(mag_series)

# Phase series
phase_series = LineSeries()
phase_series.data = phase_data
phase_series.name = "Phase"
phase_series.color = "#e67e22"
phase_series.x_axis = 1
phase_series.y_axis = 1
phase_series.z_index = 4
chart.add_series(phase_series)

# Gain crossover marker on magnitude plot
gc_mag_marker = ScatterSeries()
gc_mag_marker.data = [[round(float(gain_crossover_hz), 6), 0.0]]
gc_mag_marker.name = f"Gain Crossover ({gain_crossover_hz:.2f} Hz)"
gc_mag_marker.color = "#306998"
gc_mag_marker.marker = {
    "symbol": "diamond",
    "radius": 18,
    "fillColor": "#306998",
    "lineWidth": 4,
    "lineColor": "#ffffff",
}
gc_mag_marker.x_axis = 0
gc_mag_marker.y_axis = 0
gc_mag_marker.z_index = 6
gc_mag_marker.show_in_legend = False
chart.add_series(gc_mag_marker)

# Phase margin marker on phase plot
gc_phase_marker = ScatterSeries()
gc_phase_marker.data = [[round(float(gain_crossover_hz), 6), round(float(phase_at_gain_crossover), 3)]]
gc_phase_marker.name = f"PM = {phase_margin:.1f}\u00b0"
gc_phase_marker.color = "#8e44ad"
gc_phase_marker.marker = {
    "symbol": "diamond",
    "radius": 18,
    "fillColor": "#8e44ad",
    "lineWidth": 4,
    "lineColor": "#ffffff",
}
gc_phase_marker.x_axis = 1
gc_phase_marker.y_axis = 1
gc_phase_marker.z_index = 6
chart.add_series(gc_phase_marker)

# Gain margin marker on magnitude plot
pc_mag_marker = ScatterSeries()
pc_mag_marker.data = [[round(float(phase_crossover_hz), 6), round(float(mag_at_phase_crossover), 3)]]
pc_mag_marker.name = f"GM = {gain_margin:.1f} dB"
pc_mag_marker.color = "#d35400"
pc_mag_marker.marker = {
    "symbol": "circle",
    "radius": 18,
    "fillColor": "#d35400",
    "lineWidth": 4,
    "lineColor": "#ffffff",
}
pc_mag_marker.x_axis = 0
pc_mag_marker.y_axis = 0
pc_mag_marker.z_index = 6
chart.add_series(pc_mag_marker)

# Phase crossover marker on phase plot
pc_phase_marker = ScatterSeries()
pc_phase_marker.data = [[round(float(phase_crossover_hz), 6), -180.0]]
pc_phase_marker.name = f"Phase Crossover ({phase_crossover_hz:.2f} Hz)"
pc_phase_marker.color = "#d35400"
pc_phase_marker.marker = {
    "symbol": "circle",
    "radius": 18,
    "fillColor": "#d35400",
    "lineWidth": 4,
    "lineColor": "#ffffff",
}
pc_phase_marker.x_axis = 1
pc_phase_marker.y_axis = 1
pc_phase_marker.z_index = 6
pc_phase_marker.show_in_legend = False
chart.add_series(pc_phase_marker)

# Vertical connector line for gain margin (from magnitude to 0 dB reference)
gm_connector = LineSeries()
gm_connector.data = [
    [round(float(phase_crossover_hz), 6), round(float(mag_at_phase_crossover), 3)],
    [round(float(phase_crossover_hz), 6), 0.0],
]
gm_connector.name = "GM connector"
gm_connector.color = "#d35400"
gm_connector.dash_style = "ShortDash"
gm_connector.line_width = 3
gm_connector.marker = {"enabled": False}
gm_connector.enable_mouse_tracking = False
gm_connector.x_axis = 0
gm_connector.y_axis = 0
gm_connector.z_index = 5
gm_connector.show_in_legend = False
chart.add_series(gm_connector)

# Vertical connector line for phase margin (from phase to -180° reference)
pm_connector = LineSeries()
pm_connector.data = [
    [round(float(gain_crossover_hz), 6), -180.0],
    [round(float(gain_crossover_hz), 6), round(float(phase_at_gain_crossover), 3)],
]
pm_connector.name = "PM connector"
pm_connector.color = "#8e44ad"
pm_connector.dash_style = "ShortDash"
pm_connector.line_width = 3
pm_connector.marker = {"enabled": False}
pm_connector.enable_mouse_tracking = False
pm_connector.x_axis = 1
pm_connector.y_axis = 1
pm_connector.z_index = 5
pm_connector.show_in_legend = False
chart.add_series(pm_connector)

# Gain margin annotation label
gm_annotation = ScatterSeries()
gm_annotation.data = [[round(float(phase_crossover_hz), 6), round(float(mag_at_phase_crossover / 2), 3)]]
gm_annotation.name = "GM label"
gm_annotation.color = "#d35400"
gm_annotation.marker = {"enabled": False}
gm_annotation.data_labels = {
    "enabled": True,
    "format": f"GM = {gain_margin:.1f} dB",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#d35400", "textOutline": "3px #ffffff"},
    "x": 70,
    "y": 0,
}
gm_annotation.x_axis = 0
gm_annotation.y_axis = 0
gm_annotation.z_index = 7
gm_annotation.show_in_legend = False
chart.add_series(gm_annotation)

# Phase margin annotation label
pm_annotation = ScatterSeries()
pm_annotation.data = [[round(float(gain_crossover_hz), 6), round(float((phase_at_gain_crossover - 180) / 2), 3)]]
pm_annotation.name = "PM label"
pm_annotation.color = "#8e44ad"
pm_annotation.marker = {"enabled": False}
pm_annotation.data_labels = {
    "enabled": True,
    "format": f"PM = {phase_margin:.1f}\u00b0",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#8e44ad", "textOutline": "3px #ffffff"},
    "x": 70,
    "y": 0,
}
pm_annotation.x_axis = 1
pm_annotation.y_axis = 1
pm_annotation.z_index = 7
pm_annotation.show_in_legend = False
chart.add_series(pm_annotation)

# Save
html_str = chart.to_js_literal()

hc_dir = Path(tempfile.mkdtemp())
subprocess.run(["npm", "pack", "highcharts", "--pack-destination", str(hc_dir)], capture_output=True, check=True)
hc_tgz = next(hc_dir.glob("highcharts-*.tgz"))
subprocess.run(["tar", "xzf", str(hc_tgz), "-C", str(hc_dir)], capture_output=True, check=True)
highcharts_js = (hc_dir / "package" / "highcharts.src.js").read_text(encoding="utf-8")

html_content = (
    '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="utf-8">\n'
    "    <script>" + highcharts_js + "</script>\n"
    '</head>\n<body style="margin:0;">\n'
    f'    <div id="container" style="width: {chart_width}px; height: {chart_height}px;"></div>\n'
    "    <script>" + html_str + "</script>\n"
    "</body>\n</html>"
)

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
