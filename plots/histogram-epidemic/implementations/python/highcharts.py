""" anyplot.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-02
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
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.options.series.spline import SplineSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint categorical palette (hybrid-v3 sort order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — simulated respiratory illness outbreak over ~90 days
np.random.seed(42)

start_date = pd.Timestamp("2024-01-15")
dates = pd.date_range(start_date, periods=90, freq="D")

# Point-source wave peaking ~day 20, then propagated wave peaking ~day 55
t = np.arange(90)
wave1_rate = 35 * np.exp(-0.5 * ((t - 20) / 6) ** 2)
wave2_rate = 55 * np.exp(-0.5 * ((t - 55) / 10) ** 2)
combined_rate = wave1_rate + wave2_rate + 2

confirmed_cases = np.random.poisson(combined_rate * 0.6).astype(int)
probable_cases = np.random.poisson(combined_rate * 0.25).astype(int)
suspect_cases = np.random.poisson(combined_rate * 0.15).astype(int)

cumulative = np.cumsum(confirmed_cases + probable_cases + suspect_cases)
date_labels = [d.strftime("%b %d") for d in dates]

# Chart — title fontsize scales with length (baseline 67 chars → 66px)
title = "histogram-epidemic · python · highcharts · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = f"{max(44, round(66 * ratio))}px"

chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "column",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 240,
    "marginLeft": 150,
    "marginRight": 180,
    "marginTop": 150,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif", "color": INK},
}

chart.options.title = {
    "text": title,
    "style": {"fontSize": title_fontsize, "fontWeight": "700", "color": INK},
    "margin": 16,
}

chart.options.subtitle = {
    "text": "Respiratory Illness Outbreak — Daily new cases by classification, Jan–Apr 2024",
    "style": {"fontSize": "40px", "color": INK_SOFT, "fontWeight": "400"},
}

# X-axis — date categories with intervention plot lines
chart.options.x_axis = {
    "categories": date_labels,
    "title": {
        "text": "Symptom Onset Date",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "600"},
        "margin": 16,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "step": 7},
    "tickInterval": 7,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "plotLines": [
        {
            "value": 25,
            "color": IMPRINT_PALETTE[4],  # matte red — restrictive alert event
            "width": 4,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": "Travel Advisory Issued",
                "style": {"fontSize": "36px", "color": IMPRINT_PALETTE[4], "fontWeight": "600"},
                "rotation": 0,
                "align": "left",
                "x": 10,
                "y": 50,
            },
        },
        {
            "value": 42,
            "color": IMPRINT_PALETTE[7],  # lime — positive health intervention
            "width": 4,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": "Vaccination Campaign",
                "style": {"fontSize": "36px", "color": IMPRINT_PALETTE[7], "fontWeight": "600"},
                "rotation": 0,
                "align": "left",
                "x": 10,
                "y": 80,
            },
        },
    ],
}

# Y-axes — primary for daily case counts, secondary for cumulative total
chart.options.y_axis = [
    {
        "title": {
            "text": "Daily New Cases",
            "style": {"fontSize": "56px", "color": INK, "fontWeight": "600"},
            "margin": 16,
        },
        "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
        "min": 0,
        "endOnTick": False,
        "tickInterval": 15,
        "gridLineColor": GRID,
        "gridLineWidth": 1,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    },
    {
        "title": {
            "text": "Cumulative Cases",
            "style": {"fontSize": "56px", "color": INK_MUTED, "fontWeight": "600"},
            "margin": 16,
        },
        "labels": {"style": {"fontSize": "44px", "color": INK_MUTED}},
        "opposite": True,
        "min": 0,
        "gridLineWidth": 0,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    },
]

chart.options.tooltip = {
    "shared": True,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "style": {"fontSize": "36px", "color": INK},
    "headerFormat": '<span style="font-size:38px;font-weight:600">{point.key}</span><br/>',
    "pointFormat": '<span style="color:{series.color}">●</span> {series.name}: <b>{point.y}</b><br/>',
}

chart.options.plot_options = {
    "column": {"stacking": "normal", "pointPadding": 0, "groupPadding": 0.02, "borderWidth": 0, "shadow": False},
    "spline": {"lineWidth": 5, "marker": {"enabled": False}},
    "series": {"animation": False},
}

chart.options.legend = {
    "enabled": True,
    "align": "left",
    "verticalAlign": "bottom",
    "floating": False,
    "itemStyle": {"fontSize": "44px", "fontWeight": "500", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolRadius": 4,
    "symbolHeight": 20,
    "symbolWidth": 20,
}

chart.options.credits = {"enabled": False}

# Stacked column series by case classification — Imprint palette positions 1, 2, 3
confirmed_series = ColumnSeries()
confirmed_series.name = "Confirmed"
confirmed_series.data = [int(v) for v in confirmed_cases]
confirmed_series.color = IMPRINT_PALETTE[0]  # #009E73 brand green — ALWAYS first series

probable_series = ColumnSeries()
probable_series.name = "Probable"
probable_series.data = [int(v) for v in probable_cases]
probable_series.color = IMPRINT_PALETTE[1]  # #C475FD lavender

suspect_series = ColumnSeries()
suspect_series.name = "Suspect"
suspect_series.data = [int(v) for v in suspect_cases]
suspect_series.color = IMPRINT_PALETTE[2]  # #4467A3 blue

chart.add_series(confirmed_series)
chart.add_series(probable_series)
chart.add_series(suspect_series)

# Cumulative line overlay — neutral/muted anchor (reference/structural layer)
cumulative_series = SplineSeries()
cumulative_series.name = "Cumulative Total"
cumulative_series.data = [int(v) for v in cumulative]
cumulative_series.color = INK_MUTED
cumulative_series.y_axis = 1
cumulative_series.dash_style = "ShortDash"

chart.add_series(cumulative_series)

# Download Highcharts JS — inline embed required for headless Chrome (no CDN from file://)
highcharts_js = None
cdn_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
for url in cdn_urls:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
            break
        except Exception:
            time.sleep(2 * (attempt + 1))
    if highcharts_js:
        break

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
# CDP override is authoritative — --window-size alone loses ~139 px to Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 3200×1800 — guards against ±1–2 px rounding from headless Chrome
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
