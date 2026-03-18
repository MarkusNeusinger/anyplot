"""pyplots.ai
curve-dose-response: Pharmacological Dose-Response Curve
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-03-18
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Synthetic dose-response for 2 compounds
np.random.seed(42)

concentrations = np.array([1e-9, 3e-9, 1e-8, 3e-8, 1e-7, 3e-7, 1e-6, 3e-6, 1e-5, 3e-5, 1e-4])
log_conc = np.log10(concentrations)


# 4PL model: response = Bottom + (Top - Bottom) / (1 + 10^((logEC50 - logC) * Hill))
def four_pl(log_c, bottom, top, log_ec50, hill):
    return bottom + (top - bottom) / (1 + 10 ** ((log_ec50 - log_c) * hill))


# Compound A: potent agonist (EC50 ~ 100 nM)
true_params_a = [5, 95, np.log10(1e-7), 1.2]
response_a_mean = four_pl(log_conc, *true_params_a)
response_a = np.clip(response_a_mean + np.random.normal(0, 3, len(concentrations)), 0, 100)
sem_a = np.random.uniform(2, 5, len(concentrations))

# Compound B: less potent agonist (EC50 ~ 3 uM)
true_params_b = [8, 85, np.log10(3e-6), 0.9]
response_b_mean = four_pl(log_conc, *true_params_b)
response_b = np.clip(response_b_mean + np.random.normal(0, 3.5, len(concentrations)), 0, 100)
sem_b = np.random.uniform(2.5, 6, len(concentrations))

# Fit 4PL curves
popt_a, pcov_a = curve_fit(four_pl, log_conc, response_a, p0=[0, 100, -7, 1], maxfev=10000)
popt_b, pcov_b = curve_fit(four_pl, log_conc, response_b, p0=[0, 100, -5.5, 1], maxfev=10000)

# Generate smooth fitted curves
log_conc_smooth = np.linspace(np.log10(5e-10), np.log10(2e-4), 200)
fit_a = four_pl(log_conc_smooth, *popt_a)
fit_b = four_pl(log_conc_smooth, *popt_b)

# 95% CI for Compound A via bootstrap from parameter covariance
boot_curves_a = np.array([four_pl(log_conc_smooth, *np.random.multivariate_normal(popt_a, pcov_a)) for _ in range(200)])
ci_lower_a = np.percentile(boot_curves_a, 2.5, axis=0)
ci_upper_a = np.percentile(boot_curves_a, 97.5, axis=0)

# Extract EC50 values and half-maximal responses
ec50_a = 10 ** popt_a[2]
ec50_b = 10 ** popt_b[2]
half_response_a = popt_a[0] + (popt_a[1] - popt_a[0]) / 2
half_response_b = popt_b[0] + (popt_b[1] - popt_b[0]) / 2

# Prepare series data as JSON
ci_band_data = [
    [float(x), float(lo), float(hi)] for x, lo, hi in zip(log_conc_smooth, ci_lower_a, ci_upper_a, strict=False)
]
fit_a_data = [[float(x), float(y)] for x, y in zip(log_conc_smooth, fit_a, strict=False)]
fit_b_data = [[float(x), float(y)] for x, y in zip(log_conc_smooth, fit_b, strict=False)]
scatter_a_data = [[float(lc), float(r)] for lc, r in zip(log_conc, response_a, strict=False)]
scatter_b_data = [[float(lc), float(r)] for lc, r in zip(log_conc, response_b, strict=False)]

# Error bar data for Compound A (scatter with low/high)
errorbar_a_data = [
    [float(lc), float(r - s), float(r + s)] for lc, r, s in zip(log_conc, response_a, sem_a, strict=False)
]
errorbar_b_data = [
    [float(lc), float(r - s), float(r + s)] for lc, r, s in zip(log_conc, response_b, sem_b, strict=False)
]

# Build Highcharts config as dict (bypass Python library validation issues)
config = {
    "chart": {
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "spacingTop": 80,
        "spacingBottom": 100,
        "spacingLeft": 40,
        "spacingRight": 40,
    },
    "title": {
        "text": "curve-dose-response \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "52px", "fontWeight": "bold"},
    },
    "subtitle": {
        "text": f"EC\u2085\u2080: Compound A = {ec50_a:.1e} M  |  Compound B = {ec50_b:.1e} M",
        "style": {"fontSize": "34px", "color": "#666666"},
    },
    "xAxis": {
        "title": {
            "text": "Concentration (M, log\u2081\u2080 scale)",
            "style": {"fontSize": "36px", "fontWeight": "bold"},
            "margin": 20,
        },
        "labels": {"style": {"fontSize": "28px"}},
        "min": float(np.log10(5e-10)),
        "max": float(np.log10(2e-4)),
        "tickInterval": 1,
        "gridLineWidth": 1,
        "gridLineColor": "#f0f0f0",
        "plotLines": [
            {
                "value": float(popt_a[2]),
                "color": "#306998",
                "width": 3,
                "dashStyle": "Dash",
                "zIndex": 3,
                "label": {
                    "text": "EC\u2085\u2080 A",
                    "style": {"fontSize": "24px", "color": "#306998", "fontWeight": "bold"},
                    "rotation": 90,
                    "y": 30,
                },
            },
            {
                "value": float(popt_b[2]),
                "color": "#E85D75",
                "width": 3,
                "dashStyle": "Dash",
                "zIndex": 3,
                "label": {
                    "text": "EC\u2085\u2080 B",
                    "style": {"fontSize": "24px", "color": "#E85D75", "fontWeight": "bold"},
                    "rotation": 90,
                    "y": 30,
                },
            },
        ],
    },
    "yAxis": {
        "title": {"text": "Response (%)", "style": {"fontSize": "36px", "fontWeight": "bold"}, "margin": 20},
        "labels": {"style": {"fontSize": "28px"}},
        "min": 0,
        "max": 105,
        "gridLineWidth": 1,
        "gridLineColor": "#f0f0f0",
        "plotLines": [
            {"value": float(half_response_a), "color": "#306998", "width": 2, "dashStyle": "Dot", "zIndex": 2},
            {"value": float(half_response_b), "color": "#E85D75", "width": 2, "dashStyle": "Dot", "zIndex": 2},
            {"value": float(popt_a[1]), "color": "#306998", "width": 1, "dashStyle": "LongDash", "zIndex": 1},
            {"value": float(popt_a[0]), "color": "#306998", "width": 1, "dashStyle": "LongDash", "zIndex": 1},
        ],
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "x": -20,
        "y": 100,
        "itemStyle": {"fontSize": "26px", "fontWeight": "normal"},
        "symbolWidth": 40,
        "symbolHeight": 16,
        "itemMarginBottom": 12,
        "backgroundColor": "rgba(255,255,255,0.9)",
        "borderWidth": 1,
        "borderColor": "#e0e0e0",
        "padding": 16,
    },
    "tooltip": {"style": {"fontSize": "22px"}},
    "plotOptions": {
        "spline": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"lineWidth": 6}}},
        "scatter": {"marker": {"radius": 12, "lineWidth": 2, "lineColor": "#ffffff"}},
        "arearange": {"lineWidth": 0, "marker": {"enabled": False}, "enableMouseTracking": False},
        "errorbar": {"lineWidth": 3, "color": "inherit"},
    },
    "credits": {"enabled": False},
    "series": [
        {
            "type": "arearange",
            "name": "95% CI (Compound A)",
            "data": ci_band_data,
            "color": "rgba(48, 105, 152, 0.18)",
            "fillOpacity": 0.18,
            "zIndex": 0,
        },
        {
            "type": "spline",
            "name": "Compound A (fit)",
            "data": fit_a_data,
            "color": "#306998",
            "lineWidth": 5,
            "zIndex": 2,
        },
        {
            "type": "spline",
            "name": "Compound B (fit)",
            "data": fit_b_data,
            "color": "#E85D75",
            "lineWidth": 5,
            "zIndex": 2,
        },
        {
            "type": "scatter",
            "name": "Compound A (data)",
            "data": scatter_a_data,
            "color": "#306998",
            "marker": {"symbol": "circle", "radius": 12, "lineWidth": 2, "lineColor": "#ffffff"},
            "zIndex": 3,
        },
        {
            "type": "errorbar",
            "name": "SEM (Compound A)",
            "data": errorbar_a_data,
            "color": "#306998",
            "linkedTo": ":previous",
            "showInLegend": False,
            "zIndex": 1,
        },
        {
            "type": "scatter",
            "name": "Compound B (data)",
            "data": scatter_b_data,
            "color": "#E85D75",
            "marker": {"symbol": "circle", "radius": 12, "lineWidth": 2, "lineColor": "#ffffff"},
            "zIndex": 3,
        },
        {
            "type": "errorbar",
            "name": "SEM (Compound B)",
            "data": errorbar_b_data,
            "color": "#E85D75",
            "linkedTo": ":previous",
            "showInLegend": False,
            "zIndex": 1,
        },
    ],
}

config_json = json.dumps(config)

# X-axis formatter for scientific notation (injected as raw JS)
x_formatter = """function() {
    var exp = Math.round(this.value);
    var supers = '\\u2070\\u00b9\\u00b2\\u00b3\\u2074\\u2075\\u2076\\u2077\\u2078\\u2079';
    var s = '10\\u207b';
    var abs_exp = Math.abs(exp);
    if (abs_exp >= 10) { s += supers.charAt(Math.floor(abs_exp / 10)); }
    s += supers.charAt(abs_exp % 10);
    return s;
}"""

# Download Highcharts JS and highcharts-more (for arearange/errorbar)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
hc_req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(hc_req, timeout=30) as resp:
    highcharts_js = resp.read().decode("utf-8")

highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js"
hcm_req = urllib.request.Request(highcharts_more_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(hcm_req, timeout=30) as resp:
    highcharts_more_js = resp.read().decode("utf-8")

# Build HTML with inline JS config
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        var config = {config_json};
        config.xAxis.labels.formatter = {x_formatter};
        Highcharts.chart('container', config);
    }});
    </script>
</body>
</html>"""

# Save HTML for interactive viewing
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
