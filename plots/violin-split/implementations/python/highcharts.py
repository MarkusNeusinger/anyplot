""" anyplot.ai
violin-split: Split Violin Plot
Library: highcharts unknown | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-08
"""

import os
import tempfile
import time
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series always #009E73)
BRAND = "#009E73"
ACCENT = "#C475FD"

# Data - Employee satisfaction scores by department, comparing Remote vs Office workers
np.random.seed(42)

categories = ["Engineering", "Marketing", "Sales", "HR"]
split_groups = ["Remote", "Office"]

# Generate realistic satisfaction data (1-10 scale)
data = {}
for cat in categories:
    data[cat] = {}
    if cat == "Engineering":
        data[cat]["Remote"] = np.random.normal(7.8, 0.9, 120)
        data[cat]["Office"] = np.random.normal(6.5, 1.3, 100)
    elif cat == "Marketing":
        data[cat]["Remote"] = np.random.normal(7.0, 1.1, 80)
        data[cat]["Office"] = np.random.normal(7.2, 1.0, 90)
    elif cat == "Sales":
        data[cat]["Remote"] = np.random.normal(6.2, 1.4, 90)
        data[cat]["Office"] = np.random.normal(7.5, 0.8, 110)
    else:  # HR
        data[cat]["Remote"] = np.random.normal(7.5, 1.0, 70)
        data[cat]["Office"] = np.random.normal(7.3, 1.2, 85)

# Clip to valid range
for cat in categories:
    for group in split_groups:
        data[cat][group] = np.clip(data[cat][group], 1, 10)

# Build series data for split violins
series_data = []
colors = {"Remote": BRAND, "Office": ACCENT}

# Track which groups have been added to legend
legend_added = {"Remote": False, "Office": False}

for i, cat in enumerate(categories):
    cat_x = i

    for group in split_groups:
        values = np.asarray(data[cat][group])
        n = len(values)
        std = np.std(values, ddof=1)
        bandwidth = 1.06 * std * n ** (-1 / 5)

        # KDE computation inline (Gaussian kernel)
        y_vals = np.linspace(min(values) - 0.5, max(values) + 0.5, 100)
        density = np.zeros(100)
        for v in values:
            density += np.exp(-0.5 * ((y_vals - v) / bandwidth) ** 2)
        density = density / (n * bandwidth * np.sqrt(2 * np.pi))
        density = density / density.max() * 0.35

        area_data = []
        if group == "Remote":
            for y, d in zip(y_vals, density, strict=True):
                area_data.append({"x": float(y), "low": float(cat_x - d), "high": float(cat_x)})
        else:
            for y, d in zip(y_vals, density, strict=True):
                area_data.append({"x": float(y), "low": float(cat_x), "high": float(cat_x + d)})

        show_in_legend = not legend_added[group]
        legend_added[group] = True

        series_data.append(
            {
                "type": "areasplinerange",
                "name": group,
                "showInLegend": show_in_legend,
                "data": area_data,
                "color": colors[group],
                "fillOpacity": 0.75,
                "lineWidth": 2,
                "lineColor": colors[group],
                "marker": {"enabled": False},
            }
        )

# Add median and quartile markers
stat_markers = []
for i, cat in enumerate(categories):
    for group in split_groups:
        values = data[cat][group]
        median_val = float(np.median(values))
        offset = -0.12 if group == "Remote" else 0.12
        x_pos = float(i + offset)

        # Add median marker (diamond)
        stat_markers.append({"x": median_val, "y": x_pos, "marker": {"symbol": "diamond", "radius": 16}})

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration - inverted for horizontal violins
chart.options.chart = {
    "type": "areasplinerange",
    "inverted": True,
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 320,
    "marginLeft": 350,
    "marginRight": 200,
    "marginTop": 150,
}

# Title
chart.options.title = {"text": "violin-split · highcharts · anyplot.ai", "style": {"fontSize": "28px", "color": INK}}

chart.options.subtitle = {
    "text": "Employee Satisfaction Scores: Remote vs Office Workers",
    "style": {"fontSize": "18px", "color": INK_SOFT},
}

# X-axis (vertical after inversion - shows satisfaction scores)
chart.options.x_axis = {
    "title": {"text": "Satisfaction Score", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 1,
    "max": 10,
    "reversed": False,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "tickInterval": 1,
}

# Y-axis (horizontal after inversion - shows categories)
chart.options.y_axis = {
    "title": {"text": "Department", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "categories": categories,
    "min": -0.5,
    "max": 3.5,
    "gridLineWidth": 0,
    "tickPositions": [0, 1, 2, 3],
    "showLastLabel": True,
    "showFirstLabel": True,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -80,
    "y": 150,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolHeight": 16,
    "symbolWidth": 16,
    "symbolRadius": 3,
}

# Tooltip
chart.options.tooltip = {
    "enabled": True,
    "style": {"fontSize": "16px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "headerFormat": "<b>{series.name}</b><br/>",
    "pointFormat": "Score: {point.x:.1f}",
}

# Plot options
chart.options.plot_options = {
    "areasplinerange": {"fillOpacity": 0.75, "lineWidth": 2, "states": {"hover": {"lineWidth": 3}}},
    "series": {"animation": False},
}

# Add all violin series
for s in series_data:
    chart.options.add_series(s)

# Add scatter series for median markers (diamond shape)
median_series = {
    "type": "scatter",
    "name": "Median",
    "showInLegend": False,
    "data": stat_markers,
    "marker": {"symbol": "diamond", "radius": 16, "fillColor": PAGE_BG, "lineColor": INK_SOFT, "lineWidth": 2},
    "enableMouseTracking": False,
}
chart.options.add_series(median_series)

# Load Highcharts JS from node_modules
script_dir = os.path.dirname(os.path.abspath(__file__))
highcharts_js_path = os.path.join(script_dir, "node_modules", "highcharts", "highcharts.js")
highcharts_more_js_path = os.path.join(
    script_dir, "node_modules", "highcharts", "highcharts-more.js"
)

with open(highcharts_js_path, "r", encoding="utf-8") as f:
    highcharts_js = f.read()

with open(highcharts_more_js_path, "r", encoding="utf-8") as f:
    highcharts_more_js = f.read()

# Generate HTML with inline scripts
html_str = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write the HTML file
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
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
