"""anyplot.ai
lollipop-basic: Basic Lollipop Chart
Library: highcharts | Python 3.14
Quality: pending | Updated: 2026-04-26
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1 — ALWAYS first series

# Data — Product sales by category (deterministic, sorted descending)
categories = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Toys",
    "Beauty",
    "Automotive",
    "Food & Grocery",
    "Health",
]
values = [124820, 97340, 86715, 75260, 64480, 53905, 47620, 41370, 37815, 30945]

# Plot — combine column (thin stems) and scatter (round markers) for the lollipop look
chart_options = {
    "chart": {
        "type": "scatter",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "spacingTop": 60,
        "spacingBottom": 60,
        "spacingLeft": 60,
        "spacingRight": 80,
        "marginBottom": 220,
        "style": {"fontFamily": "Inter, system-ui, sans-serif", "color": INK},
    },
    "title": {
        "text": "Product Sales by Category · lollipop-basic · highcharts · anyplot.ai",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "500"},
        "margin": 40,
    },
    "xAxis": {
        "categories": categories,
        "title": {
            "text": "Product Category",
            "style": {"fontSize": "36px", "fontWeight": "500", "color": INK},
            "margin": 28,
        },
        "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}, "y": 50},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineWidth": 0,
    },
    "yAxis": {
        "min": 0,
        "tickAmount": 8,
        "title": {
            "text": "Sales (Units)",
            "style": {"fontSize": "36px", "fontWeight": "500", "color": INK},
            "margin": 28,
        },
        "labels": {"style": {"fontSize": "26px", "color": INK_SOFT}, "format": "{value:,.0f}", "x": -12},
        "gridLineColor": GRID,
        "gridLineWidth": 1,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    },
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "plotOptions": {
        "scatter": {"marker": {"radius": 36, "symbol": "circle"}},
        "column": {"pointWidth": 8, "borderWidth": 0},
    },
    "series": [
        {"type": "column", "name": "Sales", "data": values, "color": BRAND, "enableMouseTracking": False},
        {
            "type": "scatter",
            "name": "Sales",
            "data": values,
            "color": BRAND,
            "marker": {"radius": 36, "fillColor": BRAND, "lineWidth": 5, "lineColor": PAGE_BG},
            "dataLabels": {
                "enabled": True,
                "format": "{y:,.0f}",
                "style": {"fontSize": "24px", "color": INK, "fontWeight": "500", "textOutline": "none"},
                "verticalAlign": "bottom",
                "y": -28,
            },
        },
    ],
}

# Download Highcharts JS for inline embedding (headless Chrome can't load CDN from file://)
cdn_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
highcharts_js = None
for url in cdn_urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS from all CDN sources")

# Generate HTML with inline scripts
chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

# Save HTML artifact (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Render PNG via headless Chrome
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
