"""pyplots.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Mild steel tensile test simulation
np.random.seed(42)

youngs_modulus = 210000  # MPa
yield_strength = 250  # MPa
uts = 400  # MPa
fracture_strain = 0.35
uts_strain = 0.22
yield_strain = yield_strength / youngs_modulus  # ~0.00119

# Elastic region (0 to yield)
strain_elastic = np.linspace(0, yield_strain, 60)
stress_elastic = youngs_modulus * strain_elastic

# Yield plateau (mild steel has a distinct yield point with small plateau)
strain_plateau = np.linspace(yield_strain, 0.015, 20)
stress_plateau = np.full_like(strain_plateau, yield_strength) + np.random.normal(0, 1.5, len(strain_plateau))

# Strain hardening region (from plateau to UTS)
strain_hardening = np.linspace(0.015, uts_strain, 120)
t_h = (strain_hardening - 0.015) / (uts_strain - 0.015)
stress_hardening = yield_strength + (uts - yield_strength) * (1 - (1 - t_h) ** 2)
stress_hardening += np.random.normal(0, 1.0, len(strain_hardening))

# Necking region (UTS to fracture - stress decreases)
strain_necking = np.linspace(uts_strain, fracture_strain, 80)
t_n = (strain_necking - uts_strain) / (fracture_strain - uts_strain)
stress_necking = uts - (uts - 300) * t_n**1.5
stress_necking += np.random.normal(0, 1.0, len(strain_necking))

# Combine all regions
strain = np.concatenate([strain_elastic, strain_plateau[1:], strain_hardening[1:], strain_necking[1:]])
stress = np.concatenate([stress_elastic, stress_plateau[1:], stress_hardening[1:], stress_necking[1:]])

# 0.2% offset line
offset = 0.002
offset_line_strain = np.array([offset, offset + yield_strength / youngs_modulus + 0.003])
offset_line_stress = np.array([0, (offset_line_strain[1] - offset) * youngs_modulus])
# Clamp offset line to where it would intersect the curve (~yield strength)
offset_line_strain_full = np.array([offset, offset + yield_strength / youngs_modulus])
offset_line_stress_full = np.array([0, yield_strength])

# Key points
yield_point_strain = offset + yield_strength / youngs_modulus  # ~0.00319
fracture_stress = float(stress_necking[-1])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 300,
    "marginLeft": 280,
    "marginRight": 200,
    "marginTop": 200,
    "spacingBottom": 40,
}

chart.options.title = {
    "text": "Mild Steel Tensile Test · line-stress-strain · highcharts · pyplots.ai",
    "style": {"fontSize": "60px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": f"E = {youngs_modulus:,} MPa · σ_y = {yield_strength} MPa · UTS = {uts} MPa",
    "style": {"fontSize": "40px", "color": "#666666"},
}

# X-axis (Strain)
chart.options.x_axis = {
    "title": {"text": "Engineering Strain (mm/mm)", "style": {"fontSize": "44px"}, "margin": 30},
    "labels": {"style": {"fontSize": "34px"}, "y": 45},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "min": 0,
    "max": 0.40,
    "tickInterval": 0.05,
    "plotBands": [
        {
            "from": 0,
            "to": 0.015,
            "color": "rgba(46, 204, 113, 0.08)",
            "label": {
                "text": "Elastic",
                "align": "center",
                "verticalAlign": "bottom",
                "y": -20,
                "style": {"fontSize": "30px", "color": "rgba(39, 174, 96, 0.8)", "fontWeight": "bold"},
            },
        },
        {
            "from": 0.015,
            "to": uts_strain,
            "color": "rgba(52, 152, 219, 0.06)",
            "label": {
                "text": "Strain Hardening",
                "align": "center",
                "verticalAlign": "bottom",
                "y": -20,
                "style": {"fontSize": "30px", "color": "rgba(41, 128, 185, 0.8)", "fontWeight": "bold"},
            },
        },
        {
            "from": uts_strain,
            "to": fracture_strain,
            "color": "rgba(231, 76, 60, 0.06)",
            "label": {
                "text": "Necking",
                "align": "center",
                "verticalAlign": "bottom",
                "y": -20,
                "style": {"fontSize": "30px", "color": "rgba(192, 57, 43, 0.8)", "fontWeight": "bold"},
            },
        },
    ],
}

# Y-axis (Stress)
chart.options.y_axis = {
    "title": {"text": "Engineering Stress (MPa)", "style": {"fontSize": "44px"}},
    "labels": {"style": {"fontSize": "34px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "min": 0,
    "max": 480,
    "plotLines": [
        {
            "value": yield_strength,
            "color": "rgba(39, 174, 96, 0.5)",
            "width": 2,
            "dashStyle": "Dot",
            "label": {
                "text": f"σ_y = {yield_strength} MPa",
                "align": "right",
                "x": -20,
                "y": -12,
                "style": {"fontSize": "28px", "color": "rgba(39, 174, 96, 0.9)"},
            },
            "zIndex": 3,
        },
        {
            "value": uts,
            "color": "rgba(41, 128, 185, 0.5)",
            "width": 2,
            "dashStyle": "Dot",
            "label": {
                "text": f"UTS = {uts} MPa",
                "align": "right",
                "x": -20,
                "y": -12,
                "style": {"fontSize": "28px", "color": "rgba(41, 128, 185, 0.9)"},
            },
            "zIndex": 3,
        },
    ],
}

# Plot options
chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"lineWidthPlus": 2}}},
    "series": {"animation": False},
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "34px", "fontWeight": "normal"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -40,
    "y": 80,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "style": {"fontSize": "28px"},
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderRadius": 8,
    "headerFormat": "",
    "pointFormat": "Strain: {point.x:.4f}<br/>Stress: {point.y:.1f} MPa",
}

# Main stress-strain curve
main_series = LineSeries()
main_series.data = [[round(float(s), 5), round(float(st), 1)] for s, st in zip(strain, stress, strict=True)]
main_series.name = "Stress-Strain Curve"
main_series.color = "#306998"
main_series.marker = {"enabled": False}
chart.add_series(main_series)

# 0.2% offset line
offset_series = LineSeries()
offset_series.data = [
    [round(float(offset_line_strain_full[0]), 5), round(float(offset_line_stress_full[0]), 1)],
    [round(float(offset_line_strain_full[1]), 5), round(float(offset_line_stress_full[1]), 1)],
]
offset_series.name = "0.2% Offset Line"
offset_series.color = "#e67e22"
offset_series.dash_style = "Dash"
offset_series.line_width = 3
offset_series.marker = {"enabled": False}
chart.add_series(offset_series)

# Critical points as scatter-like markers
yield_point_series = LineSeries()
yield_point_series.data = [[round(yield_point_strain, 5), yield_strength]]
yield_point_series.name = "Yield Point (0.2% offset)"
yield_point_series.color = "#27ae60"
yield_point_series.marker = {
    "enabled": True,
    "radius": 14,
    "symbol": "circle",
    "fillColor": "#27ae60",
    "lineWidth": 3,
    "lineColor": "#ffffff",
}
yield_point_series.line_width = 0
chart.add_series(yield_point_series)

uts_point_series = LineSeries()
uts_point_series.data = [[uts_strain, uts]]
uts_point_series.name = "Ultimate Tensile Strength"
uts_point_series.color = "#2980b9"
uts_point_series.marker = {
    "enabled": True,
    "radius": 14,
    "symbol": "diamond",
    "fillColor": "#2980b9",
    "lineWidth": 3,
    "lineColor": "#ffffff",
}
uts_point_series.line_width = 0
chart.add_series(uts_point_series)

fracture_series = LineSeries()
fracture_series.data = [[fracture_strain, round(fracture_stress, 1)]]
fracture_series.name = "Fracture Point"
fracture_series.color = "#c0392b"
fracture_series.marker = {
    "enabled": True,
    "radius": 14,
    "symbol": "triangle",
    "fillColor": "#c0392b",
    "lineWidth": 3,
    "lineColor": "#ffffff",
}
fracture_series.line_width = 0
chart.add_series(fracture_series)

# Save HTML
html_str = chart.to_js_literal()

# Load Highcharts JS from local npm package
hc_dir = Path(tempfile.mkdtemp())
subprocess.run(["npm", "pack", "highcharts", "--pack-destination", str(hc_dir)], capture_output=True, check=True)
hc_tgz = next(hc_dir.glob("highcharts-*.tgz"))
subprocess.run(["tar", "xzf", str(hc_tgz), "-C", str(hc_dir)], capture_output=True, check=True)
highcharts_js = (hc_dir / "package" / "highcharts.src.js").read_text(encoding="utf-8")

html_content = (
    '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="utf-8">\n'
    "    <script>" + highcharts_js + "</script>\n"
    '</head>\n<body style="margin:0;">\n'
    '    <div id="container" style="width: 4800px; height: 2700px;"></div>\n'
    "    <script>" + html_str + "</script>\n"
    "</body>\n</html>"
)

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
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
