""" anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: highcharts unknown | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-20
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.options.series.spline import SplineSeries
from PIL import Image
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette positions
BRAND = "#009E73"  # position 1 — main histogram bars
COLOR_2 = "#C475FD"  # position 2 — tail regions
COLOR_3 = "#4467A3"  # position 3 — normal distribution curve

# Data
np.random.seed(42)
n_days = 252
daily_returns = np.random.normal(loc=0.05, scale=1.2, size=n_days)

# Statistics
mean_return = np.mean(daily_returns)
std_return = np.std(daily_returns)
skewness = stats.skew(daily_returns)
kurtosis = stats.kurtosis(daily_returns)

# Histogram bins
n_bins = 30
hist_counts, bin_edges = np.histogram(daily_returns, bins=n_bins, density=True)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Normal distribution overlay
x_norm = np.linspace(daily_returns.min() - 0.5, daily_returns.max() + 0.5, 100)
y_norm = stats.norm.pdf(x_norm, mean_return, std_return)

# Split histogram into central and tail regions (beyond 2σ)
lower_tail = mean_return - 2 * std_return
upper_tail = mean_return + 2 * std_return
histogram_data = []
tail_data = []
for center, count in zip(bin_centers, hist_counts, strict=True):
    if center < lower_tail or center > upper_tail:
        tail_data.append({"x": float(center), "y": float(count)})
        histogram_data.append({"x": float(center), "y": 0})
    else:
        histogram_data.append({"x": float(center), "y": float(count)})
        tail_data.append({"x": float(center), "y": 0})

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "column",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 180,
    "marginLeft": 180,
    "marginRight": 180,
    "marginTop": 130,
    "style": {"color": INK},
}

chart.options.title = {
    "text": "histogram-returns-distribution · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
}

stats_text = (
    f"Mean: {mean_return:.2f}% | Std Dev: {std_return:.2f}% | Skewness: {skewness:.2f} | Kurtosis: {kurtosis:.2f}"
)
chart.options.subtitle = {"text": stats_text, "style": {"fontSize": "40px", "color": INK_SOFT}}

chart.options.x_axis = {
    "title": {"text": "Daily Returns (%)", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 0,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.y_axis = {
    "title": {"text": "Density", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"color": INK_SOFT, "fontSize": "44px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 120,
}

chart.options.plot_options = {
    "column": {"pointPadding": 0, "groupPadding": 0, "borderWidth": 1, "borderColor": PAGE_BG},
    "spline": {"lineWidth": 7, "marker": {"enabled": False}},
}

chart.options.credits = {"enabled": False}

# Histogram bar width: plot area ≈ 3200 - 180 - 180 = 2840 px across 30 bins
point_px = int(2840 / n_bins * 0.85)

main_series = ColumnSeries()
main_series.name = "Returns Distribution"
main_series.data = histogram_data
main_series.color = BRAND
main_series.point_width = point_px
chart.add_series(main_series)

tail_series = ColumnSeries()
tail_series.name = "Tail Regions (>2σ)"
tail_series.data = tail_data
tail_series.color = COLOR_2
tail_series.point_width = point_px
chart.add_series(tail_series)

normal_series = SplineSeries()
normal_series.name = "Normal Distribution"
normal_series.data = [[float(x), float(y)] for x, y in zip(x_norm, y_norm, strict=True)]
normal_series.color = COLOR_3
normal_series.line_width = 7
normal_series.marker = {"enabled": False}
chart.add_series(normal_series)

# Download Highcharts JS for inline embedding (CDN blocked in headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact (theme-suffixed)
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin saved PNG to exact 3200×1800 (safety net for ±1–2 px Chrome rounding)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
