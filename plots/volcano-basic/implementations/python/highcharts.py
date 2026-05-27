""" anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-14
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]
COLOR_NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"

np.random.seed(42)
n_genes = 500

log2_fc = np.random.normal(0, 1.5, n_genes)
pvalues = np.random.beta(0.5, 5, n_genes)

n_sig_up = 30
n_sig_down = 25

log2_fc[:n_sig_up] = np.random.uniform(1.5, 4, n_sig_up)
pvalues[:n_sig_up] = np.random.uniform(1e-10, 0.001, n_sig_up)

log2_fc[n_sig_up : n_sig_up + n_sig_down] = np.random.uniform(-4, -1.5, n_sig_down)
pvalues[n_sig_up : n_sig_up + n_sig_down] = np.random.uniform(1e-10, 0.001, n_sig_down)

neg_log10_p = -np.log10(pvalues)

p_threshold = 0.05
fc_threshold = 1.0

sig_up = (pvalues < p_threshold) & (log2_fc > fc_threshold)
sig_down = (pvalues < p_threshold) & (log2_fc < -fc_threshold)
not_sig = ~(sig_up | sig_down)

chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginLeft": 220,
    "marginRight": 280,
    "marginTop": 150,
}

chart.options.title = {
    "text": "volcano-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "normal"},
}

chart.options.x_axis = {
    "title": {"text": "log₂(Fold Change)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "plotLines": [
        {"value": -fc_threshold, "color": INK_SOFT, "dashStyle": "Dash", "width": 2, "zIndex": 3},
        {"value": fc_threshold, "color": INK_SOFT, "dashStyle": "Dash", "width": 2, "zIndex": 3},
    ],
}

neg_log10_threshold = -np.log10(p_threshold)
chart.options.y_axis = {
    "title": {"text": "-log₁₀(p-value)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "plotLines": [{"value": neg_log10_threshold, "color": INK_SOFT, "dashStyle": "Dash", "width": 2, "zIndex": 3}],
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 80,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 8, "states": {"hover": {"enabled": True, "lineColor": INK}}},
        "states": {"inactive": {"opacity": 1}},
    }
}

series_ns = ScatterSeries()
series_ns.name = f"Not Significant ({np.sum(not_sig)})"
series_ns.data = [[float(x), float(y)] for x, y in zip(log2_fc[not_sig], neg_log10_p[not_sig], strict=True)]
series_ns.color = COLOR_NEUTRAL
series_ns.marker = {"radius": 8, "symbol": "circle"}
chart.add_series(series_ns)

series_down = ScatterSeries()
series_down.name = f"Down-regulated ({np.sum(sig_down)})"
series_down.data = [[float(x), float(y)] for x, y in zip(log2_fc[sig_down], neg_log10_p[sig_down], strict=True)]
series_down.color = IMPRINT[2]
series_down.marker = {"radius": 10, "symbol": "circle"}
chart.add_series(series_down)

series_up = ScatterSeries()
series_up.name = f"Up-regulated ({np.sum(sig_up)})"
series_up.data = [[float(x), float(y)] for x, y in zip(log2_fc[sig_up], neg_log10_p[sig_up], strict=True)]
series_up.color = IMPRINT[1]
series_up.marker = {"radius": 10, "symbol": "circle"}
chart.add_series(series_up)

chart.options.credits = {"enabled": False}

y_max = float(np.max(neg_log10_p)) + 0.3

chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": -fc_threshold, "y": y_max, "xAxis": 0, "yAxis": 0},
                "text": "FC = -1",
                "style": {"fontSize": "18px", "color": INK_SOFT},
                "backgroundColor": ELEVATED_BG,
                "borderColor": INK_SOFT,
                "borderWidth": 1,
                "y": -15,
            },
            {
                "point": {"x": fc_threshold, "y": y_max, "xAxis": 0, "yAxis": 0},
                "text": "FC = +1",
                "style": {"fontSize": "18px", "color": INK_SOFT},
                "backgroundColor": ELEVATED_BG,
                "borderColor": INK_SOFT,
                "borderWidth": 1,
                "y": -15,
            },
            {
                "point": {"x": 4.5, "y": neg_log10_threshold, "xAxis": 0, "yAxis": 0},
                "text": "p = 0.05",
                "style": {"fontSize": "18px", "color": INK_SOFT},
                "backgroundColor": ELEVATED_BG,
                "borderColor": INK_SOFT,
                "borderWidth": 1,
                "y": -25,
            },
        ],
        "labelOptions": {"shape": "rect"},
    }
]

try:
    req = urllib.request.Request(
        "https://code.highcharts.com/highcharts.js",
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")

    req_anno = urllib.request.Request(
        "https://code.highcharts.com/modules/annotations.js",
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
    )
    with urllib.request.urlopen(req_anno, timeout=30) as response:
        annotations_js = response.read().decode("utf-8")
except urllib.error.URLError:
    try:
        req = urllib.request.Request("https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js")
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        req_anno = urllib.request.Request("https://cdn.jsdelivr.net/npm/highcharts@latest/modules/annotations.js")
        with urllib.request.urlopen(req_anno, timeout=30) as response:
            annotations_js = response.read().decode("utf-8")
    except Exception:
        highcharts_js = ""
        annotations_js = ""

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
