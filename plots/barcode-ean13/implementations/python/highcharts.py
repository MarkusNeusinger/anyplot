""" anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-21
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BARCODE_BG = "#FFFDF6"
BAR_COLOR = "#1A1A17"

# EAN-13 encoding tables
L_CODES = {
    "0": "0001101",
    "1": "0011001",
    "2": "0010011",
    "3": "0111101",
    "4": "0100011",
    "5": "0110001",
    "6": "0101111",
    "7": "0111011",
    "8": "0110111",
    "9": "0001011",
}
G_CODES = {
    "0": "0100111",
    "1": "0110011",
    "2": "0011011",
    "3": "0100001",
    "4": "0011101",
    "5": "0111001",
    "6": "0000101",
    "7": "0010001",
    "8": "0001001",
    "9": "0010111",
}
R_CODES = {
    "0": "1110010",
    "1": "1100110",
    "2": "1101100",
    "3": "1000010",
    "4": "1011100",
    "5": "1001110",
    "6": "1010000",
    "7": "1000100",
    "8": "1001000",
    "9": "1110100",
}
FIRST_DIGIT_PATTERNS = {
    "0": "LLLLLL",
    "1": "LLGLGG",
    "2": "LLGGLG",
    "3": "LLGGGL",
    "4": "LGLLGG",
    "5": "LGGLLG",
    "6": "LGGGLL",
    "7": "LGLGLG",
    "8": "LGLGGL",
    "9": "LGGLGL",
}

# Data — German product code (Bosch drill bit set)
code_input = "4006381333931"
digits_12 = code_input[:12]
total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits_12))
check = str((10 - (total % 10)) % 10)
full_code = digits_12 + check

# Encode EAN-13: start guard → left group → center guard → right group → end guard
binary = "101"
pattern = FIRST_DIGIT_PATTERNS[full_code[0]]
for i, digit in enumerate(full_code[1:7]):
    binary += L_CODES[digit] if pattern[i] == "L" else G_CODES[digit]
binary += "01010"
for digit in full_code[7:]:
    binary += R_CODES[digit]
binary += "101"

# Axis coordinate system: 1 unit = 1 module, quiet zones on each side
QZ = 9  # quiet zone modules
X_TOTAL = QZ * 2 + 95  # 113 total modules on axis

# xrange series data: each 1-bit → a bar rectangle (x, x2, y=0, color)
bars_data = [{"x": QZ + i, "x2": QZ + i + 1, "y": 0, "color": BAR_COLOR} for i, bit in enumerate(binary) if bit == "1"]
bars_data_json = json.dumps(bars_data)

# Guard 1-bit x positions (start/center/end guards) for taller bar overlays
guard_x_units = [QZ + i for i, bit in enumerate(binary) if bit == "1" and (i < 3 or (45 <= i < 50) or i >= 92)]
guard_x_units_js = json.dumps(guard_x_units)

# Digit label x positions in axis units and the 13 digit characters
digit_x_units = (
    [QZ - 4.0]  # first digit: left of start guard
    + [QZ + 3 + i * 7 + 3.5 for i in range(6)]  # left group digits 1-6
    + [QZ + 50 + i * 7 + 3.5 for i in range(6)]  # right group digits 7-12
)
digit_x_units_js = json.dumps(digit_x_units)
digits_json = json.dumps(list(full_code))

# Canvas layout
W, H = 3200, 1800
MARGIN_T, MARGIN_R, MARGIN_B, MARGIN_L = 220, 200, 280, 200
BAR_H = 700  # data bar height px (xrange pointWidth)
GUARD_H = 820  # guard bar height px (extends below data bars)

# Download Highcharts core + xrange module (inline embedding for headless Chrome)
hc_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/12.2.0/highcharts.js"
hc_xrange_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/12.2.0/modules/xrange.js"
with urllib.request.urlopen(hc_url, timeout=30) as r:
    highcharts_js = r.read().decode("utf-8")
with urllib.request.urlopen(hc_xrange_url, timeout=30) as r:
    highcharts_xrange_js = r.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_xrange_js}</script>
</head>
<body style="margin:0;padding:0;background:{PAGE_BG};">
    <div id="container" style="width:{W}px;height:{H}px;"></div>
    <script>
    var chart = Highcharts.chart('container', {{
        chart: {{
            type: 'xrange',
            width: {W},
            height: {H},
            backgroundColor: '{PAGE_BG}',
            plotBackgroundColor: '{BARCODE_BG}',
            plotBorderWidth: 0,
            margin: [{MARGIN_T}, {MARGIN_R}, {MARGIN_B}, {MARGIN_L}],
            animation: false,
            events: {{
                load: function () {{
                    var c = this;
                    var xa = c.xAxis[0];
                    var plotT = c.plotTop;
                    var plotH = c.plotHeight;

                    // Data bars (xrange) are centered in the plot area at pointWidth={BAR_H}
                    var dataBarTop = plotT + plotH / 2 - {BAR_H} / 2;
                    var dataBarBot = dataBarTop + {BAR_H};
                    var guardExt = {GUARD_H} - {BAR_H};  // extra 120 px below data bars

                    // Guard bar extensions via Highcharts SVG Renderer
                    var guardXUnits = {guard_x_units_js};
                    guardXUnits.forEach(function (xu) {{
                        var px = xa.toPixels(xu);
                        var pw = xa.toPixels(xu + 1) - px;
                        c.renderer.rect(px, dataBarBot, pw, guardExt)
                            .attr({{'stroke-width': 0, fill: '{BAR_COLOR}', zIndex: 5}})
                            .add();
                    }});

                    // Human-readable digit labels below the barcode
                    var digitY = dataBarBot + guardExt + 100;
                    var digitXUnits = {digit_x_units_js};
                    var digits = {digits_json};
                    digitXUnits.forEach(function (xu, i) {{
                        var px = xa.toPixels(xu);
                        c.renderer.text(digits[i], px, digitY)
                            .attr({{align: 'center', zIndex: 6}})
                            .css({{
                                fontSize: '80px',
                                fontWeight: 'bold',
                                color: '{BAR_COLOR}',
                                fontFamily: 'Arial, sans-serif'
                            }})
                            .add();
                    }});
                }}
            }}
        }},
        title: {{
            text: 'barcode-ean13 · python · highcharts · anyplot.ai',
            style: {{
                fontSize: '66px',
                fontWeight: 'bold',
                color: '{INK}',
                fontFamily: 'Arial, sans-serif'
            }},
            y: 70
        }},
        subtitle: {{
            text: 'EAN-13: {full_code}',
            style: {{
                fontSize: '48px',
                color: '{INK_SOFT}',
                fontFamily: 'Arial, sans-serif'
            }},
            y: 155
        }},
        tooltip: {{enabled: false}},
        credits: {{enabled: false}},
        legend: {{enabled: false}},
        xAxis: {{
            min: 0,
            max: {X_TOTAL},
            visible: false
        }},
        yAxis: {{
            min: -0.5,
            max: 0.5,
            visible: false
        }},
        plotOptions: {{
            xrange: {{
                pointWidth: {BAR_H},
                borderWidth: 0,
                borderRadius: 0,
                grouping: false,
                animation: false,
                states: {{hover: {{enabled: false}}}}
            }}
        }},
        series: [{{
            type: 'xrange',
            name: 'EAN-13 Barcode',
            data: {bars_data_json}
        }}]
    }});
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome with exact viewport control
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument(f"--window-size={W},{H}")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dimensions (safety net for ±1-2 px rounding)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.size != (W, H):
    norm = Image.new("RGB", (W, H), PAGE_BG)
    norm.paste(img, ((W - img.size[0]) // 2, (H - img.size[1]) // 2))
    norm.save(f"plot-{THEME}.png")
