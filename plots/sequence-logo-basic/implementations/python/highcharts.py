""" anyplot.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-02
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.utility_classes.javascript_functions import CallbackFunction
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# DNA colors using Imprint palette positions (semantic exception: biology conventions)
# A=green, C=blue, G=ochre, T=red — standard molecular biology color scheme
letter_colors = {
    "A": "#009E73",  # Imprint slot 1 — green (standard A color)
    "C": "#4467A3",  # Imprint slot 3 — blue (standard C color)
    "G": "#BD8233",  # Imprint slot 4 — ochre (standard G orange/yellow)
    "T": "#AE3030",  # Imprint slot 5 — matte red (standard T color)
}
nucleotides = ["A", "C", "G", "T"]

# ETS-family transcription factor binding site motif (10 positions)
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

# Information content: IC = 2 - entropy (max 2 bits for DNA)
stacks = []
for freqs in freq_matrix:
    entropy = sum(-f * np.log2(f) for f in freqs.values() if f > 0)
    ic = max(0, 2.0 - entropy)
    heights = [(freqs[nt] * ic, nt) for nt in nucleotides if freqs[nt] > 0]
    heights.sort(key=lambda x: x[0])
    stacks.append(heights)

# Letter glyph formatter: renders scaled letters — only when bar is tall enough
# Threshold 0.10 bits prevents tiny squished glyphs on minor nucleotides
label_formatter = CallbackFunction.from_js_literal(
    """function() {
    var letter = this.point.custom && this.point.custom.letter;
    if (!letter || this.point.y < 0.10) return '';
    var h = this.point.shapeArgs ? this.point.shapeArgs.height : 0;
    var w = this.point.shapeArgs ? this.point.shapeArgs.width : 80;
    if (h < 14) return '';
    var baseFontSize = Math.max(40, Math.min(Math.floor(w * 0.70), 160));
    var scaleY = Math.max(0.35, Math.min(h / (baseFontSize * 1.1), 4.0));
    return '<div style="font-family:Arial Black,Impact,sans-serif;'
        + 'font-size:' + baseFontSize + 'px;font-weight:900;'
        + 'color:rgba(255,255,255,0.94);line-height:1;text-align:center;'
        + 'transform:scaleY(' + scaleY.toFixed(2) + ');'
        + 'text-shadow:0 1px 4px rgba(0,0,0,0.40);">'
        + letter + '</div>';
}"""
)

tooltip_formatter = CallbackFunction.from_js_literal(
    """function() {
    var letter = this.point.custom && this.point.custom.letter;
    if (!letter) return false;
    return '<b>Position ' + (this.point.index + 1) + '</b><br/>'
        + 'Nucleotide: <b>' + letter + '</b><br/>'
        + 'Height: <b>' + this.point.y.toFixed(3) + ' bits</b>';
}"""
)

# Build chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "column",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 180,
    "marginTop": 160,
    "marginLeft": 230,
    "marginRight": 100,
    "style": {"fontFamily": "'Helvetica Neue', Arial, sans-serif", "color": INK},
}

chart.options.title = {
    "text": "sequence-logo-basic · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "600", "color": INK},
    "margin": 36,
}

chart.options.subtitle = {
    "text": "ETS-family transcription factor binding site — conserved GGAATT core motif",
    "style": {"fontSize": "44px", "fontWeight": "400", "color": INK_SOFT},
}

chart.options.x_axis = {
    "categories": [str(i + 1) for i in range(len(freq_matrix))],
    "title": {"text": "Position", "style": {"fontSize": "56px", "fontWeight": "500", "color": INK}, "margin": 24},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineWidth": 2,
    "lineColor": INK_SOFT,
    "tickWidth": 0,
    "gridLineColor": GRID,
}

chart.options.y_axis = {
    "title": {
        "text": "Information content (bits)",
        "style": {"fontSize": "56px", "fontWeight": "500", "color": INK},
        "margin": 28,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "max": 2.0,
    "min": 0,
    "tickInterval": 0.5,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Solid",
    "lineWidth": 2,
    "lineColor": INK_SOFT,
}

chart.options.plot_options = {
    "column": {"stacking": "normal", "pointPadding": 0.02, "groupPadding": 0.06, "borderWidth": 0, "borderRadius": 0}
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.tooltip = {
    "useHTML": True,
    "formatter": tooltip_formatter,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "style": {"fontSize": "36px", "color": INK},
}

# Build 4 series (one per stack level, bottom → top)
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

# Load Highcharts JS inline (required — headless Chrome blocks CDN from file:// URLs)
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
    req = urllib.request.Request(
        "https://code.highcharts.com/highcharts.js",
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via Selenium with authoritative viewport override
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative — --window-size alone gets eaten by Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dimensions; occasional ±1–2 px rounding from CDP
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
