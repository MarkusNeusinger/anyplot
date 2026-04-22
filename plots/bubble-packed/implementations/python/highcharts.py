""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 85/100 | Updated: 2026-02-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Company market value by sector ($B)
data = [
    {
        "name": "Technology",
        "data": [
            {"name": "Software", "value": 850},
            {"name": "Hardware", "value": 420},
            {"name": "Cloud", "value": 680},
            {"name": "Semicon.", "value": 390},
            {"name": "Cybersec.", "value": 280},
        ],
    },
    {
        "name": "Finance",
        "data": [
            {"name": "Banking", "value": 720},
            {"name": "Insurance", "value": 480},
            {"name": "Asset Mgmt", "value": 350},
            {"name": "Fintech", "value": 260},
        ],
    },
    {
        "name": "Healthcare",
        "data": [
            {"name": "Pharma", "value": 580},
            {"name": "Med Devices", "value": 320},
            {"name": "Biotech", "value": 420},
            {"name": "Health Svcs", "value": 240},
        ],
    },
    {
        "name": "Energy",
        "data": [
            {"name": "Oil & Gas", "value": 550},
            {"name": "Renewables", "value": 380},
            {"name": "Utilities", "value": 290},
        ],
    },
    {
        "name": "Consumer",
        "data": [
            {"name": "Retail", "value": 460},
            {"name": "Food & Bev", "value": 340},
            {"name": "Automotive", "value": 510},
            {"name": "Entertain.", "value": 270},
        ],
    },
]

# Refined colorblind-safe palette — muted tones with strong contrast
colors = ["#306998", "#D4920B", "#7B4F9E", "#0E9AA7", "#C05746"]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Render at 900x900 CSS px, capture at 4x device scale → 3600x3600 (square format)
chart.options.chart = {
    "type": "packedbubble",
    "width": 900,
    "height": 900,
    "backgroundColor": {
        "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
        "stops": [[0, "#FAFBFD"], [1, "#F0F2F5"]],
    },
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
    "spacing": [8, 8, 12, 8],
}

# Title — sizes at 1/4 of target since 4x device scale factor
chart.options.title = {
    "text": "bubble-packed \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "16px", "fontWeight": "700", "color": "#1a1a2e"},
    "margin": 2,
}

# Subtitle
chart.options.subtitle = {
    "text": "Market value by sector ($B)",
    "style": {"fontSize": "9px", "color": "#555555", "fontWeight": "400"},
}

# Hide watermark
chart.options.credits = {"enabled": False}

# Tooltip
chart.options.tooltip = {
    "useHTML": True,
    "style": {"fontSize": "8px"},
    "pointFormat": "<b>{point.name}</b>: ${point.value}B",
}

# Legend — compact with small symbols
chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "floating": False,
    "margin": 4,
    "padding": 6,
    "itemStyle": {"fontSize": "9px", "fontWeight": "500", "color": "#333333"},
    "symbolHeight": 6,
    "symbolWidth": 6,
    "symbolRadius": 3,
    "itemDistance": 16,
}

# Plot options — selective labels on largest bubbles to prevent overlap
chart.options.plot_options = {
    "packedbubble": {
        "minSize": "40%",
        "maxSize": "200%",
        "zMin": 0,
        "zMax": 1000,
        "layoutAlgorithm": {
            "gravitationalConstant": 0.02,
            "splitSeries": True,
            "seriesInteraction": False,
            "dragBetweenSeries": False,
            "parentNodeLimit": True,
            "parentNodeOptions": {"reingold": {"gravitationalConstant": 0.08}, "marker": {"fillOpacity": 0}},
            "bubblePadding": 6,
        },
        "dataLabels": {
            "enabled": True,
            "format": "{point.name}",
            "filter": {"property": "y", "operator": ">", "value": 480},
            "style": {"fontSize": "10px", "fontWeight": "600", "color": "white", "textOutline": "1px rgba(0,0,0,0.4)"},
        },
        "marker": {"lineWidth": 1, "lineColor": "rgba(255,255,255,0.35)"},
    }
}

# Add series with colors and per-bubble opacity for visual hierarchy
series_list = []
for i, sector in enumerate(data):
    enriched_data = []
    for item in sector["data"]:
        opacity = 0.7 + 0.3 * (item["value"] / 850)
        enriched_data.append({"name": item["name"], "value": item["value"], "marker": {"fillOpacity": opacity}})
    series_list.append(
        {"type": "packedbubble", "name": sector["name"], "data": enriched_data, "color": colors[i % len(colors)]}
    )

chart.options.series = series_list

# Download Highcharts JS and highcharts-more.js for packed bubble support
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts-more.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()

# Post-render: center and scale the bubble cluster to fill 90% of the plot area
fit_script = """
<script>
setTimeout(function() {
    var c = Highcharts.charts[0];
    if (!c || !c.seriesGroup) return;
    var el = c.seriesGroup.element;
    var bb = el.getBBox();
    if (bb.width < 1 || bb.height < 1) return;
    var s = Math.min(c.plotWidth * 0.92 / bb.width, c.plotHeight * 0.92 / bb.height, 1.6);
    if (s <= 1.05) return;
    var tx = c.plotLeft + c.plotWidth / 2 - (bb.x + bb.width / 2) * s;
    var ty = c.plotTop + c.plotHeight / 2 - (bb.y + bb.height / 2) * s;
    el.setAttribute('transform', 'translate(' + tx + ',' + ty + ') scale(' + s + ')');
}, 6000);
</script>
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <style>
        .highcharts-series-group,
        .highcharts-series-group > * {{
            overflow: visible !important;
        }}
        svg.highcharts-root {{
            overflow: visible !important;
        }}
    </style>
</head>
<body style="margin:0; overflow:hidden; background:#F0F2F5; min-height:100vh;">
    <div id="container" style="width: 900px; height: 900px; overflow: visible;"></div>
    <script>{html_str}</script>
    {fit_script}
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts/highcharts-more.js"></script>
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
chrome_options.add_argument("--window-size=1100,1100")
chrome_options.add_argument("--force-device-scale-factor=4")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(10)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 3600x3600 dimensions (square format)
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 3600, 3600))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
