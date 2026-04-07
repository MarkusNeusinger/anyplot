""" pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 90/100 | Updated: 2026-04-07
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import qrcode
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data
content = "https://pyplots.ai"
qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=4)
qr.add_data(content)
qr.make(fit=True)
matrix = qr.get_matrix()
size = len(matrix)
qr_version = qr.version
module_count = size - 2 * qr.border  # actual QR modules without quiet zone

# Convert to heatmap data [x, y, value] with y flipped for correct orientation
heatmap_data = []
for row_idx, row in enumerate(matrix):
    for col_idx, cell in enumerate(row):
        y = size - 1 - row_idx
        heatmap_data.append([col_idx, y, 1 if cell else 0])

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#f8f9fa",
    "marginTop": 200,
    "marginBottom": 200,
    "marginLeft": 120,
    "marginRight": 120,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "qrcode-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "700", "color": "#1a1a2e"},
    "y": 60,
}

chart.options.subtitle = {
    "text": f"\ud83d\udd17 Encoded: {content}",
    "style": {"fontSize": "40px", "color": "#306998", "fontWeight": "500"},
    "y": 120,
}

chart.options.x_axis = {"visible": False, "min": -0.5, "max": size - 0.5}
chart.options.y_axis = {"visible": False, "min": -0.5, "max": size - 0.5, "reversed": False}

chart.options.color_axis = {"min": 0, "max": 1, "stops": [[0, "#ffffff"], [1, "#1a1a2e"]], "visible": False}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

# Build tooltip config properly instead of brittle string replacement
chart.options.tooltip = {
    "enabled": True,
    "snap": 0,
    "headerFormat": "",
    "backgroundColor": "rgba(26,26,46,0.9)",
    "borderColor": "#306998",
    "borderRadius": 12,
    "borderWidth": 2,
    "style": {"color": "#ffffff", "fontSize": "28px"},
    "useHTML": True,
}

chart.options.plot_options = {
    "heatmap": {
        "borderWidth": 0,
        "colsize": 1,
        "rowsize": 1,
        "dataLabels": {"enabled": False},
        "states": {
            "hover": {"brightness": 0.15, "borderColor": "#306998", "borderWidth": 2},
            "inactive": {"opacity": 1},
        },
    }
}

# Responsive rules: adapt title size for smaller containers
chart.options.responsive = {
    "rules": [
        {
            "condition": {"maxWidth": 1200},
            "chartOptions": {"title": {"style": {"fontSize": "36px"}}, "subtitle": {"style": {"fontSize": "24px"}}},
        }
    ]
}

# Series
series = HeatmapSeries()
series.data = heatmap_data
series.name = "QR Code"
series.border_width = 0
chart.add_series(series)

# Download Highcharts JS with CDN fallback
cdn_bases = ["https://code.highcharts.com", "https://cdn.jsdelivr.net/npm/highcharts@11"]
js_paths = {"highcharts": "/highcharts.js", "heatmap": "/modules/heatmap.js"}
js_code = {}
for name, path in js_paths.items():
    for base in cdn_bases:
        try:
            req = urllib.request.Request(base + path, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                js_code[name] = resp.read().decode("utf-8")
            break
        except Exception:
            continue

highcharts_js = js_code["highcharts"]
heatmap_js = js_code["heatmap"]

# Build options JSON and inject formatter as JS function
options_dict = chart.options.to_dict()
options_json = json.dumps(options_dict)

# Inject tooltip pointFormatter as a real JS function via placeholder
tooltip_placeholder = '"__POINT_FORMATTER__"'
options_dict["tooltip"]["pointFormatter"] = "__POINT_FORMATTER__"
options_json = json.dumps(options_dict)
formatter_js = (
    "function() { "
    "var pos = '(' + this.x + ', ' + (this.series.yAxis.max - this.y) + ')'; "
    "return '<b>' + (this.point.value === 1 ? '\\u25a0 Data Module' : '\\u25a1 Quiet Zone') + '</b><br/>Position: ' + pos; "
    "}"
)
options_json = options_json.replace(tooltip_placeholder, formatter_js)

# Footer text with QR technical details
footer_text = (
    f"Version {qr_version} &middot; Error Correction M (15%) &middot; {module_count}&times;{module_count} modules"
)

# Custom render callback to draw rounded frame and footer
render_callback = f"""
Highcharts.addEvent(chart, 'render', function() {{
    var ren = this.renderer;
    if (this.customFrame) this.customFrame.destroy();
    if (this.customFooter) this.customFooter.destroy();
    var plotX = this.plotLeft - 20;
    var plotY = this.plotTop - 20;
    var plotW = this.plotWidth + 40;
    var plotH = this.plotHeight + 40;
    this.customFrame = ren.rect(plotX, plotY, plotW, plotH, 16)
        .attr({{
            'stroke': '#306998',
            'stroke-width': 4,
            fill: 'none',
            zIndex: 5,
            filter: 'url(#drop-shadow)'
        }})
        .add();
    this.customFooter = ren.text('{footer_text}',
        this.chartWidth / 2, this.chartHeight - 60)
        .attr({{ align: 'center', zIndex: 5 }})
        .css({{ fontSize: '32px', color: '#6c757d', fontWeight: '400',
               fontFamily: "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif" }})
        .add();
}});
"""

# SVG filter for drop shadow
shadow_filter = """
<defs>
    <filter id="drop-shadow" x="-5%" y="-5%" width="120%" height="120%">
        <feDropShadow dx="4" dy="6" stdDeviation="8" flood-color="rgba(48,105,152,0.25)"/>
    </filter>
</defs>
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; padding:0; background-color:#f8f9fa; overflow:hidden;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
    var chart = Highcharts.chart('container', {options_json});
    // Add drop shadow filter to SVG
    var svgEl = chart.renderer.box;
    var defsHtml = '{shadow_filter.strip().replace(chr(10), "")}';
    var temp = document.createElement('div');
    temp.innerHTML = '<svg>' + defsHtml + '</svg>';
    var defs = temp.firstChild.firstChild;
    svgEl.insertBefore(defs, svgEl.firstChild);
    // Draw rounded frame with shadow and footer
    {render_callback}
    </script>
</body>
</html>"""

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
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
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
