""" pyplots.ai
bar-feature-importance: Feature Importance Bar Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Data - Feature importances from a Random Forest classifier (house price prediction)
features = [
    "Square Footage",
    "Number of Bedrooms",
    "Location Score",
    "Year Built",
    "Lot Size",
    "Number of Bathrooms",
    "Garage Capacity",
    "School District Rating",
    "Distance to City Center",
    "Property Tax Rate",
    "HOA Fees",
    "Neighborhood Crime Rate",
    "Nearby Amenities Count",
    "Public Transit Access",
    "Energy Efficiency Score",
]

# Importance scores (from ensemble averaging)
importance = [0.215, 0.142, 0.128, 0.089, 0.078, 0.068, 0.062, 0.055, 0.048, 0.041, 0.028, 0.019, 0.014, 0.009, 0.004]

# Sort by importance (already sorted, but make explicit)
sorted_data = sorted(zip(features, importance, strict=True), key=lambda x: x[1], reverse=True)
features_sorted = [x[0] for x in sorted_data]
importance_sorted = [x[1] for x in sorted_data]

# Reverse for horizontal bar chart (highest importance at top in Highcharts bar)
features_sorted = features_sorted[::-1]
importance_sorted = importance_sorted[::-1]

# Create gradient colors based on importance (light to dark blue)
max_imp = max(importance_sorted)
min_imp = min(importance_sorted)


def importance_to_color(imp):
    """Map importance to color from light (#a8d5f2) to dark (#306998)."""
    ratio = (imp - min_imp) / (max_imp - min_imp) if max_imp != min_imp else 0.5
    r = int(168 + (48 - 168) * ratio)
    g = int(213 + (105 - 213) * ratio)
    b = int(242 + (152 - 242) * ratio)
    return f"#{r:02x}{g:02x}{b:02x}"


# Build data with colors
bar_data = []
for imp in importance_sorted:
    bar_data.append({"y": imp, "color": importance_to_color(imp)})

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build chart options as a dictionary
chart_options = {
    "chart": {
        "type": "bar",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginLeft": 380,
        "marginRight": 180,
        "marginTop": 150,
        "marginBottom": 120,
        "animation": False,
    },
    "title": {
        "text": "bar-feature-importance \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "bold"},
    },
    "subtitle": {
        "text": "House Price Prediction - Random Forest Feature Importances",
        "style": {"fontSize": "32px", "color": "#666666"},
    },
    "xAxis": {
        "categories": features_sorted,
        "title": {"text": None},
        "labels": {"style": {"fontSize": "26px"}},
        "lineWidth": 0,
        "tickWidth": 0,
    },
    "yAxis": {
        "title": {"text": "Importance Score", "style": {"fontSize": "32px"}},
        "labels": {"style": {"fontSize": "24px"}},
        "min": 0,
        "max": 0.25,
        "gridLineWidth": 1,
        "gridLineColor": "#e0e0e0",
    },
    "legend": {"enabled": False},
    "tooltip": {"enabled": False},
    "plotOptions": {
        "bar": {
            "dataLabels": {
                "enabled": True,
                "format": "{point.y:.3f}",
                "style": {"fontSize": "22px", "fontWeight": "normal", "textOutline": "none"},
                "align": "left",
                "x": 10,
            },
            "pointPadding": 0.1,
            "groupPadding": 0.05,
            "borderWidth": 0,
            "animation": False,
        }
    },
    "credits": {"enabled": False},
    "series": [{"name": "Feature Importance", "data": bar_data, "animation": False}],
}

# Convert to JSON for embedding
chart_json = json.dumps(chart_options)

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background-color: #ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {chart_json});
    </script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(5000, 3000)
driver.get(f"file://{temp_path}")

# Wait for Highcharts chart to render
try:
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".highcharts-root")))
    time.sleep(3)
except Exception:
    time.sleep(10)

# Get the container element and screenshot it
container = driver.find_element(By.ID, "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
