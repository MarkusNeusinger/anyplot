"""anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: highcharts unknown | Python 3.13.13
Quality: 84/100 | Created: 2026-05-23
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
from highcharts_core.options.series.area import LineSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

ANYPLOT_PALETTE = ["#009E73", "#9418DB", "#B71D27", "#16B8F3", "#99B314", "#D359A7", "#BA843E"]

# Data — synthetic semiconductor sector vs S&P 500, 2024 (252 trading days)
np.random.seed(42)

trading_days = pd.date_range("2024-01-02", periods=252, freq="B")

stocks = {
    "NVDA": {"mu": 0.0012, "sigma": 0.032},
    "AMD": {"mu": 0.0003, "sigma": 0.028},
    "INTC": {"mu": -0.0006, "sigma": 0.022},
    "SPY": {"mu": 0.0004, "sigma": 0.010},
}

prices = {}
for sym, params in stocks.items():
    daily_returns = np.random.normal(params["mu"], params["sigma"], len(trading_days) - 1)
    daily_returns = np.insert(daily_returns, 0, 0.0)
    prices[sym] = 100.0 * np.cumprod(1 + daily_returns)

dates_ms = [int(d.timestamp() * 1000) for d in trading_days]

# Find NVDA peak for annotation
nvda_peak_idx = int(np.argmax(prices["NVDA"]))
nvda_peak_date_ms = dates_ms[nvda_peak_idx]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
    "marginBottom": 120,
    "marginLeft": 140,
    "plotBorderWidth": 0,
}

chart.options.title = {
    "text": "Tech Sector 2024 · line-stock-comparison · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "color": INK, "fontWeight": "bold"},
}

chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "tickInterval": 30 * 24 * 3600 * 1000,
    "plotLines": [
        {
            "value": nvda_peak_date_ms,
            "color": "#009E73",
            "dashStyle": "ShortDash",
            "width": 2,
            "label": {"text": "NVDA Peak", "style": {"color": "#009E73", "fontSize": "36px"}, "rotation": 0, "y": 20},
            "zIndex": 3,
        }
    ],
}

chart.options.y_axis = {
    "title": {"text": "Rebased Performance (Start = 100)", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "plotLines": [
        {
            "value": 100,
            "color": INK_SOFT,
            "dashStyle": "Dash",
            "width": 2,
            "label": {
                "text": "Baseline (100)",
                "style": {"color": INK_SOFT, "fontSize": "36px"},
                "align": "right",
                "x": -8,
            },
            "zIndex": 4,
        }
    ],
}

chart.options.legend = {
    "itemStyle": {"color": INK_SOFT, "fontSize": "44px"},
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 0,
}

chart.options.plot_options = {"line": {"lineWidth": 3.5, "marker": {"enabled": False}}}

chart.options.colors = ANYPLOT_PALETTE

for symbol, price_data in prices.items():
    series = LineSeries()
    series.name = symbol
    series.data = [[dates_ms[i], float(price_data[i])] for i in range(len(dates_ms))]
    chart.add_series(series)

# Export HTML + PNG
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
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

_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
