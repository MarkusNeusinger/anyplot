"""pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-03-06
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart  # noqa: F401
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - ETS-family transcription factor binding site motif (10 positions)
# Frequency matrix: each position has relative frequencies for A, C, G, T
freq_matrix = [
    {"A": 0.23, "C": 0.31, "G": 0.25, "T": 0.21},
    {"A": 0.10, "C": 0.05, "G": 0.80, "T": 0.05},
    {"A": 0.05, "C": 0.05, "G": 0.85, "T": 0.05},
    {"A": 0.90, "C": 0.03, "G": 0.04, "T": 0.03},
    {"A": 0.85, "C": 0.05, "G": 0.05, "T": 0.05},
    {"A": 0.02, "C": 0.02, "G": 0.02, "T": 0.94},
    {"A": 0.03, "C": 0.03, "G": 0.03, "T": 0.91},
    {"A": 0.20, "C": 0.40, "G": 0.10, "T": 0.30},
    {"A": 0.25, "C": 0.25, "G": 0.25, "T": 0.25},
    {"A": 0.15, "C": 0.45, "G": 0.20, "T": 0.20},
]

letter_colors = {"A": "#2ca02c", "C": "#1f77b4", "G": "#ff7f0e", "T": "#d62728"}
nucleotides = ["A", "C", "G", "T"]

# Calculate information content and letter heights per position
stacks = []
for freqs in freq_matrix:
    entropy = sum(-f * np.log2(f) for f in freqs.values() if f > 0)
    ic = max(0, 2.0 - entropy)
    heights = [(freqs[nt] * ic, nt) for nt in nucleotides if freqs[nt] > 0]
    heights.sort(key=lambda x: x[0])
    stacks.append(heights)

# Build 4 series (one per stack level, bottom to top)
series_config = []
for level in range(4):
    data_points = []
    for stack in stacks:
        if level < len(stack):
            height, letter = stack[level]
            data_points.append({"y": round(height, 4), "color": letter_colors[letter], "custom": {"letter": letter}})
        else:
            data_points.append({"y": 0, "color": "transparent", "custom": {"letter": ""}})
    series_config.append(
        {
            "type": "column",
            "name": f"Level {level}",
            "data": data_points,
            "showInLegend": False,
            "borderWidth": 0,
            "enableMouseTracking": True,
            "dataLabels": {
                "enabled": True,
                "useHTML": True,
                "align": "center",
                "verticalAlign": "middle",
                "y": 0,
                "padding": 0,
                "crop": False,
                "overflow": "allow",
                "style": {"textOutline": "none"},
                "formatter": "__FORMATTER__",
            },
        }
    )

# Build Highcharts config
config = {
    "chart": {
        "type": "column",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 200,
        "marginTop": 140,
        "marginLeft": 220,
        "marginRight": 100,
    },
    "title": {
        "text": "sequence-logo-basic \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "500"},
    },
    "xAxis": {
        "categories": [str(i + 1) for i in range(len(freq_matrix))],
        "title": {"text": "Position", "style": {"fontSize": "36px"}, "margin": 20},
        "labels": {"style": {"fontSize": "28px"}},
        "lineWidth": 2,
        "lineColor": "#333",
        "tickWidth": 0,
    },
    "yAxis": {
        "title": {"text": "Information content (bits)", "style": {"fontSize": "36px"}, "margin": 30},
        "labels": {"style": {"fontSize": "28px"}},
        "max": 2.0,
        "min": 0,
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0,0,0,0.1)",
        "lineWidth": 2,
        "lineColor": "#333",
    },
    "plotOptions": {"column": {"stacking": "normal", "pointPadding": 0, "groupPadding": 0.08, "borderWidth": 0}},
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "tooltip": {"style": {"fontSize": "22px"}, "formatter": "__TOOLTIP_FORMATTER__", "useHTML": True},
    "series": series_config,
}

# Serialize config to JSON, then inject JS functions
config_json = json.dumps(config)

formatter_js = """function() {
    var letter = this.point.custom && this.point.custom.letter;
    if (!letter || this.point.y < 0.03) return '';
    var h = this.point.shapeArgs ? this.point.shapeArgs.height : 30;
    var fontSize = Math.max(20, Math.min(Math.floor(h * 0.78), 200));
    return '<div style="font-family:Arial Black,Impact,sans-serif;font-size:' + fontSize + 'px;font-weight:900;color:#fff;line-height:1;text-align:center;text-shadow:1px 1px 2px rgba(0,0,0,0.3);">' + letter + '</div>';
}"""

tooltip_js = """function() {
    var letter = this.point.custom && this.point.custom.letter;
    if (!letter) return false;
    return '<b>Position ' + (this.point.index + 1) + '</b><br/>' +
           'Nucleotide: <b>' + letter + '</b><br/>' +
           'Height: <b>' + this.point.y.toFixed(3) + ' bits</b>';
}"""

config_js = config_json.replace('"__FORMATTER__"', formatter_js)
config_js = config_js.replace('"__TOOLTIP_FORMATTER__"', tooltip_js)

# Load Highcharts JS for inline embedding
# Try local npm install first (CDN may be blocked in CI), then fall back to CDN
highcharts_paths = [
    Path(__file__).resolve().parents[3] / "node_modules" / "highcharts" / "highcharts.js",
    Path("node_modules/highcharts/highcharts.js"),
]
highcharts_js = None
for p in highcharts_paths:
    if p.exists():
        highcharts_js = p.read_text(encoding="utf-8")
        break
if highcharts_js is None:
    highcharts_url = "https://code.highcharts.com/highcharts.js"
    req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")

# Build HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>Highcharts.chart('container', {config_js});</script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
