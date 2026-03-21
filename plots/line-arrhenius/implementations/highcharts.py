""" pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: highcharts unknown | Python 3.14.3
Quality: 87/100 | Created: 2026-03-21
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.annotations import Annotation
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - First-order decomposition reaction rate constants at various temperatures
R_gas = 8.314  # Gas constant J/(mol·K)
Ea_true = 75000  # Activation energy in J/mol (75 kJ/mol)
A_prefactor = 1e13  # Pre-exponential factor (s⁻¹)

np.random.seed(42)
temperature_K = np.array([300, 325, 350, 375, 400, 425, 450, 475, 500, 550, 600])
inv_T = 1.0 / temperature_K
ln_k_true = np.log(A_prefactor) - Ea_true / (R_gas * temperature_K)
ln_k = ln_k_true + np.random.normal(0, 0.15, len(temperature_K))

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(inv_T, ln_k)
r_squared = r_value**2
Ea_fitted = -slope * R_gas / 1000  # kJ/mol

# Regression line points
inv_T_fit = np.linspace(inv_T.min() * 0.97, inv_T.max() * 1.03, 100)
ln_k_fit = slope * inv_T_fit + intercept

# Scale 1/T by 1000 for readability (units: 10⁻³ K⁻¹)
inv_T_scaled = inv_T * 1000
inv_T_fit_scaled = inv_T_fit * 1000

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingTop": 60,
    "spacingBottom": 60,
    "marginBottom": 160,
    "spacingLeft": 100,
    "spacingRight": 100,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "line-arrhenius \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "600", "color": "#1a1a2e"},
    "margin": 50,
}

# Temperature reference marks as plotLines on x-axis
ref_temps = [300, 350, 400, 450, 500, 600]
plot_lines = []
for t in ref_temps:
    plot_lines.append(
        {
            "value": 1000.0 / t,
            "color": "rgba(0,0,0,0.12)",
            "width": 1,
            "dashStyle": "Dot",
            "label": {"text": f"{t} K", "style": {"fontSize": "22px", "color": "#888888"}, "rotation": 0, "y": -10},
        }
    )

chart.options.x_axis = {
    "title": {
        "text": "1000 / T  (K\u207b\u00b9)",
        "style": {"fontSize": "36px", "fontWeight": "600", "color": "#333333"},
        "margin": 24,
    },
    "labels": {"style": {"fontSize": "26px", "color": "#444444"}, "step": 2},
    "reversed": True,
    "tickInterval": 0.2,
    "lineColor": "#666666",
    "lineWidth": 2,
    "tickLength": 0,
    "gridLineWidth": 0,
    "plotLines": plot_lines,
}

chart.options.y_axis = {
    "title": {"text": "ln(k)", "style": {"fontSize": "36px", "fontWeight": "600", "color": "#333333"}, "margin": 24},
    "labels": {"style": {"fontSize": "26px", "color": "#444444"}},
    "lineColor": "#666666",
    "lineWidth": 2,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.08)",
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 80,
    "itemStyle": {"fontSize": "28px", "fontWeight": "500", "color": "#333333"},
    "backgroundColor": "rgba(255,255,255,0.85)",
    "borderColor": "#cccccc",
    "borderWidth": 1,
    "borderRadius": 6,
    "padding": 14,
    "symbolRadius": 6,
}
chart.options.credits = {"enabled": False}

chart.options.plot_options = {
    "scatter": {"marker": {"radius": 14, "lineWidth": 3, "lineColor": "#ffffff"}},
    "spline": {"marker": {"enabled": False}, "lineWidth": 4},
}

# Regression line series
fit_data = [[round(float(x), 4), round(float(y), 3)] for x, y in zip(inv_T_fit_scaled, ln_k_fit, strict=False)]
regression_series = SplineSeries()
regression_series.data = fit_data
regression_series.name = "Linear Fit"
regression_series.color = "#c0392b"
regression_series.line_width = 4
regression_series.dash_style = "Dash"
chart.add_series(regression_series)

# Data points series (on top of regression line)
scatter_data = [[round(float(x), 4), round(float(y), 3)] for x, y in zip(inv_T_scaled, ln_k, strict=False)]
data_series = ScatterSeries()
data_series.data = scatter_data
data_series.name = "Experimental Data"
data_series.color = "#306998"
data_series.z_index = 5
chart.add_series(data_series)

# Annotations for R², Ea, and slope - positioned near the data midpoint
anno_x = round(float(inv_T_scaled[3]), 4)  # Near 375K data point region
y_mid = float(slope * inv_T[3] + intercept)  # On regression line at that x

chart.options.annotations = [
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {"allowOverlap": True, "overflow": "none", "crop": False},
            "labels": [
                {
                    "point": {"xAxis": 0, "yAxis": 0, "x": anno_x, "y": round(y_mid + 2.5, 2)},
                    "text": f"R\u00b2 = {r_squared:.4f}",
                    "style": {"fontSize": "34px", "fontWeight": "700", "color": "#c0392b"},
                    "backgroundColor": "rgba(255,255,255,0.92)",
                    "borderColor": "#c0392b",
                    "borderWidth": 2,
                    "borderRadius": 8,
                    "padding": 16,
                },
                {
                    "point": {"xAxis": 0, "yAxis": 0, "x": anno_x, "y": round(y_mid + 1.2, 2)},
                    "text": f"E\u2090 = {Ea_fitted:.1f} kJ/mol",
                    "style": {"fontSize": "34px", "fontWeight": "700", "color": "#d35400"},
                    "backgroundColor": "rgba(255,255,255,0.92)",
                    "borderColor": "#d35400",
                    "borderWidth": 2,
                    "borderRadius": 8,
                    "padding": 16,
                },
                {
                    "point": {"xAxis": 0, "yAxis": 0, "x": anno_x, "y": round(y_mid - 0.1, 2)},
                    "text": f"Slope = \u2212E\u2090/R = {slope:.0f} K",
                    "style": {"fontSize": "30px", "fontWeight": "600", "color": "#555555"},
                    "backgroundColor": "rgba(255,255,255,0.92)",
                    "borderColor": "#888888",
                    "borderWidth": 1,
                    "borderRadius": 8,
                    "padding": 14,
                },
            ],
        }
    )
]

# Download Highcharts JS and annotations module
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
hc_req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(hc_req, timeout=30) as resp:
    highcharts_js = resp.read().decode("utf-8")

annotations_url = "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js"
ann_req = urllib.request.Request(annotations_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(ann_req, timeout=30) as resp:
    annotations_module_js = resp.read().decode("utf-8")

# Generate JS and build HTML
html_str = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_module_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
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
