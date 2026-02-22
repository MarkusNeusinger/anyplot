"""pyplots.ai
bullet-basic: Basic Bullet Chart
Library: highcharts 1.10.3 | Python 3.14.3
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Q4 KPI dashboard with actual values, targets, and qualitative ranges
metrics = [
    {"name": "Revenue", "actual": 275, "target": 250, "max": 300, "label": "$275K"},
    {"name": "Profit", "actual": 22, "target": 27, "max": 35, "label": "22%"},
    {"name": "New Customers", "actual": 1650, "target": 1500, "max": 2000, "label": "1,650"},
    {"name": "Satisfaction", "actual": 4.5, "target": 4.7, "max": 5.0, "label": "4.5/5"},
]

# Qualitative range thresholds as percentage of max — poor / satisfactory / good
range_pcts = [50, 75, 100]

# Grayscale for qualitative ranges — light to dark = poor to good
range_colors = ["#e0e0e0", "#b0b0b0", "#808080"]

# Conditional bar colors — colorblind-safe green/amber for target achievement
color_above = "#2E7D32"  # Forest green — exceeds target
color_below = "#E65100"  # Deep orange — below target

# Font stack for polished typography
font_family = "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

# Normalize all values to 0-100% scale for a shared axis
series_data = []
for m in metrics:
    above_target = m["actual"] >= m["target"]
    series_data.append(
        {
            "y": round(m["actual"] / m["max"] * 100, 1),
            "target": round(m["target"] / m["max"] * 100, 1),
            "label": m["label"],
            "color": color_above if above_target else color_below,
        }
    )

categories = [m["name"] for m in metrics]

# Identify worst-performing metric (lowest actual/target ratio) for storytelling emphasis
worst_idx = min(range(len(metrics)), key=lambda i: metrics[i]["actual"] / metrics[i]["target"])
worst_m = metrics[worst_idx]
gap_pct = round((1 - worst_m["actual"] / worst_m["target"]) * 100, 1)

# Chart configuration — tighter layout for better canvas utilization
chart_options = {
    "chart": {
        "type": "bullet",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "inverted": True,
        "marginLeft": 380,
        "marginRight": 120,
        "spacing": [50, 40, 50, 40],
        "style": {"fontFamily": font_family},
    },
    "title": {
        "text": "Q4 Performance Dashboard · bullet-basic · highcharts · pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "bold", "fontFamily": font_family},
    },
    "subtitle": {
        "text": (
            "Actual performance vs targets across key business metrics"
            '<br/><span style="font-size:24px;">'
            '<span style="color:#2E7D32;">&#9632;</span> Exceeds target'
            "&emsp;&emsp;"
            '<span style="color:#E65100;">&#9632;</span> Below target'
            "&emsp;&emsp;"
            '<span style="color:#1a1a1a;">&#124;</span> Target marker'
            "</span>"
        ),
        "useHTML": True,
        "style": {"fontSize": "30px", "color": "#555555", "fontFamily": font_family},
    },
    "xAxis": {
        "categories": categories,
        "labels": {"style": {"fontSize": "32px", "fontWeight": "bold", "fontFamily": font_family}},
    },
    "yAxis": {
        "gridLineWidth": 0,
        "min": 0,
        "max": 100,
        "title": {"text": "% of Maximum", "style": {"fontSize": "28px", "fontFamily": font_family}},
        "tickInterval": 10,
        "labels": {"format": "{value}%", "style": {"fontSize": "24px", "fontFamily": font_family}},
        "plotBands": [
            {"from": 0, "to": range_pcts[0], "color": range_colors[0]},
            {"from": range_pcts[0], "to": range_pcts[1], "color": range_colors[1]},
            {"from": range_pcts[1], "to": range_pcts[2], "color": range_colors[2]},
        ],
    },
    "legend": {"enabled": False},
    "plotOptions": {
        "bullet": {
            "pointPadding": 0.1,
            "borderWidth": 0,
            "groupPadding": 0.02,
            "targetOptions": {"width": "220%", "height": 12, "borderWidth": 0, "color": "#000000"},
            "dataLabels": {
                "enabled": True,
                "format": "{point.label}",
                "style": {
                    "fontSize": "28px",
                    "fontWeight": "bold",
                    "color": "#ffffff",
                    "fontFamily": font_family,
                    "textOutline": "none",
                },
                "inside": True,
                "align": "right",
            },
        }
    },
    "series": [{"name": "Performance", "data": series_data}],
    "tooltip": {
        "headerFormat": '<span style="font-size: 24px; font-weight: bold;">{point.key}</span><br/>',
        "pointFormat": (
            '<span style="font-size: 20px;">'
            "Actual: <b>{point.label}</b> ({point.y}%)<br/>"
            "Target: {point.target}%"
            "</span>"
        ),
    },
    "annotations": [
        {
            "labels": [
                {
                    "point": {"x": worst_idx, "y": series_data[worst_idx]["y"], "xAxis": 0, "yAxis": 0},
                    "text": f"▼ {gap_pct}% below target",
                    "style": {"fontSize": "24px", "fontWeight": "bold", "color": "#E65100", "fontFamily": font_family},
                    "backgroundColor": "rgba(255,255,255,0.85)",
                    "borderColor": "#E65100",
                    "borderWidth": 2,
                    "borderRadius": 6,
                    "padding": 10,
                    "y": -30,
                }
            ],
            "draggable": "",
        }
    ],
    "credits": {"enabled": False},
}

# Download Highcharts JS files for inline embedding (jsDelivr CDN)
cdn_base = "https://cdn.jsdelivr.net/npm/highcharts@11.4"
js_urls = {
    "highcharts": f"{cdn_base}/highcharts.js",
    "highcharts_more": f"{cdn_base}/highcharts-more.js",
    "bullet": f"{cdn_base}/modules/bullet.js",
    "annotations": f"{cdn_base}/modules/annotations.js",
}
js_modules = {}
for name, url in js_urls.items():
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        js_modules[name] = response.read().decode("utf-8")

# Generate HTML with inline scripts
chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_modules["highcharts"]}</script>
    <script>{js_modules["highcharts_more"]}</script>
    <script>{js_modules["bullet"]}</script>
    <script>{js_modules["annotations"]}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
