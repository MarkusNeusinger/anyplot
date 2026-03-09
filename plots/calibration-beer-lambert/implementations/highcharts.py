""" pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: highcharts unknown | Python 3.14.3
Quality: 89/100 | Created: 2026-03-09
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries, LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - calibration standards for UV-Vis spectrophotometry
np.random.seed(42)
concentration = np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0])
epsilon_l = 0.045
absorbance_true = epsilon_l * concentration
absorbance = absorbance_true + np.random.normal(0, 0.008, len(concentration))
absorbance[0] = 0.005

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(concentration, absorbance)
r_squared = r_value**2

# Regression line and prediction interval
conc_fit = np.linspace(-0.5, 15.5, 200)
abs_fit = slope * conc_fit + intercept
n = len(concentration)
mean_conc = np.mean(concentration)
ss_conc = np.sum((concentration - mean_conc) ** 2)
residuals = absorbance - (slope * concentration + intercept)
mse = np.sum(residuals**2) / (n - 2)
se_pred = np.sqrt(mse * (1 + 1 / n + (conc_fit - mean_conc) ** 2 / ss_conc))
t_val = stats.t.ppf(0.975, n - 2)
upper_band = abs_fit + t_val * se_pred
lower_band = abs_fit - t_val * se_pred

# Unknown sample
unknown_absorbance = 0.38
unknown_concentration = (unknown_absorbance - intercept) / slope

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingTop": 60,
    "spacingBottom": 80,
    "spacingLeft": 60,
    "spacingRight": 60,
    "style": {"fontFamily": "Arial, Helvetica, sans-serif"},
}

chart.options.title = {
    "text": "calibration-beer-lambert \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "52px", "fontWeight": "500", "color": "#333333"},
    "margin": 50,
}

chart.options.x_axis = {
    "title": {"text": "Concentration (mg/L)", "style": {"fontSize": "36px", "color": "#444444"}, "margin": 30},
    "labels": {"style": {"fontSize": "28px", "color": "#666666"}},
    "min": 0,
    "max": 15,
    "tickInterval": 2,
    "gridLineWidth": 0,
    "lineColor": "#cccccc",
    "lineWidth": 2,
    "tickWidth": 0,
    "plotLines": [
        {"value": float(unknown_concentration), "color": "#c0392b", "width": 4, "dashStyle": "Dash", "zIndex": 2}
    ],
}

chart.options.y_axis = {
    "title": {"text": "Absorbance", "style": {"fontSize": "36px", "color": "#444444"}, "margin": 30},
    "labels": {"style": {"fontSize": "28px", "color": "#666666"}},
    "min": -0.05,
    "max": 0.75,
    "tickInterval": 0.1,
    "gridLineColor": "#eeeeee",
    "gridLineWidth": 1,
    "lineColor": "#cccccc",
    "lineWidth": 2,
    "plotLines": [
        {"value": float(unknown_absorbance), "color": "#c0392b", "width": 4, "dashStyle": "Dash", "zIndex": 2}
    ],
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -40,
    "y": 80,
    "floating": True,
    "backgroundColor": "rgba(255,255,255,0.85)",
    "borderColor": "#cccccc",
    "borderWidth": 1,
    "borderRadius": 6,
    "itemStyle": {"fontSize": "28px", "fontWeight": "normal", "color": "#444444"},
    "symbolRadius": 6,
    "itemMarginBottom": 8,
}

chart.options.credits = {"enabled": False}

# Prediction interval band (arearange)
band_data = [[float(conc_fit[i]), float(lower_band[i]), float(upper_band[i])] for i in range(len(conc_fit))]

band_series = AreaRangeSeries()
band_series.data = band_data
band_series.name = "95% Prediction Interval"
band_series.color = "rgba(48, 105, 152, 0.15)"
band_series.fill_opacity = 1.0
band_series.line_width = 0
band_series.marker = {"enabled": False}
band_series.enable_mouse_tracking = False
band_series.z_index = 0
band_series.show_in_legend = True
chart.add_series(band_series)

# Regression line
fit_line_data = [[float(conc_fit[i]), float(abs_fit[i])] for i in range(len(conc_fit))]
fit_series = LineSeries()
fit_series.data = fit_line_data
fit_series.name = "Linear Fit"
fit_series.color = "#306998"
fit_series.line_width = 5
fit_series.marker = {"enabled": False}
fit_series.enable_mouse_tracking = False
fit_series.z_index = 1
fit_series.show_in_legend = True
chart.add_series(fit_series)

# Calibration standards
standards_data = [[float(c), float(a)] for c, a in zip(concentration, absorbance, strict=True)]
standards_series = ScatterSeries()
standards_series.data = standards_data
standards_series.name = "Standards"
standards_series.color = "#306998"
standards_series.marker = {
    "radius": 16,
    "symbol": "circle",
    "lineColor": "#ffffff",
    "lineWidth": 4,
    "fillColor": "#306998",
}
standards_series.data_labels = {"enabled": False}
standards_series.z_index = 3
standards_series.show_in_legend = True
chart.add_series(standards_series)

# Unknown sample point
unknown_series = ScatterSeries()
unknown_series.data = [[float(unknown_concentration), float(unknown_absorbance)]]
unknown_series.name = "Unknown Sample"
unknown_series.color = "#c0392b"
unknown_series.marker = {
    "radius": 18,
    "symbol": "diamond",
    "lineColor": "#ffffff",
    "lineWidth": 4,
    "fillColor": "#c0392b",
}
unknown_series.data_labels = {"enabled": False}
unknown_series.z_index = 4
unknown_series.show_in_legend = True
chart.add_series(unknown_series)

# Annotations - equation text and unknown label
sign = "+" if intercept >= 0 else "-"
eq_text = f"y = {slope:.4f}x {sign} {abs(intercept):.4f}"
r2_text = f"R\u00b2 = {r_squared:.5f}"

chart.options.annotations = [
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": "rgba(255,255,255,0.90)",
            "borderColor": "#306998",
            "borderWidth": 3,
            "borderRadius": 8,
            "style": {"fontSize": "36px", "color": "#306998", "fontWeight": "bold"},
            "padding": 24,
        },
        "labels": [{"point": {"x": 2.5, "y": 0.62, "xAxis": 0, "yAxis": 0}, "text": f"{eq_text}<br>{r2_text}"}],
    },
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": "rgba(255,255,255,0.90)",
            "borderColor": "#c0392b",
            "borderWidth": 3,
            "borderRadius": 8,
            "style": {"fontSize": "30px", "color": "#c0392b", "fontWeight": "600"},
            "padding": 18,
        },
        "labels": [
            {
                "point": {
                    "x": float(unknown_concentration) + 1.2,
                    "y": float(unknown_absorbance) + 0.08,
                    "xAxis": 0,
                    "yAxis": 0,
                },
                "text": f"Unknown: {unknown_concentration:.1f} mg/L",
            }
        ],
    },
]

# Save HTML
html_str = chart.to_js_literal()

# Download Highcharts JS and modules
js_urls = {
    "highcharts": "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js",
    "highcharts_more": "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js",
    "annotations": "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js",
}
js_scripts = {}
for name, url in js_urls.items():
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        js_scripts[name] = response.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_scripts["highcharts"]}</script>
    <script>{js_scripts["highcharts_more"]}</script>
    <script>{js_scripts["annotations"]}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

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
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
