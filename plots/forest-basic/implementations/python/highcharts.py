""" anyplot.ai
forest-basic: Meta-Analysis Forest Plot
Library: highcharts unknown | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-11
"""

import os
import tempfile
import time
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


try:
    import requests
except ImportError:
    requests = None

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"
SECONDARY = "#C475FD"

# Data: Meta-analysis of treatment effect studies (mean difference)
studies = [
    "Smith et al. 2018",
    "Johnson et al. 2019",
    "Williams et al. 2019",
    "Brown et al. 2020",
    "Davis et al. 2020",
    "Miller et al. 2021",
    "Wilson et al. 2021",
    "Moore et al. 2022",
    "Taylor et al. 2022",
    "Anderson et al. 2023",
]

# Effect sizes (mean differences) with confidence intervals
effect_sizes = [-0.35, 0.12, -0.52, -0.28, 0.05, -0.41, -0.18, -0.55, -0.22, -0.38]
ci_lower = [-0.68, -0.21, -0.88, -0.55, -0.32, -0.72, -0.48, -0.91, -0.52, -0.65]
ci_upper = [-0.02, 0.45, -0.16, -0.01, 0.42, -0.10, 0.12, -0.19, 0.08, -0.11]
weights = [8.5, 6.2, 9.1, 10.3, 5.8, 8.9, 7.4, 6.8, 9.5, 11.2]

# Pooled estimate (diamond)
pooled_effect = -0.28
pooled_ci_lower = -0.42
pooled_ci_upper = -0.14

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginLeft": 350,
    "marginRight": 150,
    "marginBottom": 250,
    "marginTop": 150,
}

# Title
chart.options.title = {"text": "forest-basic · highcharts · anyplot.ai", "style": {"fontSize": "28px", "color": INK}}

chart.options.subtitle = {
    "text": "Meta-Analysis of Treatment Effect on Primary Outcome",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# Y-axis labels: studies at top, pooled at bottom
all_labels = ["Pooled Estimate", ""] + list(reversed(studies))
n_studies = len(studies)

# X-axis (effect size)
chart.options.x_axis = {
    "title": {"text": "Mean Difference (95% CI)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "plotLines": [
        {
            "value": 0,
            "color": INK_SOFT,
            "width": 3,
            "dashStyle": "Dash",
            "zIndex": 3,
            "label": {
                "text": "No Effect",
                "style": {"fontSize": "18px", "color": INK_SOFT},
                "rotation": 0,
                "align": "center",
                "verticalAlign": "top",
                "y": 25,
                "x": 0,
            },
        }
    ],
    "min": -1.2,
    "max": 0.8,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "tickInterval": 0.2,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Y-axis (studies)
chart.options.y_axis = {
    "title": {"text": None},
    "categories": all_labels,
    "reversed": False,
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "x": -10},
    "gridLineWidth": 0,
    "min": -0.15,
    "max": len(all_labels) - 0.5,
    "tickPositions": list(range(len(all_labels))),
    "startOnTick": False,
    "endOnTick": False,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Disable legend
chart.options.legend = {"enabled": False}

# Create series for study points
study_points_data = []
for i, (es, w, lower, upper) in enumerate(zip(effect_sizes, weights, ci_lower, ci_upper, strict=True)):
    radius = 8 + (w / max(weights)) * 16
    y_pos = n_studies + 1 - i
    study_points_data.append(
        {
            "x": es,
            "y": y_pos,
            "marker": {"radius": radius, "symbol": "square"},
            "name": studies[i],
            "custom": {"weight": w, "ciLower": lower, "ciUpper": upper},
        }
    )

study_series = ScatterSeries()
study_series.data = study_points_data
study_series.name = "Study Effect"
study_series.color = BRAND
study_series.marker = {"symbol": "square", "lineWidth": 2, "lineColor": BRAND}

chart.add_series(study_series)

# Create series for confidence interval lines
for i, (lower, upper) in enumerate(zip(ci_lower, ci_upper, strict=True)):
    y_pos = n_studies + 1 - i
    ci_series = ScatterSeries()
    ci_series.data = [{"x": lower, "y": y_pos}, {"x": upper, "y": y_pos}]
    ci_series.name = f"CI {i}"
    ci_series.color = BRAND
    ci_series.marker = {"enabled": False}
    ci_series.enable_mouse_tracking = False
    ci_series.show_in_legend = False
    ci_series.line_width = 3
    ci_series.type = "line"
    chart.add_series(ci_series)

# Pooled estimate (diamond)
pooled_y = 0

diamond_series = ScatterSeries()
diamond_series.data = [
    {
        "x": pooled_effect,
        "y": pooled_y,
        "name": "Pooled Estimate",
        "custom": {"ciLower": pooled_ci_lower, "ciUpper": pooled_ci_upper, "weight": 100},
    }
]
diamond_series.name = "Pooled Estimate"
diamond_series.color = SECONDARY
diamond_series.marker = {"symbol": "diamond", "radius": 20, "lineWidth": 3, "lineColor": BRAND, "fillColor": SECONDARY}

chart.add_series(diamond_series)

# CI line for pooled estimate
pooled_ci_series = ScatterSeries()
pooled_ci_series.data = [{"x": pooled_ci_lower, "y": pooled_y}, {"x": pooled_ci_upper, "y": pooled_y}]
pooled_ci_series.name = "Pooled CI"
pooled_ci_series.color = BRAND
pooled_ci_series.marker = {"enabled": False}
pooled_ci_series.line_width = 4
pooled_ci_series.type = "line"
pooled_ci_series.enable_mouse_tracking = False
pooled_ci_series.show_in_legend = False

chart.add_series(pooled_ci_series)

# Enhanced tooltip
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        "<b>{point.name}</b><br/>"
        "Effect Size: {point.x:.2f}<br/>"
        "95% CI: [{point.custom.ciLower:.2f}, {point.custom.ciUpper:.2f}]<br/>"
        "Weight: {point.custom.weight:.1f}%"
    ),
    "style": {"fontSize": "18px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 2,
    "borderColor": INK_SOFT,
}

# Credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS for inline embedding
# Try multiple CDN sources for reliability
cdn_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11.4.0/highcharts.min.js",
    "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.min.js",
    "https://code.highcharts.com/highcharts.js",
]

highcharts_js = None

for cdn_url in cdn_urls:
    if requests:
        try:
            session = requests.Session()
            session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/javascript,*/*",
                    "Accept-Encoding": "gzip, deflate",
                }
            )
            response = session.get(cdn_url, timeout=30)
            response.raise_for_status()
            highcharts_js = response.text
            break
        except Exception:
            continue

if not highcharts_js:
    import urllib.request

    for cdn_url in cdn_urls:
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    cdn_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                with urllib.request.urlopen(req, timeout=30) as response:
                    highcharts_js = response.read().decode("utf-8")
                break
            except Exception:
                if attempt == 1:
                    break
                time.sleep(1)
        if highcharts_js:
            break

if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts JS from any CDN")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML file
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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

driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
