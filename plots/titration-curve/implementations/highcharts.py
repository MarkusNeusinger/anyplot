"""pyplots.ai
titration-curve: Acid-Base Titration Curve
Library: highcharts unknown | Python 3.14.3
Quality: 87/100 | Created: 2026-03-21
"""

import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries, LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Strong acid/strong base: 25 mL of 0.1 M HCl titrated with 0.1 M NaOH
c_acid = 0.1
v_acid = 25.0
c_base = 0.1

volume_naoh = np.linspace(0.01, 50.0, 500)

ph_values = np.zeros_like(volume_naoh)
for i, v in enumerate(volume_naoh):
    total_vol = (v_acid + v) / 1000.0
    moles_acid = c_acid * v_acid / 1000.0
    moles_base = c_base * v / 1000.0

    if moles_base < moles_acid - 1e-10:
        h_plus = (moles_acid - moles_base) / total_vol
        ph_values[i] = -np.log10(h_plus)
    elif abs(moles_base - moles_acid) < 1e-10:
        ph_values[i] = 7.0
    else:
        oh_minus = (moles_base - moles_acid) / total_vol
        poh = -np.log10(oh_minus)
        ph_values[i] = 14.0 - poh

# Derivative dpH/dV
dph_dv = np.gradient(ph_values, volume_naoh)

# Equivalence point - known for strong acid/strong base at equal concentrations
eq_volume = 25.0
eq_ph = 7.0

# Cap derivative for display (spike is extremely tall at equivalence)
dph_dv_display = np.clip(dph_dv, 0, 5.0)

# Build chart data
curve_data = [[round(float(v), 3), round(float(p), 4)] for v, p in zip(volume_naoh, ph_values, strict=True)]
deriv_data = [[round(float(v), 3), round(float(d), 4)] for v, d in zip(volume_naoh, dph_dv_display, strict=True)]

# Chart layout
chart_width = 4800
chart_height = 2700

chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": chart_width,
    "height": chart_height,
    "backgroundColor": "#fafbfc",
    "plotBackgroundColor": "#ffffff",
    "plotBorderWidth": 0,
    "marginTop": 160,
    "marginBottom": 160,
    "marginLeft": 280,
    "marginRight": 280,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "titration-curve \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "700", "color": "#1a1a2e", "letterSpacing": "0.5px"},
    "y": 55,
}

chart.options.subtitle = {
    "text": "25 mL of 0.1 M HCl Titrated with 0.1 M NaOH",
    "style": {"fontSize": "32px", "color": "#555555", "fontStyle": "italic"},
    "y": 110,
}

chart.options.credits = {"enabled": False}

chart.options.x_axis = {
    "title": {
        "text": "Volume of NaOH Added (mL)",
        "style": {"fontSize": "34px", "fontWeight": "600", "color": "#333333"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "26px", "color": "#555555"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "lineWidth": 1,
    "lineColor": "rgba(0, 0, 0, 0.2)",
    "tickWidth": 0,
    "min": 0,
    "max": 50,
    "tickInterval": 5,
    "plotLines": [
        {
            "value": float(eq_volume),
            "color": "#c0392b",
            "width": 4,
            "dashStyle": "LongDash",
            "zIndex": 4,
            "label": {
                "text": f"Equivalence Point ({eq_volume:.0f} mL, pH {eq_ph:.0f})",
                "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#c0392b", "textOutline": "4px #ffffff"},
                "rotation": 0,
                "align": "left",
                "x": 16,
                "y": 60,
            },
        }
    ],
    "plotBands": [
        {
            "from": 0,
            "to": 20,
            "color": "rgba(46, 204, 113, 0.10)",
            "label": {
                "text": "Buffer Region",
                "style": {"fontSize": "22px", "color": "rgba(39, 174, 96, 0.7)", "fontWeight": "600"},
                "align": "center",
                "verticalAlign": "bottom",
                "y": -20,
            },
        },
        {
            "from": 30,
            "to": 50,
            "color": "rgba(46, 204, 113, 0.10)",
            "label": {
                "text": "Buffer Region",
                "style": {"fontSize": "22px", "color": "rgba(39, 174, 96, 0.7)", "fontWeight": "600"},
                "align": "center",
                "verticalAlign": "bottom",
                "y": -20,
            },
        },
    ],
}

chart.options.y_axis = [
    {
        "id": "y-ph",
        "title": {"text": "pH", "style": {"fontSize": "34px", "fontWeight": "600", "color": "#306998"}},
        "labels": {"style": {"fontSize": "26px", "color": "#555555"}},
        "min": 0,
        "max": 14,
        "endOnTick": False,
        "tickInterval": 2,
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.06)",
        "lineWidth": 2,
        "lineColor": "#333333",
        "plotLines": [{"value": 7, "color": "rgba(0, 0, 0, 0.15)", "width": 2, "dashStyle": "Dot", "zIndex": 2}],
    },
    {
        "id": "y-deriv",
        "title": {"text": "dpH/dV", "style": {"fontSize": "34px", "fontWeight": "600", "color": "#e67e22"}},
        "labels": {"style": {"fontSize": "26px", "color": "#e67e22"}},
        "opposite": True,
        "gridLineWidth": 0,
        "lineWidth": 2,
        "lineColor": "#e67e22",
        "min": 0,
        "max": 5,
        "endOnTick": False,
    },
]

chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"lineWidthPlus": 1}}},
    "area": {"lineWidth": 3, "marker": {"enabled": False}, "states": {"hover": {"lineWidthPlus": 1}}},
    "scatter": {"marker": {"radius": 16}},
    "series": {"animation": False},
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px", "fontWeight": "normal"},
    "align": "left",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": 80,
    "y": 150,
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
    "shared": True,
    "headerFormat": '<span style="font-size: 22px; color: #666;">V = {point.x:.1f} mL</span><br/>',
    "pointFormat": '<span style="color:{series.color};">\u25cf</span> {series.name}: <b>{point.y:.2f}</b><br/>',
}

# pH curve series
ph_series = LineSeries()
ph_series.data = curve_data
ph_series.name = "pH"
ph_series.color = "#306998"
ph_series.y_axis = 0
ph_series.z_index = 5
chart.add_series(ph_series)

# Derivative series on secondary axis
deriv_series = AreaSeries()
deriv_series.data = deriv_data
deriv_series.name = "dpH/dV"
deriv_series.color = "#e67e22"
deriv_series.fill_opacity = 0.12
deriv_series.line_width = 3
deriv_series.y_axis = 1
deriv_series.z_index = 3
chart.add_series(deriv_series)

# Equivalence point marker
eq_marker = ScatterSeries()
eq_marker.data = [[round(float(eq_volume), 3), round(float(eq_ph), 4)]]
eq_marker.name = f"Equivalence ({eq_volume:.1f} mL)"
eq_marker.color = "#c0392b"
eq_marker.marker = {"symbol": "diamond", "radius": 20, "fillColor": "#c0392b", "lineWidth": 4, "lineColor": "#ffffff"}
eq_marker.y_axis = 0
eq_marker.z_index = 7
chart.add_series(eq_marker)

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
