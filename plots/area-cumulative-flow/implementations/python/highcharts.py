""" anyplot.ai
area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
Library: highcharts unknown | Python 3.13.13
Quality: 79/100 | Created: 2026-05-07
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — 90-day Kanban board with 5 workflow stages
np.random.seed(42)
n_days = 90
dates = pd.date_range("2024-01-15", periods=n_days, freq="D")

# Total items entered the system (monotonically increasing top boundary)
total_entered = np.cumsum(np.random.poisson(4, n_days)) + 20

# Build cumulative lines as fractions of total_entered (bottom → top: Done → Backlog)
done_frac = np.linspace(0.0, 0.78, n_days) + np.random.normal(0, 0.02, n_days)
done_frac = np.clip(done_frac, 0, 0.96)
done_frac = np.maximum.accumulate(done_frac)

testing_frac = np.linspace(0.05, 0.86, n_days) + np.random.normal(0, 0.02, n_days)
testing_frac = np.clip(testing_frac, done_frac, 0.97)
testing_frac = np.maximum.accumulate(testing_frac)

dev_frac = np.linspace(0.12, 0.92, n_days) + np.random.normal(0, 0.02, n_days)
dev_frac = np.clip(dev_frac, testing_frac, 0.98)
dev_frac = np.maximum.accumulate(dev_frac)

analysis_frac = np.linspace(0.18, 0.96, n_days) + np.random.normal(0, 0.02, n_days)
analysis_frac = np.clip(analysis_frac, dev_frac, 1.0)
analysis_frac = np.maximum.accumulate(analysis_frac)

done_cumulative = (done_frac * total_entered).astype(int)
testing_cumulative = (testing_frac * total_entered).astype(int)
dev_cumulative = (dev_frac * total_entered).astype(int)
analysis_cumulative = (analysis_frac * total_entered).astype(int)

# Band heights = WIP count in each stage
done_band = done_cumulative.tolist()
testing_band = (testing_cumulative - done_cumulative).tolist()
dev_band = (dev_cumulative - testing_cumulative).tolist()
analysis_band = (analysis_cumulative - dev_cumulative).tolist()
backlog_band = (total_entered - analysis_cumulative).tolist()

date_labels = [d.strftime("%b %d") for d in dates]

# Plot
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
    "marginBottom": 160,
    "marginLeft": 180,
    "marginRight": 80,
    "marginTop": 120,
}

chart.options.title = {
    "text": "area-cumulative-flow · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "600"},
    "margin": 40,
}

chart.options.x_axis = {
    "categories": date_labels,
    "tickInterval": 15,
    "title": {"text": "Date", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

chart.options.y_axis = {
    "title": {"text": "Cumulative Items", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineColor": GRID,
    "min": 0,
}

chart.options.plot_options = {
    "area": {"stacking": "normal", "lineWidth": 2, "fillOpacity": 0.85, "marker": {"enabled": False}}
}

chart.options.legend = {
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT, "fontWeight": "normal"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
}

chart.options.tooltip = {
    "shared": True,
    "style": {"fontSize": "16px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
}

# Highcharts reversedStacks=true (default): first added series = visual TOP.
# Add top→bottom so Done (green #009E73) is at the bottom and Backlog at the top.
stages = [
    ("Backlog", backlog_band, IMPRINT[4]),
    ("Analysis", analysis_band, IMPRINT[3]),
    ("Development", dev_band, IMPRINT[2]),
    ("Testing", testing_band, IMPRINT[1]),
    ("Done", done_band, IMPRINT[0]),
]

for name, data, color in stages:
    series = AreaSeries()
    series.name = name
    series.data = data
    series.color = color
    chart.add_series(series)


# Download Highcharts JS for inline embedding (headless Chrome blocks CDN)
def download_js(path, timeout=15):
    cdn_bases = [
        "https://cdn.jsdelivr.net/npm/highcharts@11/",
        "https://unpkg.com/highcharts@11/",
        "https://code.highcharts.com/",
    ]
    for base in cdn_bases:
        url = base + path
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.read().decode("utf-8")
            except Exception:
                if attempt == 0:
                    time.sleep(1)
    return None


highcharts_js = download_js("highcharts.js")
if highcharts_js is None:
    raise RuntimeError("Failed to download highcharts.js from all CDNs")

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
