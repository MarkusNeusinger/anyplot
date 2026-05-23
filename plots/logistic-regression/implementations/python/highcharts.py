""" anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-23
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.linear_model import LogisticRegression


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Semantic color mapping: Pass→green (good), Fail→red (bad)
COLOR_PASS = "#009E73"  # anyplot position 1 — semantic: pass/good
COLOR_FAIL = "#B71D27"  # anyplot position 3 — semantic: fail/bad
COLOR_CURVE = "#9418DB"  # anyplot position 2 — logistic curve

# Data — exam pass/fail as a function of study hours
np.random.seed(42)
n_points = 150

study_hours = np.random.uniform(0, 10, n_points)
true_prob = 1 / (1 + np.exp(-1.5 * (study_hours - 5)))
passed = (np.random.random(n_points) < true_prob).astype(int)

model = LogisticRegression()
model.fit(study_hours.reshape(-1, 1), passed)
accuracy = model.score(study_hours.reshape(-1, 1), passed)

x_curve = np.linspace(0, 10, 200)
prob_curve = model.predict_proba(x_curve.reshape(-1, 1))[:, 1]

# Bootstrap 95% confidence intervals
n_bootstrap = 100
bootstrap_probs = np.zeros((n_bootstrap, len(x_curve)))
for i in range(n_bootstrap):
    idx = np.random.choice(n_points, n_points, replace=True)
    m = LogisticRegression()
    m.fit(study_hours[idx].reshape(-1, 1), passed[idx])
    bootstrap_probs[i] = m.predict_proba(x_curve.reshape(-1, 1))[:, 1]

ci_lower = np.percentile(bootstrap_probs, 2.5, axis=0)
ci_upper = np.percentile(bootstrap_probs, 97.5, axis=0)

# Jitter y values so overlapping points are visible
y_jitter = passed + np.random.uniform(-0.03, 0.03, n_points)
x_fail = study_hours[passed == 0].tolist()
y_fail = y_jitter[passed == 0].tolist()
x_pass = study_hours[passed == 1].tolist()
y_pass = y_jitter[passed == 1].tolist()

# Chart
title = "logistic-regression · python · highcharts · anyplot.ai"
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    "spacingBottom": 80,
    "spacingLeft": 50,
    "spacingTop": 50,
    "spacingRight": 50,
}

chart.options.title = {"text": title, "style": {"fontSize": "66px", "color": INK, "fontWeight": "bold"}}

chart.options.subtitle = {
    "text": "Exam Pass Probability vs Study Hours",
    "style": {"fontSize": "44px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "title": {"text": "Study Hours", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 0,
    "max": 10,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.y_axis = {
    "title": {"text": "Probability", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": -0.05,
    "max": 1.05,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "plotLines": [
        {
            "value": 0.5,
            "color": INK_SOFT,
            "width": 3,
            "dashStyle": "Dash",
            "label": {
                "text": "Decision Threshold (p = 0.5)",
                "align": "right",
                "style": {"fontSize": "36px", "color": INK_SOFT},
                "x": -10,
                "y": -12,
            },
            "zIndex": 4,
        }
    ],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"color": INK_SOFT, "fontSize": "44px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolRadius": 6,
    "symbolHeight": 20,
    "symbolWidth": 20,
}

chart.options.plot_options = {
    "scatter": {"marker": {"radius": 8, "symbol": "circle"}},
    "spline": {"lineWidth": 6, "marker": {"enabled": False}},
    "arearange": {"fillOpacity": 0.2, "lineWidth": 0, "marker": {"enabled": False}},
}

chart.options.tooltip = {
    "useHTML": True,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "style": {"color": INK, "fontSize": "28px"},
    "formatter": """function() {
        var s = this.series.name;
        if (s === 'Logistic Curve') {
            return '<b>Logistic Curve</b><br/>Study Hours: <b>' + Highcharts.numberFormat(this.x, 2) + '</b><br/>P(Pass): <b>' + Highcharts.numberFormat(this.y * 100, 1) + '%</b>';
        } else if (s === '95% CI') {
            return '<b>95% CI Band</b><br/>Study Hours: <b>' + Highcharts.numberFormat(this.x, 2) + '</b><br/>Lower: <b>' + Highcharts.numberFormat(this.point.low * 100, 1) + '%</b><br/>Upper: <b>' + Highcharts.numberFormat(this.point.high * 100, 1) + '%</b>';
        } else {
            var outcome = s === 'Pass (1)' ? 'Pass' : 'Fail';
            return '<b>' + outcome + '</b><br/>Study Hours: <b>' + Highcharts.numberFormat(this.x, 2) + '</b>';
        }
    }""",
}

# Confidence interval band
ci_series = AreaRangeSeries()
ci_series.data = [[float(x_curve[i]), float(ci_lower[i]), float(ci_upper[i])] for i in range(len(x_curve))]
ci_series.name = "95% CI"
ci_series.color = COLOR_CURVE
ci_series.fill_opacity = 0.2
chart.add_series(ci_series)

# Logistic curve
curve_series = SplineSeries()
curve_series.data = [[float(x_curve[i]), float(prob_curve[i])] for i in range(len(x_curve))]
curve_series.name = "Logistic Curve"
curve_series.color = COLOR_CURVE
chart.add_series(curve_series)

# Fail (0) scatter points
scatter_fail = ScatterSeries()
scatter_fail.data = [[x_fail[i], y_fail[i]] for i in range(len(x_fail))]
scatter_fail.name = "Fail (0)"
scatter_fail.color = "rgba(183, 29, 39, 0.6)"  # #B71D27 at 0.6 alpha
scatter_fail.marker = {"radius": 8, "symbol": "circle"}
chart.add_series(scatter_fail)

# Pass (1) scatter points
scatter_pass = ScatterSeries()
scatter_pass.data = [[x_pass[i], y_pass[i]] for i in range(len(x_pass))]
scatter_pass.name = "Pass (1)"
scatter_pass.color = "rgba(0, 158, 115, 0.6)"  # #009E73 at 0.6 alpha
scatter_pass.marker = {"radius": 8, "symbol": "circle"}
chart.add_series(scatter_pass)

# Accuracy annotation (theme-adaptive)
chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": 8.5, "y": 0.12, "xAxis": 0, "yAxis": 0},
                "text": f"Accuracy: {accuracy:.1%}",
                "style": {"fontSize": "36px", "color": INK},
                "backgroundColor": ELEVATED_BG,
                "borderColor": INK_SOFT,
                "borderWidth": 2,
                "padding": 15,
            }
        ],
        "labelOptions": {"shape": "rect"},
    }
]

chart.options.credits = {"enabled": False}

# Download Highcharts JS (inline for headless Chrome — CDN blocked from file://)
_headers = {"User-Agent": "Mozilla/5.0"}

req = urllib.request.Request("https://cdn.jsdelivr.net/npm/highcharts/highcharts.js", headers=_headers)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request("https://cdn.jsdelivr.net/npm/highcharts/highcharts-more.js", headers=_headers)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

req = urllib.request.Request("https://cdn.jsdelivr.net/npm/highcharts/modules/annotations.js", headers=_headers)
with urllib.request.urlopen(req, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact for site embedding
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Render PNG via headless Chrome
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
# CDP override is authoritative — --window-size alone leaves ~139 px eaten by Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL safety net: pin to exact 3200×1800 in case of ±1–2 px rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
