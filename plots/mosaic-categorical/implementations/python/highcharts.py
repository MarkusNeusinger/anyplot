""" anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-19
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first series always #009E73
PALETTE = ["#009E73", "#D55E00", "#0072B2"]

# Data — Physical activity level by age group (population health survey)
np.random.seed(42)
age_groups = ["Young (18–35)", "Middle (36–55)", "Senior (56+)"]
activity_levels = ["Active", "Moderate", "Sedentary"]
counts = [
    [450, 300, 150],  # Young
    [250, 400, 350],  # Middle
    [100, 250, 450],  # Senior
]

# Build hierarchical treemap data (mosaic layout)
treemap_data = []
for i, age in enumerate(age_groups):
    treemap_data.append({"id": age, "name": age})
    for j, activity in enumerate(activity_levels):
        treemap_data.append({"parent": age, "name": activity, "value": counts[i][j], "color": PALETTE[j]})

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "treemap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginTop": 220,
    "marginBottom": 80,
    "marginLeft": 60,
    "marginRight": 60,
}

chart.options.title = {
    "text": "mosaic-categorical · python · highcharts · anyplot.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold", "color": INK},
    "y": 70,
}

chart.options.subtitle = {
    "text": "Physical Activity Level by Age Group · column width ∝ group size · height ∝ activity share",
    "style": {"fontSize": "34px", "color": INK_SOFT},
    "y": 140,
}

chart.options.tooltip = {
    "style": {"fontSize": "30px"},
    "pointFormat": "<b>{point.name}</b>: {point.value:,.0f} respondents",
}

# Stripes layout with vertical starting direction creates proper mosaic columns:
# level-1 nodes form side-by-side columns (widths ∝ marginal proportions)
# level-2 nodes stack within each column (heights ∝ conditional proportions)
series_config = {
    "type": "treemap",
    "name": "Respondents",
    "layoutAlgorithm": "stripes",
    "layoutStartingDirection": "vertical",
    "alternateStartingDirection": True,
    "animationLimit": 1000,
    "levels": [
        {
            "level": 1,
            "dataLabels": {
                "enabled": True,
                "align": "center",
                "verticalAlign": "top",
                "style": {"fontSize": "44px", "fontWeight": "bold", "textOutline": "3px contrast"},
            },
            "borderWidth": 8,
            "borderColor": PAGE_BG,
        },
        {
            "level": 2,
            "dataLabels": {
                "enabled": True,
                "style": {"fontSize": "32px", "fontWeight": "bold", "textOutline": "2px contrast"},
            },
            "borderWidth": 3,
            "borderColor": PAGE_BG,
        },
    ],
    "data": treemap_data,
}

chart.options.series = [series_config]
chart.options.legend = {"enabled": False}

# Download required JS (inline for headless Chrome file:// compatibility)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@12/highcharts.js"
treemap_url = "https://cdn.jsdelivr.net/npm/highcharts@12/modules/treemap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(treemap_url, timeout=30) as response:
    treemap_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{treemap_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot for PNG artifact (theme-suffixed)
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot_temp.png")
driver.quit()

# Crop to exact 4800×2700 dimensions
img = Image.open("plot_temp.png")
img.crop((0, 0, 4800, 2700)).save(f"plot-{THEME}.png")
Path("plot_temp.png").unlink()

Path(temp_path).unlink()
