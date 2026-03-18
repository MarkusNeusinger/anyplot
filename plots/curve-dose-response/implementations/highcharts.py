""" pyplots.ai
curve-dose-response: Pharmacological Dose-Response Curve
Library: highcharts unknown | Python 3.14.3
Quality: 89/100 | Created: 2026-03-18
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries
from highcharts_core.options.series.boxplot import ErrorBarSeries
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
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

# Pre-format x-axis tick labels as Unicode superscript strings
superscript_map = str.maketrans("-0123456789", "\u207b\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079")
x_tick_values = list(range(-9, -3))
x_tick_categories = {v: f"10{str(v).translate(superscript_map)}" for v in x_tick_values}

# Create chart using highcharts-core API
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "borderWidth": 0,
    "spacingTop": 80,
    "spacingBottom": 100,
    "spacingLeft": 80,
    "spacingRight": 60,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

# Title and subtitle
chart.options.title = {
    "text": "curve-dose-response \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "52px", "fontWeight": "700", "color": "#1a1a2e"},
}
chart.options.subtitle = {
    "text": f"EC\u2085\u2080: Compound A = {ec50_a:.1e} M  \u2502  Compound B = {ec50_b:.1e} M",
    "style": {"fontSize": "34px", "color": "#555555", "fontWeight": "400"},
}

# X-axis with plotLines for EC50 markers — horizontal labels for better readability
chart.options.x_axis = {
    "title": {
        "text": "Concentration (M, log\u2081\u2080 scale)",
        "style": {"fontSize": "36px", "fontWeight": "600", "color": "#333333"},
        "margin": 24,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#444444"}},
    "min": float(np.log10(5e-10)),
    "max": float(np.log10(2e-4)),
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "#f0f0f0",
    "lineColor": "#cccccc",
    "lineWidth": 1,
    "tickColor": "#cccccc",
    "plotLines": [
        {
            "value": float(popt_a[2]),
            "color": "#306998",
            "width": 3,
            "dashStyle": "Dash",
            "zIndex": 3,
            "label": {
                "text": f"EC\u2085\u2080 A = {ec50_a:.1e} M",
                "style": {"fontSize": "26px", "color": "#306998", "fontWeight": "bold"},
                "rotation": 0,
                "align": "left",
                "x": 8,
                "y": 200,
            },
        },
        {
            "value": float(popt_b[2]),
            "color": "#D4526E",
            "width": 3,
            "dashStyle": "Dash",
            "zIndex": 3,
            "label": {
                "text": f"EC\u2085\u2080 B = {ec50_b:.1e} M",
                "style": {"fontSize": "26px", "color": "#D4526E", "fontWeight": "bold"},
                "rotation": 0,
                "align": "left",
                "x": 8,
                "y": 200,
            },
        },
    ],
}

# Y-axis with half-maximal and asymptote plotLines — tighter max, better label positioning
chart.options.y_axis = {
    "title": {
        "text": "Response (%)",
        "style": {"fontSize": "36px", "fontWeight": "600", "color": "#333333"},
        "margin": 24,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#444444"}},
    "min": -2,
    "max": 102,
    "gridLineWidth": 1,
    "gridLineColor": "#f0f0f0",
    "lineColor": "#cccccc",
    "lineWidth": 1,
    "plotLines": [
        {"value": float(half_response_a), "color": "#306998", "width": 2, "dashStyle": "Dot", "zIndex": 2},
        {"value": float(half_response_b), "color": "#D4526E", "width": 2, "dashStyle": "Dot", "zIndex": 2},
        {
            "value": float(popt_a[1]),
            "color": "rgba(48, 105, 152, 0.55)",
            "width": 3,
            "dashStyle": "LongDash",
            "zIndex": 1,
            "label": {
                "text": f"Top asymptote ({popt_a[1]:.0f}%)",
                "align": "left",
                "style": {"fontSize": "24px", "color": "rgba(48, 105, 152, 0.7)"},
                "x": 10,
                "y": -8,
            },
        },
        {
            "value": float(popt_a[0]),
            "color": "rgba(48, 105, 152, 0.55)",
            "width": 3,
            "dashStyle": "LongDash",
            "zIndex": 1,
            "label": {
                "text": f"Bottom asymptote ({popt_a[0]:.0f}%)",
                "align": "left",
                "style": {"fontSize": "24px", "color": "rgba(48, 105, 152, 0.7)"},
                "x": 10,
                "y": -12,
            },
        },
    ],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "floating": True,
    "x": -30,
    "y": 80,
    "itemStyle": {"fontSize": "26px", "fontWeight": "normal", "color": "#333333"},
    "symbolWidth": 40,
    "symbolHeight": 16,
    "itemMarginBottom": 12,
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderWidth": 1,
    "borderColor": "#dddddd",
    "borderRadius": 6,
    "padding": 18,
    "shadow": {"enabled": True, "color": "rgba(0, 0, 0, 0.06)", "offsetX": 2, "offsetY": 2, "width": 4},
}

# Plot options
chart.options.plot_options = {
    "spline": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"lineWidth": 6}}},
    "scatter": {"marker": {"radius": 12, "lineWidth": 2, "lineColor": "#ffffff"}},
    "arearange": {"lineWidth": 0, "marker": {"enabled": False}, "enableMouseTracking": False},
    "errorbar": {"lineWidth": 3, "color": "inherit", "stemWidth": 3, "whiskerWidth": 3, "whiskerLength": "40%"},
}

chart.options.credits = {"enabled": False}
chart.options.tooltip = {"style": {"fontSize": "22px"}}

# --- Series using highcharts-core API ---

# 95% CI band for Compound A
ci_band_data = [
    [float(x), float(lo), float(hi)] for x, lo, hi in zip(log_conc_smooth, ci_lower_a, ci_upper_a, strict=False)
]
ci_series = AreaRangeSeries()
ci_series.data = ci_band_data
ci_series.name = "95% CI (Compound A)"
ci_series.color = "rgba(48, 105, 152, 0.30)"
ci_series.fill_opacity = 0.30
ci_series.z_index = 0
chart.add_series(ci_series)

# Compound A fitted curve
fit_a_data = [[float(x), float(y)] for x, y in zip(log_conc_smooth, fit_a, strict=False)]
fit_a_series = SplineSeries()
fit_a_series.data = fit_a_data
fit_a_series.name = "Compound A (4PL fit)"
fit_a_series.color = "#306998"
fit_a_series.line_width = 5
fit_a_series.z_index = 2
chart.add_series(fit_a_series)

# Compound B fitted curve
fit_b_data = [[float(x), float(y)] for x, y in zip(log_conc_smooth, fit_b, strict=False)]
fit_b_series = SplineSeries()
fit_b_series.data = fit_b_data
fit_b_series.name = "Compound B (4PL fit)"
fit_b_series.color = "#D4526E"
fit_b_series.line_width = 5
fit_b_series.z_index = 2
chart.add_series(fit_b_series)

# Compound A scatter data
scatter_a_data = [[float(lc), float(r)] for lc, r in zip(log_conc, response_a, strict=False)]
scatter_a_series = ScatterSeries()
scatter_a_series.data = scatter_a_data
scatter_a_series.name = "Compound A (data)"
scatter_a_series.color = "#306998"
scatter_a_series.marker = {"symbol": "circle", "radius": 13, "lineWidth": 3, "lineColor": "#ffffff"}
scatter_a_series.z_index = 3
chart.add_series(scatter_a_series)

# Compound A error bars
errorbar_a_data = [
    [float(lc), float(r - s), float(r + s)] for lc, r, s in zip(log_conc, response_a, sem_a, strict=False)
]
eb_a_series = ErrorBarSeries()
eb_a_series.data = errorbar_a_data
eb_a_series.name = "SEM (Compound A)"
eb_a_series.color = "#306998"
eb_a_series.linked_to = ":previous"
eb_a_series.show_in_legend = False
eb_a_series.z_index = 1
chart.add_series(eb_a_series)

# Compound B scatter data
scatter_b_data = [[float(lc), float(r)] for lc, r in zip(log_conc, response_b, strict=False)]
scatter_b_series = ScatterSeries()
scatter_b_series.data = scatter_b_data
scatter_b_series.name = "Compound B (data)"
scatter_b_series.color = "#D4526E"
scatter_b_series.marker = {"symbol": "circle", "radius": 13, "lineWidth": 3, "lineColor": "#ffffff"}
scatter_b_series.z_index = 3
chart.add_series(scatter_b_series)

# Compound B error bars
errorbar_b_data = [
    [float(lc), float(r - s), float(r + s)] for lc, r, s in zip(log_conc, response_b, sem_b, strict=False)
]
eb_b_series = ErrorBarSeries()
eb_b_series.data = errorbar_b_data
eb_b_series.name = "SEM (Compound B)"
eb_b_series.color = "#D4526E"
eb_b_series.linked_to = ":previous"
eb_b_series.show_in_legend = False
eb_b_series.z_index = 1
chart.add_series(eb_b_series)

# Generate JS literal from Chart API
html_str = chart.to_js_literal()

# Inject x-axis label formatter using Highcharts native callback approach
# Build a mapping object for tick values to superscript labels
tick_map_js = ", ".join(f"'{v}': '{label}'" for v, label in x_tick_categories.items())
formatter_js = (
    f"formatter: function() {{ var m = {{{tick_map_js}}}; return m[Math.round(this.value)] || this.value; }},"
)

# Insert formatter into xAxis labels block via targeted replacement
html_str = html_str.replace("labels: {\n  style:", "labels: {\n  " + formatter_js + "\n  style:", 1)

# Download Highcharts JS and highcharts-more (for arearange/errorbar)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
hc_req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(hc_req, timeout=30) as resp:
    highcharts_js = resp.read().decode("utf-8")

highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js"
hcm_req = urllib.request.Request(highcharts_more_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(hcm_req, timeout=30) as resp:
    highcharts_more_js = resp.read().decode("utf-8")

# Build HTML with inline scripts and Chart API-generated config
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
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
