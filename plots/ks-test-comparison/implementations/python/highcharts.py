""" anyplot.ai
ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
Library: highcharts unknown | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-29
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.annotations import Annotation
from highcharts_core.options.series.area import LineSeries
from PIL import Image
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BAND_COLOR = "rgba(26,26,23,0.07)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette — semantic exception: good/pass→green, bad/fail→red
COLOR_GOOD = "#009E73"  # Imprint position 1 (brand green)
COLOR_BAD = "#AE3030"  # Imprint position 5 (matte red — semantic anchor for bad/loss/error)
COLOR_DIST = INK  # theme-adaptive neutral for reference line

# Data — Credit scoring: Good vs Bad customer score distributions
np.random.seed(42)
good_scores = np.random.beta(5, 2, size=300) * 800 + 200
bad_scores = np.random.beta(2, 4, size=300) * 800 + 200

ks_stat, p_value = stats.ks_2samp(good_scores, bad_scores)

# Compute ECDFs
good_sorted = np.sort(good_scores)
bad_sorted = np.sort(bad_scores)
good_ecdf_y = np.arange(1, len(good_sorted) + 1) / len(good_sorted)
bad_ecdf_y = np.arange(1, len(bad_sorted) + 1) / len(bad_sorted)

# Point of maximum divergence
all_values = np.sort(np.concatenate([good_scores, bad_scores]))
good_ecdf_at_all = np.searchsorted(good_sorted, all_values, side="right") / len(good_sorted)
bad_ecdf_at_all = np.searchsorted(bad_sorted, all_values, side="right") / len(bad_sorted)
max_idx = np.argmax(np.abs(good_ecdf_at_all - bad_ecdf_at_all))
max_x = float(all_values[max_idx])
max_y_good = float(good_ecdf_at_all[max_idx])
max_y_bad = float(bad_ecdf_at_all[max_idx])

# Step function data
good_step_data = [[float(x), float(y)] for x, y in zip(good_sorted, good_ecdf_y, strict=True)]
bad_step_data = [[float(x), float(y)] for x, y in zip(bad_sorted, bad_ecdf_y, strict=True)]
max_distance_data = [[max_x, min(max_y_good, max_y_bad)], [max_x, max(max_y_good, max_y_bad)]]

chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginTop": 180,
    "marginLeft": 160,
    "marginRight": 80,
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif", "color": INK},
}

chart.options.title = {
    "text": "ks-test-comparison · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "700", "color": INK},
    "y": 40,
}

chart.options.subtitle = {
    "text": (
        f"K-S Statistic = {ks_stat:.4f}  │  p-value = {p_value:.2e}  │  Distributions are significantly different"
    ),
    "style": {"fontSize": "40px", "color": INK_SOFT, "fontWeight": "400"},
    "y": 100,
}

chart.options.x_axis = {
    "title": {
        "text": "Credit Score (200–1000)",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "600"},
        "y": 16,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "tickInterval": 100,
    "min": 200,
    "max": 1000,
    "startOnTick": True,
    "endOnTick": True,
    "gridLineWidth": 0,
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickColor": INK_SOFT,
    "tickLength": 8,
    "plotBands": [{"from": max_x - 15, "to": max_x + 15, "color": BAND_COLOR, "zIndex": 0}],
}

chart.options.y_axis = {
    "title": {"text": "Cumulative Proportion (0–1)", "style": {"fontSize": "56px", "color": INK, "fontWeight": "600"}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 0,
    "max": 1,
    "tickInterval": 0.2,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dash",
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickColor": INK_SOFT,
}

chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "normal"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolWidth": 60,
    "symbolHeight": 18,
    "itemDistance": 80,
    "y": -10,
}

chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"lineWidth": 7}}}
}

chart.options.tooltip = {
    "headerFormat": '<span style="font-size:24px;font-weight:bold">Credit Score: {point.x:.0f}</span><br/>',
    "pointFormat": '<span style="font-size:22px">{series.name}: <b>{point.y:.3f}</b></span>',
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "style": {"color": INK},
}

chart.options.credits = {"enabled": False}

# Good customers ECDF — solid green (semantic: good/pass → Imprint green)
good_series = LineSeries()
good_series.data = good_step_data
good_series.name = "Good Customers"
good_series.color = COLOR_GOOD
good_series.step = "left"
good_series.z_index = 2
chart.add_series(good_series)

# Bad customers ECDF — dashed red (semantic: bad/fail → Imprint matte red)
bad_series = LineSeries()
bad_series.data = bad_step_data
bad_series.name = "Bad Customers"
bad_series.color = COLOR_BAD
bad_series.dash_style = "ShortDash"
bad_series.step = "left"
bad_series.z_index = 2
chart.add_series(bad_series)

# Max distance reference line — theme-adaptive neutral
distance_series = LineSeries()
distance_series.data = max_distance_data
distance_series.name = f"Max Distance (D = {ks_stat:.4f})"
distance_series.color = COLOR_DIST
distance_series.dash_style = "LongDash"
distance_series.line_width = 4
distance_series.marker = {
    "enabled": True,
    "radius": 10,
    "symbol": "diamond",
    "fillColor": COLOR_DIST,
    "lineColor": PAGE_BG,
    "lineWidth": 3,
}
distance_series.z_index = 5
chart.add_series(distance_series)

# Annotation callout at midpoint of max divergence
mid_y = (max_y_good + max_y_bad) / 2
chart.options.annotations = [
    Annotation.from_dict(
        {
            "labels": [
                {
                    "point": {"x": max_x, "y": mid_y, "xAxis": 0, "yAxis": 0},
                    "text": f"D = {ks_stat:.4f}<br/>Strong separation",
                    "x": 160,
                    "style": {"fontSize": "36px", "fontWeight": "bold", "color": INK, "textAlign": "center"},
                }
            ],
            "labelOptions": {
                "backgroundColor": ELEVATED_BG,
                "borderColor": INK_SOFT,
                "borderWidth": 2,
                "borderRadius": 10,
                "padding": 20,
                "shape": "callout",
                "shadow": {"color": "rgba(0,0,0,0.12)", "offsetX": 3, "offsetY": 3, "width": 8},
            },
            "draggable": "",
        }
    )
]

# Download Highcharts JS + annotations module (required for headless Chrome)
hc_base = "https://cdn.jsdelivr.net/npm/highcharts"
with urllib.request.urlopen(f"{hc_base}/highcharts.js", timeout=30) as r:
    highcharts_js = r.read().decode("utf-8")
with urllib.request.urlopen(f"{hc_base}/modules/annotations.js", timeout=30) as r:
    highcharts_ann_js = r.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_ann_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:3200px;height:1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
for flag in [
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--hide-scrollbars",
    "--window-size=3200,1800",
]:
    chrome_options.add_argument(flag)

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative — --window-size alone loses ~139 px to Chrome chrome in headless mode
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL safety net: pin to exact 3200×1800 in case of sub-pixel rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
