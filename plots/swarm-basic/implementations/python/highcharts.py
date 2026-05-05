"""anyplot.ai
swarm-basic: Basic Swarm Plot
Library: highcharts | Python 3.13
Quality: 91/100 | Updated: 2026-05-05
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"

# Okabe-Ito palette (positions 1-4)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data — employee performance scores by department
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "Operations"]

raw_data = {
    "Engineering": np.concatenate([np.random.normal(75, 8, 30), np.random.normal(90, 3, 10)]),
    "Marketing": np.random.normal(72, 12, 35),
    "Sales": np.concatenate([np.random.normal(68, 10, 25), np.random.normal(85, 5, 20)]),
    "Operations": np.random.normal(70, 7, 40),
}

for cat in categories:
    raw_data[cat] = np.clip(raw_data[cat], 40, 100)

# Compute beeswarm x-offsets inline for each category
swarm_by_cat = {}
for _, cat in enumerate(categories):
    values = raw_data[cat]
    sorted_indices = np.argsort(values)
    sorted_values = values[sorted_indices]
    x_positions = np.zeros(len(values))

    for i, (idx, val) in enumerate(zip(sorted_indices, sorted_values, strict=True)):
        nearby_mask = np.abs(sorted_values[:i] - val) < 2.5
        nearby_x = x_positions[sorted_indices[:i]][nearby_mask]
        x = 0.0
        if len(nearby_x) > 0:
            for offset in np.arange(0, 0.5, 0.12):
                for sign in [1, -1]:
                    test_x = sign * offset
                    if offset == 0 and sign == -1:
                        continue
                    if not any(abs(test_x - nx) < 0.12 for nx in nearby_x):
                        x = test_x
                        break
                else:
                    continue
                break
            else:
                x = max(abs(nx) for nx in nearby_x) + 0.12
                x = x if np.random.random() > 0.5 else -x
        x_positions[idx] = x

    swarm_by_cat[cat] = {"values": values, "x_offsets": x_positions}

means = {cat: float(np.mean(raw_data[cat])) for cat in categories}

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
}

chart.options.title = {
    "text": "swarm-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "Employee Performance Scores by Department",
    "style": {"fontSize": "48px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Department", "style": {"fontSize": "48px", "color": INK}},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "tickWidth": 0,
    "lineWidth": 2,
    "lineColor": INK_SOFT,
    "min": -0.5,
    "max": len(categories) - 0.5,
    "tickPositions": [0, 1, 2, 3],
}

chart.options.y_axis = {
    "title": {"text": "Performance Score", "style": {"fontSize": "48px", "color": INK}},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "min": 35,
    "max": 105,
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>{series.name}</b><br/>Score: {point.y:.1f}",
    "style": {"fontSize": "24px"},
}

# Scatter series per category
for cat_idx, cat in enumerate(categories):
    series = ScatterSeries()
    series.name = cat
    series.color = OKABE_ITO[cat_idx]
    cat_data = swarm_by_cat[cat]
    series.data = [
        {"x": float(cat_idx + x_off), "y": float(val)}
        for val, x_off in zip(cat_data["values"], cat_data["x_offsets"], strict=True)
    ]
    series.marker = {
        "radius": 14,
        "symbol": "circle",
        "fillColor": OKABE_ITO[cat_idx],
        "lineWidth": 2,
        "lineColor": PAGE_BG,
    }
    chart.add_series(series)

# Mean markers using adaptive neutral (Okabe-Ito position 8)
mean_series = ScatterSeries()
mean_series.name = "Mean"
mean_series.data = [{"x": float(i), "y": means[cat]} for i, cat in enumerate(categories)]
mean_series.marker = {"radius": 20, "symbol": "diamond", "fillColor": NEUTRAL, "lineWidth": 3, "lineColor": PAGE_BG}
mean_series.color = NEUTRAL
chart.add_series(mean_series)

# Download Highcharts JS (required for headless Chrome — CDN blocked from file://)
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
