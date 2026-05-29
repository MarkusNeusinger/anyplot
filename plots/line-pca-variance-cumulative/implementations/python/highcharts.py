"""anyplot.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: highcharts | Python 3.13
Quality: pending | Updated: 2026-05-29
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.options.series.scatter import ScatterSeries
from PIL import Image
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
ANNOTATION_BG = "rgba(255,253,246,0.92)" if THEME == "light" else "rgba(36,36,32,0.92)"

# Imprint palette — first series is always #009E73
BRAND = "#009E73"  # Cumulative variance line (primary, Imprint position 1)
IMPRINT_BLUE = "#4467A3"  # Individual variance columns (Imprint position 3)
AMBER = "#DDCC77"  # 90% threshold — warning/caution semantic anchor
LAVENDER = "#C475FD"  # 95% threshold — Imprint position 2

# Data — industrial sensor data (12 features), PCA via eigendecomposition
np.random.seed(42)
n_samples = 200
n_features = 12

# Correlated features: a few latent factors drive most variance
latent = np.random.randn(n_samples, 3)
mixing = np.random.randn(3, n_features)
noise = np.random.randn(n_samples, n_features) * 0.5
X_raw = latent @ mixing + noise

X = (X_raw - X_raw.mean(axis=0)) / X_raw.std(axis=0)

cov_matrix = np.cov(X, rowvar=False)
eigenvalues, _ = np.linalg.eigh(cov_matrix)
eigenvalues = eigenvalues[::-1]

explained_variance_ratio = eigenvalues / eigenvalues.sum()
n_components = list(range(1, n_features + 1))
individual_variance = explained_variance_ratio * 100
cumulative_variance = np.cumsum(individual_variance)

threshold_90 = next(i for i, v in enumerate(cumulative_variance) if v >= 90) + 1
threshold_95 = next(i for i, v in enumerate(cumulative_variance) if v >= 95) + 1
val_90 = round(float(cumulative_variance[threshold_90 - 1]), 1)
val_95 = round(float(cumulative_variance[threshold_95 - 1]), 1)

# Title — scale fontsize to prevent overflow (67-char baseline = 66px)
title_text = "PCA Component Selection · line-pca-variance-cumulative · python · highcharts · anyplot.ai"
title_len = len(title_text)
title_fontsize = f"{max(44, round(66 * 67 / title_len))}px"

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif", "color": INK},
    "spacingBottom": 80,
    "spacingLeft": 80,
    "spacingTop": 60,
    "spacingRight": 80,
}

chart.options.title = {
    "text": title_text,
    "style": {"fontSize": title_fontsize, "fontWeight": "600", "color": INK},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Industrial Sensor Data (12 features) — explained variance by principal components",
    "style": {"fontSize": "34px", "color": INK_MUTED, "fontWeight": "300"},
}

chart.options.x_axis = {
    "title": {
        "text": "Number of Components",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "categories": [str(c) for c in n_components],
    "tickInterval": 1,
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickColor": INK_SOFT,
    "tickWidth": 1,
    "tickLength": 8,
}

chart.options.y_axis = {
    "title": {
        "text": "Explained Variance (%)",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "{value}%"},
    "min": 0,
    "max": 100,
    "endOnTick": False,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "plotLines": [
        {
            "value": 90,
            "color": AMBER,
            "width": 3,
            "dashStyle": "LongDash",
            "label": {
                "text": "90%",
                "align": "left",
                "style": {"fontSize": "34px", "color": AMBER, "fontWeight": "600"},
                "x": 10,
                "y": -10,
            },
            "zIndex": 4,
        },
        {
            "value": 95,
            "color": LAVENDER,
            "width": 3,
            "dashStyle": "LongDash",
            "label": {
                "text": "95%",
                "align": "left",
                "style": {"fontSize": "34px", "color": LAVENDER, "fontWeight": "600"},
                "x": 10,
                "y": -10,
            },
            "zIndex": 4,
        },
    ],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "44px", "fontWeight": "400", "color": INK_SOFT},
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "floating": True,
    "backgroundColor": ELEVATED_BG,
    "borderRadius": 8,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "symbolWidth": 36,
    "symbolHeight": 16,
    "itemMarginBottom": 10,
    "padding": 20,
    "x": -50,
    "y": 200,
}

chart.options.plot_options = {
    "series": {"animation": False},
    "line": {
        "lineWidth": 5,
        "marker": {"enabled": True, "radius": 10, "symbol": "circle"},
        "shadow": {"color": "rgba(0,0,0,0.08)", "offsetX": 1, "offsetY": 2, "width": 4},
    },
    "column": {"borderWidth": 0, "borderRadius": 4, "pointPadding": 0.12, "groupPadding": 0.08},
}

chart.options.tooltip = {
    "shared": True,
    "style": {"fontSize": "34px"},
    "headerFormat": "<b>Component {point.key}</b><br/>",
    "pointFormat": "{series.name}: <b>{point.y:.1f}%</b><br/>",
}

# Individual variance as column series (subtle background, Imprint position 3 with alpha)
col_series = ColumnSeries()
col_series.name = "Individual Variance"
col_series.data = [round(float(v), 2) for v in individual_variance]
col_series.color = "rgba(68, 103, 163, 0.25)"
chart.add_series(col_series)

# Cumulative variance as line series (primary story, Imprint position 1)
line_series = LineSeries()
line_series.name = "Cumulative Variance"
line_series.data = [round(float(v), 2) for v in cumulative_variance]
line_series.color = BRAND
line_series.marker = {"fillColor": BRAND, "lineWidth": 2, "lineColor": PAGE_BG}
chart.add_series(line_series)

# Mark 90% threshold crossing (amber — warning/caution semantic anchor)
marker_90 = ScatterSeries()
marker_90.name = f"90% at {threshold_90} components"
marker_90.data = [[threshold_90 - 1, round(float(cumulative_variance[threshold_90 - 1]), 2)]]
marker_90.color = AMBER
marker_90.marker = {"radius": 16, "symbol": "diamond", "fillColor": AMBER, "lineWidth": 3, "lineColor": PAGE_BG}
chart.add_series(marker_90)

# Mark 95% threshold crossing (lavender — Imprint position 2)
marker_95 = ScatterSeries()
marker_95.name = f"95% at {threshold_95} components"
marker_95.data = [[threshold_95 - 1, round(float(cumulative_variance[threshold_95 - 1]), 2)]]
marker_95.color = LAVENDER
marker_95.marker = {"radius": 16, "symbol": "diamond", "fillColor": LAVENDER, "lineWidth": 3, "lineColor": PAGE_BG}
chart.add_series(marker_95)

# Annotation callouts at threshold crossings
chart.options.annotations = [
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": ANNOTATION_BG,
            "borderColor": AMBER,
            "borderWidth": 2,
            "borderRadius": 8,
            "padding": 18,
            "style": {"fontSize": "26px", "color": INK, "fontWeight": "500"},
            "shape": "callout",
            "verticalAlign": "top",
        },
        "labels": [
            {
                "point": {"x": threshold_90 - 1, "y": val_90, "xAxis": 0, "yAxis": 0},
                "text": f"Only {threshold_90} components explain {val_90}% of variance",
                "y": 60,
                "x": 80,
            }
        ],
    },
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": ANNOTATION_BG,
            "borderColor": LAVENDER,
            "borderWidth": 2,
            "borderRadius": 8,
            "padding": 18,
            "style": {"fontSize": "26px", "color": INK, "fontWeight": "500"},
            "shape": "callout",
            "verticalAlign": "top",
        },
        "labels": [
            {
                "point": {"x": threshold_95 - 1, "y": val_95, "xAxis": 0, "yAxis": 0},
                "text": f"{threshold_95} components reach {val_95}% — diminishing returns beyond",
                "y": 60,
                "x": 100,
            }
        ],
    },
]

# Download Highcharts JS and annotations module (inline — required for headless Chrome)
highcharts_js = None
for _url in ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]:
    try:
        _req = urllib.request.Request(_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(_req, timeout=30) as _r:
            highcharts_js = _r.read().decode("utf-8")
        break
    except Exception:
        continue
if not highcharts_js:
    raise RuntimeError("Failed to download highcharts.js")

annotations_js = None
for _url in [
    "https://code.highcharts.com/modules/annotations.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js",
]:
    try:
        _req = urllib.request.Request(_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(_req, timeout=30) as _r:
            annotations_js = _r.read().decode("utf-8")
        break
    except Exception:
        continue
if not annotations_js:
    raise RuntimeError("Failed to download annotations.js")

# Build HTML with inline scripts (CDN fails from file:// in headless Chrome)
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome
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
# CDP override is authoritative — --window-size alone is eaten by Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin exact dimensions (safety net for ±1–2 px rounding in headless Chrome)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
