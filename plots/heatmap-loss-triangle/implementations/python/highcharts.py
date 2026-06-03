"""anyplot.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-06-03
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from highcharts_core.utility_classes.javascript_functions import CallbackFunction
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ANYPLOT_AMBER = "#DDCC77"  # projected cell border — semantic anchor

# Imprint sequential colormap (single-polarity continuous data)
CMAP_LOW = "#009E73"  # brand green — low cumulative values
CMAP_HIGH = "#4467A3"  # blue — high cumulative values

# Canvas (2400x2400 — square for symmetric heatmap grid)
W, H = 2400, 2400

# Data
np.random.seed(42)

accident_years = list(range(2015, 2025))
development_periods = list(range(1, 11))
n_years = len(accident_years)
n_periods = len(development_periods)

base_claims = np.array([3200, 3500, 3800, 4100, 4500, 4900, 5300, 5700, 6100, 6500])
dev_factors = np.array([1.0, 2.15, 1.45, 1.22, 1.12, 1.07, 1.04, 1.025, 1.015, 1.008])

cumulative = np.zeros((n_years, n_periods))
for i in range(n_years):
    cumulative[i, 0] = base_claims[i] + np.random.normal(0, 200)
    for j in range(1, n_periods):
        noise = 1 + np.random.normal(0, 0.02)
        cumulative[i, j] = cumulative[i, j - 1] * dev_factors[j] * noise
cumulative = np.round(cumulative, 0)

is_actual = np.zeros((n_years, n_periods), dtype=bool)
for i in range(n_years):
    for j in range(n_periods):
        if i + j < n_years:
            is_actual[i, j] = True

age_to_age = []
for j in range(1, n_periods):
    factors = []
    for i in range(n_years):
        if is_actual[i, j] and is_actual[i, j - 1]:
            factors.append(cumulative[i, j] / cumulative[i, j - 1])
    age_to_age.append(round(np.mean(factors), 3) if factors else dev_factors[j])

val_min = float(np.min(cumulative))
val_max = float(np.max(cumulative))
threshold = int((val_min + val_max) * 0.45)

actual_data = []
projected_data = []
for i in range(n_years):
    for j in range(n_periods):
        val = float(cumulative[i, j])
        point = {"x": j, "y": i, "value": val}
        if is_actual[i, j]:
            actual_data.append(point)
        else:
            projected_data.append(point)

# JS callbacks
title = "heatmap-loss-triangle · python · highcharts · anyplot.ai"

datalabel_fn = CallbackFunction.from_js_literal(
    f"""function() {{
    var val = Highcharts.numberFormat(this.point.value, 0, '.', ',');
    var isProjected = (this.series.name === 'Projected (IBNR)');
    var color = this.point.value > {threshold} ? '#F0EFE8' : '#1A1A17';
    if (isProjected) {{
        return '<span style="color:' + color + ';font-size:36px;font-style:italic">' + val + '</span>';
    }}
    return '<span style="color:' + color + ';font-size:36px;font-weight:700">' + val + '</span>';
}}"""
)

tooltip_fn = CallbackFunction.from_js_literal(
    """function() {
    var year = this.series.yAxis.categories[this.point.y];
    var period = this.series.xAxis.categories[this.point.x];
    var val = Highcharts.numberFormat(this.point.value, 0, '.', ',');
    return '<b>Accident Year: ' + year + '</b><br>' +
           'Development Period: <b>' + period + '</b><br>' +
           'Cumulative Claims: <b>$' + val + 'K</b><br>' +
           'Type: <b>' + this.series.name + '</b>';
}"""
)

coloraxis_label_fn = CallbackFunction.from_js_literal(
    """function() {
    return Highcharts.numberFormat(this.value, 0, '.', ',');
}"""
)

# Age-to-age factor boxes (theme-adaptive colors embedded via Python f-string)
factor_box_parts = []
for idx, f in enumerate(age_to_age):
    lbl = f"{development_periods[idx]}→{development_periods[idx + 1]}"
    val_str = f"{f:.3f}"
    factor_box_parts.append(
        f"chart.renderer.rect(x + {idx} * spacing, fy, boxW, 72, 6)"
        f".attr({{fill: '{ELEVATED_BG}', stroke: '{INK_SOFT}', 'stroke-width': 1.5}}).add();\n"
        f"    chart.renderer.text('{lbl}', x + {idx} * spacing + boxW/2, fy + 28)"
        f".attr({{align: 'center'}})"
        f".css({{fontSize: '28px', color: '{INK_SOFT}', fontWeight: '500'}}).add();\n"
        f"    chart.renderer.text('{val_str}', x + {idx} * spacing + boxW/2, fy + 60)"
        f".attr({{align: 'center'}})"
        f".css({{fontSize: '36px', color: '{INK}', fontWeight: '700'}}).add();"
    )
factors_js = "\n    ".join(factor_box_parts)

load_fn = CallbackFunction.from_js_literal(
    f"""function() {{
    var chart = this;
    var x = chart.plotLeft;
    var plotRight = chart.plotLeft + chart.plotWidth;
    var totalW = plotRight - x;

    var sepY = chart.plotTop + chart.plotHeight + 158;
    chart.renderer.path(['M', x, sepY, 'L', plotRight, sepY])
        .attr({{stroke: '{INK_SOFT}', 'stroke-width': 1.5, 'stroke-dasharray': '10,5'}}).add();

    var fy = chart.plotTop + chart.plotHeight + 220;
    chart.renderer.text('Age-to-Age Development Factors', x, fy - 16)
        .css({{fontSize: '36px', color: '{INK}', fontWeight: '700'}}).add();

    var spacing = Math.floor(totalW / 9);
    var boxW = spacing - 14;
    {factors_js}

    var ly = fy + 110;
    chart.renderer.rect(x, ly, 44, 34, 4)
        .attr({{fill: '{CMAP_LOW}', stroke: '{PAGE_BG}', 'stroke-width': 5}}).add();
    chart.renderer.text('Actual (Observed)', x + 60, ly + 26)
        .css({{fontSize: '36px', color: '{INK}', fontWeight: '600'}}).add();

    chart.renderer.rect(x + 460, ly, 44, 34, 4)
        .attr({{fill: '{CMAP_HIGH}', stroke: '{ANYPLOT_AMBER}', 'stroke-width': 6}}).add();
    chart.renderer.text('Projected (IBNR Estimate)', x + 520, ly + 26)
        .css({{fontSize: '36px', color: '{INK}', fontWeight: '600', fontStyle: 'italic'}}).add();
}}"""
)

# Build chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": W,
    "height": H,
    "backgroundColor": PAGE_BG,
    "marginTop": 180,
    "marginBottom": 510,
    "marginLeft": 200,
    "marginRight": 290,
    "style": {"fontFamily": "'Helvetica Neue', Helvetica, Arial, sans-serif"},
    "events": {"load": load_fn},
}

chart.options.title = {"text": title, "style": {"fontSize": "66px", "fontWeight": "700", "color": INK}, "y": 50}

chart.options.subtitle = {
    "text": "Cumulative Paid Claims ($K) — Accident Years 2015–2024",
    "style": {"fontSize": "40px", "color": INK_SOFT, "fontWeight": "400"},
    "y": 110,
}

chart.options.x_axis = {
    "categories": [str(p) for p in development_periods],
    "title": {
        "text": "Development Period (Years)",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "600"},
        "margin": 24,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": "rgba(0,0,0,0)",
}

chart.options.y_axis = {
    "categories": [str(y) for y in accident_years],
    "title": {"text": "Accident Year", "style": {"fontSize": "56px", "color": INK, "fontWeight": "600"}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "reversed": True,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": "rgba(0,0,0,0)",
}

chart.options.color_axis = {
    "min": val_min,
    "max": val_max,
    "minColor": CMAP_LOW,
    "maxColor": CMAP_HIGH,
    "stops": [[0, CMAP_LOW], [1, CMAP_HIGH]],
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}, "formatter": coloraxis_label_fn},
}

chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 340,
    "itemStyle": {"fontSize": "36px", "color": INK_SOFT},
    "title": {"text": "Cumulative<br/>Claims ($K)", "style": {"fontSize": "36px", "fontWeight": "600", "color": INK}},
}

chart.options.tooltip = {
    "formatter": tooltip_fn,
    "style": {"fontSize": "28px"},
    "useHTML": True,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
}

chart.options.credits = {"enabled": False}

chart.options.plot_options = {"heatmap": {"dataLabels": {"enabled": True, "formatter": datalabel_fn, "useHTML": True}}}

actual_series = HeatmapSeries()
actual_series.name = "Actual Claims"
actual_series.data = actual_data
actual_series.border_width = 3
actual_series.border_color = PAGE_BG

projected_series = HeatmapSeries()
projected_series.name = "Projected (IBNR)"
projected_series.data = projected_data
projected_series.border_width = 5
projected_series.border_color = ANYPLOT_AMBER

chart.add_series(actual_series)
chart.add_series(projected_series)

# Export
js_literal = chart.to_js_literal()

highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/heatmap.js"
headers = {"User-Agent": "Mozilla/5.0"}

req = urllib.request.Request(highcharts_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request(heatmap_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0;background:{PAGE_BG};">
    <div id="container" style="width:{W}px;height:{H}px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument(f"--window-size={W},{H}")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dimensions (belt-and-braces for CDP rounding)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (W, H):
    _norm = Image.new("RGB", (W, H), PAGE_BG)
    _norm.paste(_img, ((W - _img.size[0]) // 2, (H - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
