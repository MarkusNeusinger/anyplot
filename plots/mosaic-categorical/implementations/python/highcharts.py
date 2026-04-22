""" pyplots.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
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
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Titanic survival by passenger class (classic contingency table example)
np.random.seed(42)

# Create contingency table data: Class vs Survival
# Realistic proportions based on Titanic data patterns
data = {
    "Class": ["First", "First", "Second", "Second", "Third", "Third", "Crew", "Crew"],
    "Survival": ["Survived", "Died", "Survived", "Died", "Survived", "Died", "Survived", "Died"],
    "Count": [203, 122, 118, 167, 178, 528, 212, 673],
}
df = pd.DataFrame(data)

# Calculate proportions for mosaic plot
total = df["Count"].sum()
class_totals = df.groupby("Class")["Count"].sum()

# Build hierarchical data for treemap (mosaic-like visualization)
# Parent nodes represent categories, children represent survival status
treemap_data = []

# Color palette - colorblind-safe
colors = {
    "Survived": "#306998",  # Python Blue
    "Died": "#FFD43B",  # Python Yellow
}

# Define order for consistent layout
class_order = ["First", "Second", "Third", "Crew"]

for cls in class_order:
    cls_data = df[df["Class"] == cls]
    cls_total = class_totals[cls]

    # Add parent node for class
    treemap_data.append({"id": cls, "name": cls})

    # Add child nodes for each survival status
    for _, row in cls_data.iterrows():
        treemap_data.append(
            {"parent": cls, "name": f"{row['Survival']}", "value": int(row["Count"]), "color": colors[row["Survival"]]}
        )

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration - optimized margins for better canvas utilization
chart.options.chart = {
    "type": "treemap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginTop": 200,
    "marginBottom": 60,
    "marginLeft": 40,
    "marginRight": 40,
}

# Title - required format without extra descriptive text
chart.options.title = {
    "text": "mosaic-categorical · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
    "y": 70,
}

# Subtitle with Titanic context and legend explanation
chart.options.subtitle = {
    "text": "Titanic Survival by Passenger Class · Rectangle area proportional to count · "
    "<span style='color:#306998'>■</span> Survived · "
    "<span style='color:#FFD43B'>■</span> Died",
    "style": {"fontSize": "42px", "color": "#555555"},
    "useHTML": True,
    "y": 140,
}

# Tooltip
chart.options.tooltip = {
    "style": {"fontSize": "36px"},
    "pointFormat": "<b>{point.name}</b>: {point.value:,.0f} passengers",
}

# Treemap series configuration - stripes layout for mosaic effect
series_config = {
    "type": "treemap",
    "name": "Passengers",
    "layoutAlgorithm": "stripes",
    "layoutStartingDirection": "horizontal",
    "alternateStartingDirection": True,
    "animationLimit": 1000,
    "dataLabels": {"enabled": True, "style": {"fontSize": "32px", "fontWeight": "bold", "textOutline": "3px contrast"}},
    "levels": [
        {
            "level": 1,
            "dataLabels": {
                "enabled": True,
                "align": "center",
                "verticalAlign": "top",
                "style": {"fontSize": "48px", "fontWeight": "bold", "textOutline": "3px contrast"},
                "padding": 20,
            },
            "borderWidth": 6,
            "borderColor": "#ffffff",
        },
        {
            "level": 2,
            "dataLabels": {
                "enabled": True,
                "style": {"fontSize": "36px", "fontWeight": "bold", "textOutline": "2px contrast"},
            },
            "borderWidth": 3,
            "borderColor": "#ffffff",
        },
    ],
    "data": treemap_data,
}

chart.options.series = [series_config]

# Legend configuration - manual items for Survived/Died colors
chart.options.legend = {"enabled": False}

# Download Highcharts JS and treemap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
treemap_url = "https://code.highcharts.com/modules/treemap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(treemap_url, timeout=30) as response:
    treemap_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{treemap_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/treemap.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(standalone_html)

# Write temp HTML and take screenshot
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot_temp.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_temp.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_temp.png").unlink()

Path(temp_path).unlink()  # Clean up temp file
