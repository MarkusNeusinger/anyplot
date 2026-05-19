"""anyplot.ai
bar-race-animated: Animated Bar Chart Race
Library: highcharts | Python 3.13
Quality: 91/100 | Created: 2026-01-11
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
from highcharts_core.options.series.bar import BarSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (positions 1–7) + adaptive neutral for 8 entities
OI_COLORS = [
    "#009E73",  # position 1: bluish green
    "#D55E00",  # position 2: vermillion
    "#0072B2",  # position 3: blue
    "#CC79A7",  # position 4: reddish purple
    "#E69F00",  # position 5: orange
    "#56B4E9",  # position 6: sky blue
    "#F0E442",  # position 7: yellow
    "#1A1A1A" if THEME == "light" else "#E8E8E0",  # position 8: adaptive neutral
]

# Data - Global Technology Companies Market Value (in $B) 2019-2024
np.random.seed(42)

companies = [
    "TechCorp Alpha",
    "DataSphere",
    "CloudNine",
    "InnovateTech",
    "CyberCore",
    "QuantumByte",
    "NetPrime",
    "DigiWave",
]

years = [2019, 2020, 2021, 2022, 2023, 2024]

base_values = np.array([180, 150, 120, 100, 90, 80, 70, 60])
data = []
for i, year in enumerate(years):
    growth = 1 + 0.15 * i + np.random.randn(len(companies)) * 0.2
    values = base_values * growth * (1 + np.random.randn(len(companies)) * 0.1)
    shuffle_factor = np.random.randn(len(companies)) * (20 + i * 10)
    values = values + shuffle_factor
    values = np.maximum(values, 10)
    for j, company in enumerate(companies):
        data.append({"company": company, "year": year, "value": values[j]})

df = pd.DataFrame(data)
company_colors = dict(zip(companies, OI_COLORS, strict=True))

# Download Highcharts JS
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@12/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=60) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate individual charts for each year snapshot
CHART_W = 1550
CHART_H = 1150
max_val = df["value"].max() * 1.1

chart_scripts = []
for idx, year in enumerate(years):
    year_data = df[df["year"] == year].sort_values("value", ascending=True)

    chart = Chart(container=f"chart{idx}")
    chart.options = HighchartsOptions()

    chart.options.chart = {
        "type": "bar",
        "width": CHART_W,
        "height": CHART_H,
        "backgroundColor": ELEVATED_BG,
        "marginLeft": 230,
        "marginRight": 110,
        "marginBottom": 80,
        "marginTop": 80,
    }

    chart.options.title = {"text": str(year), "style": {"fontSize": "38px", "fontWeight": "bold", "color": INK}}

    chart.options.x_axis = {
        "categories": year_data["company"].tolist(),
        "title": {"text": None},
        "labels": {"style": {"fontSize": "22px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    }

    chart.options.y_axis = {
        "title": {"text": "Market Value ($B)", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "min": 0,
        "max": max_val,
        "gridLineColor": GRID,
    }

    chart.options.legend = {"enabled": False}
    chart.options.credits = {"enabled": False}

    series = BarSeries()
    series.name = "Market Value"
    series.data = [
        {"y": float(row["value"]), "color": company_colors[row["company"]]} for _, row in year_data.iterrows()
    ]
    series.data_labels = {
        "enabled": True,
        "format": "${point.y:.0f}B",
        "style": {"fontSize": "19px", "fontWeight": "normal", "color": INK, "textOutline": "none"},
    }
    chart.add_series(series)

    chart.options.plot_options = {"bar": {"borderWidth": 0, "pointWidth": 58}}

    chart_scripts.append(chart.to_js_literal())

# Assemble full-page HTML with 2×3 small-multiples grid
GRID_GAP = 28
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        body {{
            margin: 0;
            padding: 40px;
            background: {PAGE_BG};
            font-family: Arial, sans-serif;
        }}
        .main-title {{
            text-align: center;
            font-size: 52px;
            font-weight: bold;
            margin-bottom: 8px;
            color: {INK};
        }}
        .subtitle {{
            text-align: center;
            font-size: 30px;
            color: {INK_MUTED};
            margin-bottom: 36px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(3, {CHART_W}px);
            grid-template-rows: repeat(2, {CHART_H}px);
            gap: {GRID_GAP}px;
            width: {3 * CHART_W + 2 * GRID_GAP}px;
            margin: 0 auto;
        }}
        .chart-container {{
            background: {ELEVATED_BG};
            border-radius: 8px;
            overflow: hidden;
        }}
    </style>
</head>
<body>
    <div class="main-title">bar-race-animated · python · highcharts · anyplot.ai</div>
    <div class="subtitle">Technology Companies Market Value Evolution (2019–2024)</div>
    <div class="grid">
        <div class="chart-container"><div id="chart0"></div></div>
        <div class="chart-container"><div id="chart1"></div></div>
        <div class="chart-container"><div id="chart2"></div></div>
        <div class="chart-container"><div id="chart3"></div></div>
        <div class="chart-container"><div id="chart4"></div></div>
        <div class="chart-container"><div id="chart5"></div></div>
    </div>
    <script>
        {chart_scripts[0]}
        {chart_scripts[1]}
        {chart_scripts[2]}
        {chart_scripts[3]}
        {chart_scripts[4]}
        {chart_scripts[5]}
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome
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
time.sleep(8)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
