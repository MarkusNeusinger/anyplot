""" pyplots.ai
bar-race-animated: Animated Bar Chart Race
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

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
    "SmartSystems",
    "ByteForce",
    "NexGen",
    "CoreLogic",
]

years = [2019, 2020, 2021, 2022, 2023, 2024]

# Generate realistic market value evolution
base_values = np.array([180, 150, 120, 100, 90, 80, 70, 60, 50, 45, 40, 35])
data = []
for i, year in enumerate(years):
    growth = 1 + 0.15 * i + np.random.randn(len(companies)) * 0.2
    values = base_values * growth * (1 + np.random.randn(len(companies)) * 0.1)
    # Add some shuffling over time to make rankings change
    shuffle_factor = np.random.randn(len(companies)) * (20 + i * 10)
    values = values + shuffle_factor
    values = np.maximum(values, 10)  # Minimum value
    for j, company in enumerate(companies):
        data.append({"company": company, "year": year, "value": values[j]})

df = pd.DataFrame(data)

# Colors - consistent per company
colors = [
    "#306998",
    "#FFD43B",
    "#9467BD",
    "#17BECF",
    "#8C564B",
    "#E377C2",
    "#7F7F7F",
    "#BCBD22",
    "#1F77B4",
    "#FF7F0E",
    "#2CA02C",
    "#D62728",
]
company_colors = dict(zip(companies, colors, strict=False))

# Select 6 key time snapshots for small multiples grid (2x3)
snapshot_years = years

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate individual charts for each year
chart_scripts = []
for idx, year in enumerate(snapshot_years):
    year_data = df[df["year"] == year].sort_values("value", ascending=True).tail(10)

    chart = Chart(container=f"chart{idx}")
    chart.options = HighchartsOptions()

    chart.options.chart = {
        "type": "bar",
        "width": 1520,
        "height": 1280,
        "backgroundColor": "#ffffff",
        "marginLeft": 200,
        "marginRight": 50,
        "marginBottom": 80,
        "marginTop": 100,
    }

    chart.options.title = {"text": f"Year {year}", "style": {"fontSize": "32px", "fontWeight": "bold"}}

    chart.options.x_axis = {
        "categories": year_data["company"].tolist(),
        "title": {"text": None},
        "labels": {"style": {"fontSize": "20px"}},
    }

    chart.options.y_axis = {
        "title": {"text": "Market Value ($B)", "style": {"fontSize": "20px"}},
        "labels": {"style": {"fontSize": "18px"}},
        "min": 0,
        "max": 400,
    }

    chart.options.legend = {"enabled": False}

    chart.options.credits = {"enabled": False}

    # Create series with individual colors
    series = BarSeries()
    series.name = "Market Value"
    series.data = [
        {"y": float(row["value"]), "color": company_colors[row["company"]]} for _, row in year_data.iterrows()
    ]
    series.data_labels = {
        "enabled": True,
        "format": "${point.y:.0f}B",
        "style": {"fontSize": "16px", "fontWeight": "normal"},
    }

    chart.add_series(series)

    chart.options.plot_options = {"bar": {"borderWidth": 0, "pointWidth": 50}}

    chart_scripts.append(chart.to_js_literal())

# Create combined HTML with 2x3 grid
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        body {{
            margin: 0;
            padding: 40px;
            background: #ffffff;
            font-family: Arial, sans-serif;
        }}
        .main-title {{
            text-align: center;
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}
        .subtitle {{
            text-align: center;
            font-size: 28px;
            color: #666;
            margin-bottom: 40px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            grid-template-rows: repeat(2, 1fr);
            gap: 30px;
            width: 4720px;
            margin: 0 auto;
        }}
        .chart-container {{
            background: #fafafa;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        }}
    </style>
</head>
<body>
    <div class="main-title">bar-race-animated · highcharts · pyplots.ai</div>
    <div class="subtitle">Technology Companies Market Value Evolution (2019-2024)</div>
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

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save as plot.html for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(8)  # Wait for all charts to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
