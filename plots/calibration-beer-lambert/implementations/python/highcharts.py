""" anyplot.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: highcharts unknown | Python 3.13.13
Quality: 91/100 | Updated: 2026-06-03
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries, LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from PIL import Image
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette
BRAND = "#009E73"  # Imprint position 1 — first categorical series
UNKNOWN_COLOR = "#AE3030"  # Imprint matte red — semantic anchor for unknown/special point
# Theme-adaptive prediction band opacity (dark mode needs higher alpha to remain visible)
BAND_OPACITY = 0.15 if THEME == "light" else 0.22

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
conc_fit = np.linspace(0, 15, 200)
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
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "spacingTop": 40,
    "spacingBottom": 60,
    "spacingLeft": 40,
    "spacingRight": 120,
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "calibration-beer-lambert · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "600", "color": INK},
    "margin": 30,
}

chart.options.subtitle = {
    "text": "UV-Vis Spectrophotometric Calibration Standards",
    "style": {"fontSize": "44px", "fontWeight": "400", "color": INK_SOFT},
}

chart.options.x_axis = {
    "title": {
        "text": "Concentration (mg/L)",
        "style": {"fontSize": "56px", "fontWeight": "600", "color": INK},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 0,
    "max": 15,
    "tickInterval": 2,
    "gridLineWidth": 0,
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickWidth": 0,
    "plotLines": [
        {"value": float(unknown_concentration), "color": UNKNOWN_COLOR, "width": 3, "dashStyle": "Dash", "zIndex": 2}
    ],
}

chart.options.y_axis = {
    "title": {"text": "Absorbance", "style": {"fontSize": "56px", "fontWeight": "600", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": -0.02,
    "max": 0.65,
    "startOnTick": False,
    "endOnTick": False,
    "tickInterval": 0.1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "gridLineWidth": 1,
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "plotLines": [
        {"value": float(unknown_absorbance), "color": UNKNOWN_COLOR, "width": 3, "dashStyle": "Dash", "zIndex": 2}
    ],
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -80,
    "y": 120,
    "floating": True,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 6,
    "itemStyle": {"fontSize": "44px", "fontWeight": "normal", "color": INK_SOFT},
    "symbolRadius": 6,
    "itemMarginBottom": 8,
    "padding": 16,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "enabled": True,
    "headerFormat": "",
    "pointFormat": "<b>{series.name}</b><br/>Concentration: {point.x:.1f} mg/L<br/>Absorbance: {point.y:.4f}",
    "borderRadius": 8,
    "backgroundColor": ELEVATED_BG,
    "style": {"color": INK, "fontSize": "36px"},
}

chart.options.plot_options = {"series": {"animation": False, "states": {"hover": {"lineWidthPlus": 0}}}}

# Prediction interval band — light Imprint green fill, no border line
band_data = [[float(conc_fit[i]), float(lower_band[i]), float(upper_band[i])] for i in range(len(conc_fit))]

band_series = AreaRangeSeries()
band_series.data = band_data
band_series.name = "95% Prediction Interval"
band_series.color = f"rgba(0,158,115,{BAND_OPACITY})"
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
fit_series.color = BRAND
fit_series.line_width = 5
fit_series.marker = {"enabled": False}
fit_series.enable_mouse_tracking = False
fit_series.z_index = 1
fit_series.show_in_legend = True
chart.add_series(fit_series)

# Calibration standards scatter
standards_data = [[float(c), float(a)] for c, a in zip(concentration, absorbance, strict=True)]
standards_series = ScatterSeries()
standards_series.data = standards_data
standards_series.name = "Calibration Standards"
standards_series.color = BRAND
standards_series.marker = {"radius": 14, "symbol": "circle", "lineColor": PAGE_BG, "lineWidth": 3, "fillColor": BRAND}
standards_series.data_labels = {"enabled": False}
standards_series.z_index = 3
standards_series.show_in_legend = True
chart.add_series(standards_series)

# Unknown sample point
unknown_series = ScatterSeries()
unknown_series.data = [[float(unknown_concentration), float(unknown_absorbance)]]
unknown_series.name = "Unknown Sample"
unknown_series.color = UNKNOWN_COLOR
unknown_series.marker = {
    "radius": 16,
    "symbol": "triangle",
    "lineColor": PAGE_BG,
    "lineWidth": 3,
    "fillColor": UNKNOWN_COLOR,
}
unknown_series.data_labels = {"enabled": False}
unknown_series.z_index = 4
unknown_series.show_in_legend = True
chart.add_series(unknown_series)

# Regression equation and unknown label annotations
sign = "+" if intercept >= 0 else "-"
eq_text = f"y = {slope:.4f}x {sign} {abs(intercept):.4f}"
r2_text = f"R² = {r_squared:.5f}"

chart.options.annotations = [
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": ELEVATED_BG,
            "borderColor": BRAND,
            "borderWidth": 2,
            "borderRadius": 6,
            "style": {"fontSize": "40px", "color": BRAND, "fontWeight": "bold"},
            "padding": 20,
        },
        "labels": [{"point": {"x": 2.5, "y": 0.52, "xAxis": 0, "yAxis": 0}, "text": f"{eq_text}<br>{r2_text}"}],
    },
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": ELEVATED_BG,
            "borderColor": UNKNOWN_COLOR,
            "borderWidth": 2,
            "borderRadius": 6,
            "style": {"fontSize": "36px", "color": UNKNOWN_COLOR, "fontWeight": "600"},
            "padding": 16,
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

# Build HTML with inline JS (headless Chrome cannot load external CDN from file://)
html_str = chart.to_js_literal()

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
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with headless Chrome — CDP override is authoritative for viewport
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

# PIL safety net — pins to exact 3200×1800 if CDP rounding left ±1-2 px
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
