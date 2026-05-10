"""anyplot.ai
bar-feature-importance: Feature Importance Bar Chart
Library: highcharts | Python 3.13
Quality: 91/100 | Updated: 2025-05-10
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

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

importance = [0.215, 0.142, 0.128, 0.089, 0.078, 0.068, 0.062, 0.055, 0.048, 0.041, 0.028, 0.019, 0.014, 0.009, 0.004]

# Sort by importance (highest first)
sorted_data = sorted(zip(features, importance, strict=True), key=lambda x: x[1], reverse=True)
features_sorted = [x[0] for x in sorted_data]
importance_sorted = [x[1] for x in sorted_data]

# Reverse for horizontal bar chart (highest importance at top in Highcharts)
features_sorted = features_sorted[::-1]
importance_sorted = importance_sorted[::-1]

# Create gradient colors using viridis-inspired sequential colormap
# For continuous importance data, use a sequential colormap (light to dark)
max_imp = max(importance_sorted)
min_imp = min(importance_sorted)

# Viridis-inspired colors (light to dark)
viridis_light = "#FDE725"  # Light end
viridis_dark = "#440154"  # Dark end

bar_data = []
for imp in importance_sorted:
    # Interpolate between light and dark
    ratio = (imp - min_imp) / (max_imp - min_imp) if max_imp != min_imp else 0.5
    r = int(253 + (68 - 253) * ratio)
    g = int(231 + (1 - 231) * ratio)
    b = int(37 + (84 - 37) * ratio)
    color = f"#{r:02x}{g:02x}{b:02x}"
    bar_data.append({"y": imp, "color": color})

# Download Highcharts JS from jsDelivr CDN (more reliable in CI/CD)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build chart options
chart_options = {
    "chart": {
        "type": "bar",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginLeft": 380,
        "marginRight": 180,
        "marginTop": 150,
        "marginBottom": 120,
        "animation": False,
    },
    "title": {
        "text": "bar-feature-importance · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
    },
    "subtitle": {
        "text": "House Price Prediction - Random Forest Feature Importances",
        "style": {"fontSize": "22px", "color": INK_SOFT},
    },
    "xAxis": {
        "categories": features_sorted,
        "title": {"text": None},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineWidth": 0,
    },
    "yAxis": {
        "title": {"text": "Importance Score", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "min": 0,
        "max": 0.25,
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    },
    "legend": {"enabled": False},
    "tooltip": {"enabled": False},
    "plotOptions": {
        "bar": {
            "dataLabels": {
                "enabled": True,
                "format": "{point.y:.3f}",
                "style": {"fontSize": "18px", "color": INK_SOFT, "textOutline": "none"},
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
<body style="margin:0; padding:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {chart_json});
    </script>
</body>
</html>"""

# Save HTML for interactive version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
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

# Wait for Highcharts chart to render
try:
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".highcharts-root")))
    time.sleep(3)
except Exception:
    time.sleep(5)

driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
