"""pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: highcharts unknown | Python 3.14.3
Quality: 73/100 | Created: 2026-03-06
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.utility_classes.javascript_functions import CallbackFunction
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - ETS-family transcription factor binding site motif (10 positions)
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

# Stretched-glyph formatter: renders letters with CSS scaleY to fill bar height
label_formatter = CallbackFunction.from_js_literal("""function() {
    var letter = this.point.custom && this.point.custom.letter;
    if (!letter || this.point.y < 0.02) return '';
    var h = this.point.shapeArgs ? this.point.shapeArgs.height : 30;
    var w = this.point.shapeArgs ? this.point.shapeArgs.width : 80;
    var baseFontSize = Math.max(28, Math.min(Math.floor(w * 0.7), 180));
    var scaleY = Math.max(0.4, Math.min(h / baseFontSize, 4.5));
    return '<div style="font-family:Arial Black,Impact,sans-serif;'
        + 'font-size:' + baseFontSize + 'px;font-weight:900;'
        + 'color:rgba(255,255,255,0.92);line-height:1;text-align:center;'
        + 'transform:scaleY(' + scaleY.toFixed(2) + ');'
        + 'text-shadow:1px 2px 3px rgba(0,0,0,0.25);">'
        + letter + '</div>';
}""")

tooltip_formatter = CallbackFunction.from_js_literal("""function() {
    var letter = this.point.custom && this.point.custom.letter;
    if (!letter) return false;
    return '<b>Position ' + (this.point.index + 1) + '</b><br/>'
        + 'Nucleotide: <b>' + letter + '</b><br/>'
        + 'Height: <b>' + this.point.y.toFixed(3) + ' bits</b>';
}""")

# Build chart using highcharts-core Python API
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafafa",
    "marginBottom": 200,
    "marginTop": 160,
    "marginLeft": 240,
    "marginRight": 120,
    "style": {"fontFamily": "'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "sequence-logo-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "600", "color": "#2c3e50"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "ETS-family transcription factor binding site \u2014 conserved GGAATT core motif",
    "style": {"fontSize": "30px", "fontWeight": "400", "color": "#7f8c8d"},
}

chart.options.x_axis = {
    "categories": [str(i + 1) for i in range(len(freq_matrix))],
    "title": {"text": "Position", "style": {"fontSize": "36px", "fontWeight": "500", "color": "#34495e"}, "margin": 24},
    "labels": {"style": {"fontSize": "30px", "color": "#34495e"}},
    "lineWidth": 2,
    "lineColor": "#34495e",
    "tickWidth": 0,
}

chart.options.y_axis = {
    "title": {
        "text": "Information content (bits)",
        "style": {"fontSize": "36px", "fontWeight": "500", "color": "#34495e"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#34495e"}},
    "max": 2.0,
    "min": 0,
    "tickInterval": 0.5,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.06)",
    "gridLineDashStyle": "Dash",
    "lineWidth": 2,
    "lineColor": "#34495e",
}

chart.options.plot_options = {
    "column": {"stacking": "normal", "pointPadding": 0.02, "groupPadding": 0.06, "borderWidth": 0, "borderRadius": 0}
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.tooltip = {"style": {"fontSize": "22px"}, "useHTML": True, "formatter": tooltip_formatter}

# Build 4 series (one per stack level, bottom to top) using ColumnSeries
for level in range(4):
    data_points = []
    for stack in stacks:
        if level < len(stack):
            height, letter = stack[level]
            data_points.append({"y": round(height, 4), "color": letter_colors[letter], "custom": {"letter": letter}})
        else:
            data_points.append({"y": 0, "color": "transparent", "custom": {"letter": ""}})

    series = ColumnSeries()
    series.data = data_points
    series.name = f"Level {level}"
    series.show_in_legend = False
    series.enable_mouse_tracking = True
    series.data_labels = {
        "enabled": True,
        "useHTML": True,
        "align": "center",
        "verticalAlign": "middle",
        "y": 0,
        "padding": 0,
        "crop": False,
        "overflow": "allow",
        "style": {"textOutline": "none"},
        "formatter": label_formatter,
    }
    chart.add_series(series)

# Generate JS from the Chart object
js_literal = chart.to_js_literal()

# Load Highcharts JS for inline embedding
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

# Build HTML with inline Highcharts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:#fafafa;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{js_literal}</script>
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
