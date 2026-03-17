""" pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: highcharts unknown | Python 3.14.3
Quality: 76/100 | Created: 2026-03-17
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Risk items with likelihood and impact ratings
np.random.seed(42)

risks = [
    {"name": "Server Outage", "likelihood": 3, "impact": 5, "category": "Technical"},
    {"name": "Data Breach", "likelihood": 2, "impact": 5, "category": "Technical"},
    {"name": "Budget Overrun", "likelihood": 4, "impact": 4, "category": "Financial"},
    {"name": "Key Staff Loss", "likelihood": 3, "impact": 4, "category": "Operational"},
    {"name": "Vendor Delay", "likelihood": 4, "impact": 3, "category": "Operational"},
    {"name": "Scope Creep", "likelihood": 5, "impact": 3, "category": "Operational"},
    {"name": "Currency Risk", "likelihood": 3, "impact": 3, "category": "Financial"},
    {"name": "Reg. Change", "likelihood": 2, "impact": 4, "category": "Financial"},
    {"name": "Tech Debt", "likelihood": 4, "impact": 2, "category": "Technical"},
    {"name": "Minor Bug", "likelihood": 5, "impact": 1, "category": "Technical"},
    {"name": "Supply Issue", "likelihood": 2, "impact": 3, "category": "Operational"},
    {"name": "IP Dispute", "likelihood": 1, "impact": 5, "category": "Financial"},
    {"name": "Power Failure", "likelihood": 1, "impact": 3, "category": "Technical"},
    {"name": "PR Crisis", "likelihood": 2, "impact": 4, "category": "Operational"},
]

likelihood_labels = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
impact_labels = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"]

# Build background heatmap data (risk score = likelihood × impact)
heatmap_data = []
for li in range(5):
    for im in range(5):
        score = (li + 1) * (im + 1)
        heatmap_data.append([im, li, score])

# Color stops for green-yellow-orange-red risk gradient
# Scores range from 1 to 25
color_stops = [
    [0, "#2ecc71"],  # Low (green)
    [0.16, "#27ae60"],  # Low-medium
    [0.36, "#f1c40f"],  # Medium (yellow)
    [0.56, "#e67e22"],  # High (orange)
    [0.76, "#e74c3c"],  # Critical (red)
    [1.0, "#c0392b"],  # Critical (dark red)
]

# Category colors for risk markers
category_colors = {"Technical": "#306998", "Financial": "#8e44ad", "Operational": "#16a085"}

# Build scatter series for each category with jitter
scatter_series = []
for category in ["Technical", "Financial", "Operational"]:
    cat_risks = [r for r in risks if r["category"] == category]
    data_points = []
    for risk in cat_risks:
        jitter_x = np.random.uniform(-0.25, 0.25)
        jitter_y = np.random.uniform(-0.25, 0.25)
        data_points.append(
            {
                "x": risk["impact"] - 1 + jitter_x,
                "y": risk["likelihood"] - 1 + jitter_y,
                "name": risk["name"],
                "score": risk["likelihood"] * risk["impact"],
            }
        )
    scatter_series.append(
        {
            "type": "scatter",
            "name": category,
            "data": data_points,
            "color": category_colors[category],
            "marker": {"radius": 18, "symbol": "circle", "lineWidth": 3, "lineColor": "#ffffff"},
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "style": {"fontSize": "22px", "fontWeight": "600", "color": "#2c3e50", "textOutline": "3px #ffffff"},
                "y": -30,
                "allowOverlap": False,
            },
            "tooltip": {"pointFormat": ("<b>{point.name}</b><br>Risk Score: <b>{point.score}</b>")},
            "zIndex": 5,
            "colorAxis": False,
            "showInLegend": True,
        }
    )

# Chart configuration
chart_options = {
    "chart": {
        "type": "heatmap",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#fafafa",
        "marginTop": 200,
        "marginBottom": 200,
        "marginRight": 300,
        "marginLeft": 360,
        "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
    },
    "title": {
        "text": "heatmap-risk-matrix · highcharts · pyplots.ai",
        "style": {"fontSize": "52px", "fontWeight": "600", "color": "#2c3e50"},
        "y": 40,
    },
    "subtitle": {
        "text": "Risk score = Likelihood × Impact — markers show individual risk items by category",
        "style": {"fontSize": "30px", "fontWeight": "normal", "color": "#7f8c8d"},
        "y": 90,
    },
    "xAxis": {
        "categories": impact_labels,
        "title": {
            "text": "Impact",
            "style": {"fontSize": "36px", "fontWeight": "600", "color": "#2c3e50"},
            "margin": 24,
        },
        "labels": {"style": {"fontSize": "30px", "color": "#34495e"}, "y": 40},
        "lineWidth": 0,
        "tickLength": 0,
        "opposite": False,
        "min": 0,
        "max": 4,
    },
    "yAxis": {
        "categories": likelihood_labels,
        "title": {
            "text": "Likelihood",
            "style": {"fontSize": "36px", "fontWeight": "600", "color": "#2c3e50"},
            "margin": 24,
        },
        "labels": {"style": {"fontSize": "30px", "color": "#34495e"}},
        "reversed": False,
        "lineWidth": 0,
        "gridLineWidth": 0,
        "min": 0,
        "max": 4,
    },
    "colorAxis": {
        "min": 1,
        "max": 25,
        "stops": color_stops,
        "labels": {"style": {"fontSize": "24px", "color": "#34495e"}},
        "showInLegend": False,
    },
    "legend": {
        "align": "right",
        "layout": "vertical",
        "verticalAlign": "bottom",
        "itemStyle": {"fontSize": "26px", "color": "#34495e"},
        "itemMarginBottom": 12,
        "x": -40,
        "y": -40,
        "symbolRadius": 10,
        "symbolHeight": 20,
        "symbolWidth": 20,
    },
    "tooltip": {"style": {"fontSize": "28px"}},
    "credits": {"enabled": False},
    "plotOptions": {"heatmap": {"colsize": 1, "rowsize": 1}},
    "series": [
        {
            "type": "heatmap",
            "name": "Risk Score",
            "data": heatmap_data,
            "borderWidth": 4,
            "borderColor": "#fafafa",
            "dataLabels": {"enabled": True, "style": {"fontSize": "34px", "fontWeight": "bold", "textOutline": "none"}},
            "tooltip": {
                "headerFormat": "",
                "pointFormat": (
                    "Impact: <b>{series.xAxis.categories.(point.x)}</b><br>"
                    "Likelihood: <b>{series.yAxis.categories.(point.y)}</b><br>"
                    "Risk Score: <b>{point.value}</b>"
                ),
            },
            "showInLegend": False,
        },
        *scatter_series,
    ],
}

# Download Highcharts JS and heatmap module
js_urls = [
    ("https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"),
    ("https://code.highcharts.com/modules/heatmap.js", "https://cdn.jsdelivr.net/npm/highcharts@11/modules/heatmap.js"),
]
js_parts = []
for primary, fallback in js_urls:
    for url in (primary, fallback):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                js_parts.append(response.read().decode("utf-8"))
            break
        except Exception:
            continue
all_js = "\n".join(js_parts)

# Convert options to JSON
options_json = json.dumps(chart_options)

# Generate HTML with inline scripts and adaptive data label colors
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{all_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:#fafafa;">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>
        var opts = {options_json};
        opts.series[0].dataLabels.formatter = function() {{
            var v = this.point.value;
            var color = v >= 15 ? '#ffffff' : '#333333';
            return '<span style="color:' + color + ';font-size:34px;font-weight:bold">' + v + '</span>';
        }};
        opts.series[0].dataLabels.useHTML = true;
        Highcharts.chart('container', opts);
    </script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot using headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2840")
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--hide-scrollbars")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4800, 2840)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
