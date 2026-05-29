""" anyplot.ai
box-basic: Basic Box Plot
Library: highcharts unknown | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-28
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.boxplot import BoxPlotSeries
from highcharts_core.options.series.data.boxplot import BoxPlotData
from highcharts_core.options.series.scatter import ScatterSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data: employee performance scores across 5 departments
np.random.seed(42)
departments = ["Engineering", "Marketing", "Sales", "Design", "Finance"]

scores = [
    np.random.normal(78, 8, 80),
    np.random.normal(72, 14, 60),
    np.random.normal(68, 9, 90),
    np.random.normal(82, 7, 50),
    np.random.normal(75, 18, 70),
]

box_stats = []
outlier_data = []

for i, data in enumerate(scores):
    data = np.clip(data, 0, 100)
    q1 = float(np.percentile(data, 25))
    median = float(np.percentile(data, 50))
    q3 = float(np.percentile(data, 75))
    iqr = q3 - q1
    whisker_low = float(max(data[data >= q1 - 1.5 * iqr].min(), data.min()))
    whisker_high = float(min(data[data <= q3 + 1.5 * iqr].max(), data.max()))

    box_stats.append(
        {
            "low": round(whisker_low, 1),
            "q1": round(q1, 1),
            "median": round(median, 1),
            "q3": round(q3, 1),
            "high": round(whisker_high, 1),
        }
    )

    outliers = data[(data < q1 - 1.5 * iqr) | (data > q3 + 1.5 * iqr)]
    for val in outliers:
        outlier_data.append([i, round(float(val), 1)])

medians = [s["median"] for s in box_stats]
spreads = [s["q3"] - s["q1"] for s in box_stats]
best_dept_idx = int(np.argmax(medians))
widest_dept_idx = int(np.argmax(spreads))
best_dept = departments[best_dept_idx]
best_median = medians[best_dept_idx]
widest_dept = departments[widest_dept_idx]
widest_iqr = spreads[widest_dept_idx]
n_outliers = len(outlier_data)
outlier_s = "s" if n_outliers != 1 else ""

# Box plot data with per-point Imprint palette colors (color property is native to BoxPlotData)
box_data = [
    BoxPlotData(
        low=box_stats[i]["low"],
        q1=box_stats[i]["q1"],
        median=box_stats[i]["median"],
        q3=box_stats[i]["q3"],
        high=box_stats[i]["high"],
        color=IMPRINT_PALETTE[i],
    )
    for i in range(len(departments))
]

# Build chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "boxplot",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 160,
    "marginLeft": 200,
    "marginRight": 100,
    "spacingTop": 30,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
    "animation": False,
}

chart.options.title = {
    "text": "box-basic · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "700", "color": INK},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Annual Performance Review Scores by Department",
    "style": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "400"},
}

chart.options.x_axis = {
    "categories": departments,
    "title": {"text": "Department", "style": {"fontSize": "56px", "color": INK, "fontWeight": "600"}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineWidth": 0,
    "tickWidth": 0,
    "gridLineWidth": 0,
}

chart.options.y_axis = {
    "title": {
        "text": "Score (out of 100)",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "600"},
        "margin": 16,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Solid",
    "tickInterval": 10,
    "lineWidth": 0,
    "max": 100,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.tooltip = {"enabled": False}

chart.options.plot_options = {
    "boxplot": {
        "pointWidth": 240,
        "lineWidth": 3,
        "medianWidth": 6,
        "medianColor": INK,
        "stemColor": INK_SOFT,
        "stemWidth": 2,
        "stemDashStyle": "Solid",
        "whiskerWidth": 3,
        "whiskerLength": "50%",
        "whiskerColor": INK_SOFT,
    },
    "series": {"animation": False},
}

box_series = BoxPlotSeries(name="Department Scores", data=box_data)

outlier_series = ScatterSeries(
    name="Outliers",
    data=outlier_data,
    marker={"fillColor": "#AE3030", "lineWidth": 2, "lineColor": "#AE3030", "radius": 10, "symbol": "circle"},
    z_index=10,
    show_in_legend=False,
)

chart.add_series(box_series)
chart.add_series(outlier_series)

chart_js = chart.to_js_literal(event_listener_enabled=False)
# Inject series-level fillColor (not exposed by highcharts-core BoxPlotSeries API)
chart_js = chart_js.replace("name: 'Department Scores'", f"fillColor: '{PAGE_BG}',\n  name: 'Department Scores'", 1)

# Download Highcharts JS (CDN cannot load from file:// in headless Chrome)
with urllib.request.urlopen("https://cdn.jsdelivr.net/npm/highcharts/highcharts.js", timeout=30) as r:
    highcharts_js = r.read().decode("utf-8")
with urllib.request.urlopen("https://cdn.jsdelivr.net/npm/highcharts/highcharts-more.js", timeout=30) as r:
    highcharts_more_js = r.read().decode("utf-8")

# Annotation labels rendered via Highcharts renderer API (no Python equivalent)
annotation_js = f"""
setTimeout(function() {{
    var chart = Highcharts.charts[0];
    if (!chart) return;

    chart.renderer.label(
        '<span style="font-size:34px;color:#009E73;font-weight:700;">▲ Top Performer</span>' +
        '<br><span style="font-size:28px;color:{INK_SOFT};">{best_dept} — Median: {best_median:.0f}</span>',
        chart.plotLeft + 20,
        chart.plotTop + 15
    )
    .attr({{ fill: '{ELEVATED_BG}', stroke: '#009E73', 'stroke-width': 2, r: 8, padding: 16, zIndex: 20 }})
    .css({{ lineHeight: '42px' }})
    .add();

    chart.renderer.label(
        '<span style="font-size:34px;color:#BD8233;font-weight:700;">● Widest Spread</span>' +
        '<br><span style="font-size:28px;color:{INK_SOFT};">{widest_dept} — IQR: {widest_iqr:.0f} pts</span>',
        chart.plotLeft + chart.plotWidth - 480,
        chart.plotTop + 15
    )
    .attr({{ fill: '{ELEVATED_BG}', stroke: '#BD8233', 'stroke-width': 2, r: 8, padding: 16, zIndex: 20 }})
    .css({{ lineHeight: '42px' }})
    .add();

    chart.renderer.label(
        '<span style="font-size:30px;color:#AE3030;font-weight:600;">● {n_outliers} outlier{outlier_s} detected</span>',
        chart.plotLeft + 20,
        chart.plotTop + chart.plotHeight - 80
    )
    .attr({{ fill: '{ELEVATED_BG}', stroke: '#AE3030', 'stroke-width': 2, r: 8, padding: 14, zIndex: 20 }})
    .css({{ lineHeight: '38px' }})
    .add();
}}, 500);
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{chart_js}</script>
    <script>{annotation_js}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via Selenium
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

# PIL safety net: pin to exact canvas dimensions
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
