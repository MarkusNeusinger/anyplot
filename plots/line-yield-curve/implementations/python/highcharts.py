""" pyplots.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: highcharts unknown | Python 3.14.3
Quality: 92/100 | Created: 2026-03-14
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - U.S. Treasury yield curves across three market regimes
maturity_labels = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
maturity_years = [0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]

yields_normal = [0.08, 0.21, 0.47, 0.78, 1.20, 1.45, 1.72, 1.88, 1.93, 2.28, 2.25]
yields_inverted = [5.54, 5.55, 5.52, 5.44, 5.05, 4.80, 4.62, 4.64, 4.62, 4.98, 4.88]
yields_normalizing = [4.34, 4.34, 4.30, 4.16, 4.20, 4.22, 4.32, 4.42, 4.53, 4.82, 4.72]

# Build chart using highcharts_core Python API
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 280,
    "marginLeft": 250,
    "marginRight": 120,
    "spacingTop": 80,
    "style": {"fontFamily": "Arial, sans-serif"},
}

chart.options.title = {
    "text": "line-yield-curve \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "60px", "fontWeight": "500", "color": "#333333"},
}

chart.options.subtitle = {
    "text": "U.S. Treasury Yield Curves \u2014 Term Structure Across Three Market Regimes",
    "style": {"fontSize": "36px", "color": "#666666"},
}

chart.options.x_axis = {
    "title": {"text": "Maturity", "style": {"fontSize": "42px", "color": "#444444"}, "margin": 30},
    "labels": {"style": {"fontSize": "34px", "color": "#444444"}, "y": 40},
    "tickPositions": [0.083, 0.5, 1, 2, 3, 5, 7, 10, 20, 30],
    "lineWidth": 2,
    "lineColor": "#cccccc",
    "tickWidth": 0,
    "gridLineWidth": 0,
    "plotBands": [
        {
            "from": 0,
            "to": 7,
            "color": "rgba(196, 78, 82, 0.06)",
            "label": {
                "text": "Inversion zone",
                "style": {"fontSize": "30px", "color": "rgba(196, 78, 82, 0.65)", "fontWeight": "500"},
                "align": "center",
                "verticalAlign": "middle",
                "y": 10,
            },
        }
    ],
}

chart.options.y_axis = {
    "title": {"text": "Yield (%)", "style": {"fontSize": "42px", "color": "#444444"}, "margin": 30},
    "labels": {"style": {"fontSize": "34px", "color": "#444444"}, "format": "{value:.1f}%", "x": -15},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.08)",
    "gridLineDashStyle": "Dash",
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal", "color": "#444444"},
    "symbolWidth": 50,
    "symbolHeight": 14,
    "itemDistance": 60,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 120,
    "floating": True,
    "backgroundColor": "rgba(255,255,255,0.85)",
    "borderWidth": 1,
    "borderColor": "#e0e0e0",
    "borderRadius": 8,
    "padding": 20,
}

chart.options.tooltip = {"shared": True, "style": {"fontSize": "28px"}, "valueDecimals": 2, "valueSuffix": "%"}

chart.options.plot_options = {
    "line": {"lineWidth": 7, "marker": {"enabled": True, "radius": 10, "lineWidth": 2, "lineColor": "#ffffff"}}
}

chart.options.credits = {"enabled": False}

# Add series using LineSeries API
series_configs = [
    ("Jan 2022 (Normal)", yields_normal, "#306998", "circle"),
    ("Oct 2023 (Inverted)", yields_inverted, "#C44E52", "diamond"),
    ("Jan 2025 (Normalizing)", yields_normalizing, "#55A868", "triangle"),
]

for name, yields, color, symbol in series_configs:
    s = LineSeries()
    s.data = [[maturity_years[i], yields[i]] for i in range(len(maturity_years))]
    s.name = name
    s.color = color
    s.marker = {"symbol": symbol}
    chart.add_series(s)

# Generate JS literal from highcharts_core
js_literal = chart.to_js_literal()

# Inject x-axis formatter (JS callback for maturity label mapping)
xaxis_formatter = (
    "formatter: function() {\n"
    "    var map = {0.083:'1M', 0.5:'6M', 1:'1Y', 2:'2Y', 3:'3Y', "
    "5:'5Y', 7:'7Y', 10:'10Y', 20:'20Y', 30:'30Y'};\n"
    "    return map[this.value] || this.value;\n"
    "  }"
)
js_literal = js_literal.replace("y: 40\n}", "y: 40,\n  " + xaxis_formatter + "\n}", 1)

# Download Highcharts JS (inline for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
fallback_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
try:
    with urllib.request.urlopen(highcharts_url, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")
except Exception:
    with urllib.request.urlopen(fallback_url, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")

# Build HTML with inline Highcharts JS
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        {js_literal}
    </script>
</body>
</html>"""

# Save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome
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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
