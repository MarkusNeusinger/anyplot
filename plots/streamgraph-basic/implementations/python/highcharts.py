""" anyplot.ai
streamgraph-basic: Basic Stream Graph
Library: highcharts unknown | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-05
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import StreamGraphSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Data - Monthly streaming hours by music genre over two years
np.random.seed(42)
months = np.arange(24)
month_labels = [
    "Jan '23",
    "Feb '23",
    "Mar '23",
    "Apr '23",
    "May '23",
    "Jun '23",
    "Jul '23",
    "Aug '23",
    "Sep '23",
    "Oct '23",
    "Nov '23",
    "Dec '23",
    "Jan '24",
    "Feb '24",
    "Mar '24",
    "Apr '24",
    "May '24",
    "Jun '24",
    "Jul '24",
    "Aug '24",
    "Sep '24",
    "Oct '24",
    "Nov '24",
    "Dec '24",
]

genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz"]

genre_data = {}
genre_data["Pop"] = 4000 + 200 * np.sin(2 * np.pi * months / 12) + np.random.normal(0, 200, 24)
genre_data["Rock"] = 2500 - months * 30 + 150 * np.sin(2 * np.pi * months / 6) + np.random.normal(0, 150, 24)
genre_data["Hip-Hop"] = 2000 + months * 80 + 100 * np.sin(2 * np.pi * months / 4) + np.random.normal(0, 180, 24)
genre_data["Electronic"] = 1800 + 300 * np.sin(2 * np.pi * months / 12 + np.pi) + np.random.normal(0, 120, 24)
genre_data["Jazz"] = 1200 + 50 * np.sin(2 * np.pi * months / 8) + np.random.normal(0, 80, 24)

for genre in genres:
    genre_data[genre] = np.clip(genre_data[genre], 300, None)

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "streamgraph",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 220,
    "marginLeft": 180,
    "marginRight": 100,
    "style": {"color": INK},
}

chart.options.title = {
    "text": "Music Streaming Trends · streamgraph-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "Monthly streaming hours by genre (2023–2024)",
    "style": {"fontSize": "32px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "categories": month_labels,
    "title": {"text": "Month", "style": {"fontSize": "24px", "color": INK}},
    "labels": {"style": {"fontSize": "22px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.y_axis = {"visible": False, "startOnTick": False, "endOnTick": False}

chart.options.plot_options = {"streamgraph": {"fillOpacity": 0.85, "lineWidth": 0, "marker": {"enabled": False}}}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "itemStyle": {"fontSize": "28px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolWidth": 40,
    "symbolHeight": 20,
    "symbolRadius": 6,
    "y": 20,
}

chart.options.colors = OKABE_ITO

for genre in genres:
    series = StreamGraphSeries()
    series.data = [float(v) for v in genre_data[genre]]
    series.name = genre
    chart.add_series(series)

# Download Highcharts JS modules for inline embedding
_HC_URLS = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
_SG_URLS = [
    "https://code.highcharts.com/modules/streamgraph.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/modules/streamgraph.js",
]

highcharts_js = None
for url in _HC_URLS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS")

streamgraph_js = None
for url in _SG_URLS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            streamgraph_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if streamgraph_js is None:
    raise RuntimeError("Failed to download Highcharts streamgraph module")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{streamgraph_js}</script>
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
