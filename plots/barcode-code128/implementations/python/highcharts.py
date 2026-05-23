""" anyplot.ai
barcode-code128: Code 128 Barcode
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-21
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

# Code 128 encoding tables (value: (pattern, Code A, Code B, Code C))
CODE128_PATTERNS = {
    0: ("212222", " ", " ", "00"),
    1: ("222122", "!", "!", "01"),
    2: ("222221", '"', '"', "02"),
    3: ("121223", "#", "#", "03"),
    4: ("121322", "$", "$", "04"),
    5: ("131222", "%", "%", "05"),
    6: ("122213", "&", "&", "06"),
    7: ("122312", "'", "'", "07"),
    8: ("132212", "(", "(", "08"),
    9: ("221213", ")", ")", "09"),
    10: ("221312", "*", "*", "10"),
    11: ("231212", "+", "+", "11"),
    12: ("112232", ",", ",", "12"),
    13: ("122132", "-", "-", "13"),
    14: ("122231", ".", ".", "14"),
    15: ("113222", "/", "/", "15"),
    16: ("123122", "0", "0", "16"),
    17: ("123221", "1", "1", "17"),
    18: ("223211", "2", "2", "18"),
    19: ("221132", "3", "3", "19"),
    20: ("221231", "4", "4", "20"),
    21: ("213212", "5", "5", "21"),
    22: ("223112", "6", "6", "22"),
    23: ("312131", "7", "7", "23"),
    24: ("311222", "8", "8", "24"),
    25: ("321122", "9", "9", "25"),
    26: ("321221", ":", ":", "26"),
    27: ("312212", ";", ";", "27"),
    28: ("322112", "<", "<", "28"),
    29: ("322211", "=", "=", "29"),
    30: ("212123", ">", ">", "30"),
    31: ("212321", "?", "?", "31"),
    32: ("232121", "@", "@", "32"),
    33: ("111323", "A", "A", "33"),
    34: ("131123", "B", "B", "34"),
    35: ("131321", "C", "C", "35"),
    36: ("112313", "D", "D", "36"),
    37: ("132113", "E", "E", "37"),
    38: ("132311", "F", "F", "38"),
    39: ("211313", "G", "G", "39"),
    40: ("231113", "H", "H", "40"),
    41: ("231311", "I", "I", "41"),
    42: ("112133", "J", "J", "42"),
    43: ("112331", "K", "K", "43"),
    44: ("132131", "L", "L", "44"),
    45: ("113123", "M", "M", "45"),
    46: ("113321", "N", "N", "46"),
    47: ("133121", "O", "O", "47"),
    48: ("313121", "P", "P", "48"),
    49: ("211331", "Q", "Q", "49"),
    50: ("231131", "R", "R", "50"),
    51: ("213113", "S", "S", "51"),
    52: ("213311", "T", "T", "52"),
    53: ("213131", "U", "U", "53"),
    54: ("311123", "V", "V", "54"),
    55: ("311321", "W", "W", "55"),
    56: ("331121", "X", "X", "56"),
    57: ("312113", "Y", "Y", "57"),
    58: ("312311", "Z", "Z", "58"),
    59: ("332111", "[", "[", "59"),
    60: ("314111", "\\", "\\", "60"),
    61: ("221411", "]", "]", "61"),
    62: ("431111", "^", "^", "62"),
    63: ("111224", "_", "_", "63"),
    64: ("111422", "NUL", "`", "64"),
    65: ("121124", "SOH", "a", "65"),
    66: ("121421", "STX", "b", "66"),
    67: ("141122", "ETX", "c", "67"),
    68: ("141221", "EOT", "d", "68"),
    69: ("112214", "ENQ", "e", "69"),
    70: ("112412", "ACK", "f", "70"),
    71: ("122114", "BEL", "g", "71"),
    72: ("122411", "BS", "h", "72"),
    73: ("142112", "HT", "i", "73"),
    74: ("142211", "LF", "j", "74"),
    75: ("241211", "VT", "k", "75"),
    76: ("221114", "FF", "l", "76"),
    77: ("413111", "CR", "m", "77"),
    78: ("241112", "SO", "n", "78"),
    79: ("134111", "SI", "o", "79"),
    80: ("111242", "DLE", "p", "80"),
    81: ("121142", "DC1", "q", "81"),
    82: ("121241", "DC2", "r", "82"),
    83: ("114212", "DC3", "s", "83"),
    84: ("124112", "DC4", "t", "84"),
    85: ("124211", "NAK", "u", "85"),
    86: ("411212", "SYN", "v", "86"),
    87: ("421112", "ETB", "w", "87"),
    88: ("421211", "CAN", "x", "88"),
    89: ("212141", "EM", "y", "89"),
    90: ("214121", "SUB", "z", "90"),
    91: ("412121", "ESC", "{", "91"),
    92: ("111143", "FS", "|", "92"),
    93: ("111341", "GS", "}", "93"),
    94: ("131141", "RS", "~", "94"),
    95: ("114113", "US", "DEL", "95"),
    96: ("114311", "FNC3", "FNC3", "96"),
    97: ("411113", "FNC2", "FNC2", "97"),
    98: ("411311", "SHIFT", "SHIFT", "98"),
    99: ("113141", "CODE_C", "CODE_C", "99"),
    100: ("114131", "CODE_B", "FNC4", "CODE_B"),
    101: ("311141", "FNC4", "CODE_A", "CODE_A"),
    102: ("411131", "FNC1", "FNC1", "FNC1"),
    103: ("211412", "START_A", "START_A", "START_A"),
    104: ("211214", "START_B", "START_B", "START_B"),
    105: ("211232", "START_C", "START_C", "START_C"),
    106: ("2331112", "STOP", "STOP", "STOP"),
}

# Reverse lookup: Code B character → value
CODE_B_LOOKUP = {data[2]: val for val, data in CODE128_PATTERNS.items() if val < 103}

# Data — a realistic shipping label barcode
content = "SHIP-2024-ABC123"

# Encode Code 128B: Start B → data chars → check digit → Stop
values = [104]  # START_B
for char in content:
    values.append(CODE_B_LOOKUP.get(char, 0))
checksum = values[0]
for i, v in enumerate(values[1:], 1):
    checksum += i * v
values.append(checksum % 103)
values.append(106)  # STOP

# Build bar positions (black bars only; alternating black/white starts black)
bars = []
x_pos = 0
is_black = True
for v in values:
    for ch in CODE128_PATTERNS[v][0]:
        width = int(ch)
        if is_black:
            bars.append({"x": x_pos, "width": width})
        x_pos += width
        is_black = not is_black
total_barcode_width = x_pos

# Structural widths for structural annotations
start_w = sum(int(c) for c in CODE128_PATTERNS[104][0])  # START_B pattern
stop_w = sum(int(c) for c in CODE128_PATTERNS[106][0])  # STOP pattern
check_digit_val = values[-2]
check_w = sum(int(c) for c in CODE128_PATTERNS[check_digit_val][0])
data_span = total_barcode_width - start_w - check_w - stop_w  # pure data chars

# Quiet zones in barcode units (~12% each side, standard recommends ≥10x narrowest bar)
quiet_zone_units = int(total_barcode_width * 0.12)

# xrange series data — each black bar becomes a {x, x2, y, color} point
# x-axis spans 0..x_total (quiet zone + barcode + quiet zone)
x_total = total_barcode_width + 2 * quiet_zone_units
bars_data = [
    {"x": b["x"] + quiet_zone_units, "x2": b["x"] + b["width"] + quiet_zone_units, "y": 0, "color": "#000000"}
    for b in bars
]

# Canvas layout
W, H = 3200, 1800
MARGIN_T, MARGIN_R, MARGIN_B, MARGIN_L = 200, 200, 200, 200
PLOT_W = W - MARGIN_L - MARGIN_R  # 2600
PLOT_H = H - MARGIN_T - MARGIN_B  # 1400

POINT_WIDTH = 950  # xrange bar height in pixels (68% of plot height)

# Vertical pixel positions
bar_cy = MARGIN_T + PLOT_H // 2  # 900
bar_top_px = bar_cy - POINT_WIDTH // 2  # 425
bar_bot_px = bar_cy + POINT_WIDTH // 2  # 1375
annot_y = bar_bot_px + 60  # 1435 — zone labels inside white box
human_y = bar_bot_px + 155  # 1530 — human-readable text
footer_y = H - 70  # 1730 — technical footer


def bx_to_px(bx_units: float) -> float:
    """Barcode x-units → absolute canvas pixel x."""
    return MARGIN_L + (bx_units / x_total) * PLOT_W


# Horizontal annotation anchor pixels
qz_left_cx = bx_to_px(quiet_zone_units / 2)
qz_right_cx = bx_to_px(x_total - quiet_zone_units / 2)
start_cx = bx_to_px(quiet_zone_units + start_w / 2)
data_cx = bx_to_px(quiet_zone_units + start_w + data_span / 2)
check_cx = bx_to_px(quiet_zone_units + start_w + data_span + check_w / 2)
stop_cx = bx_to_px(quiet_zone_units + total_barcode_width - stop_w / 2)

# Divider tick positions (vertical rules between zones, drawn as 1px rects)
div_xs = [
    bx_to_px(quiet_zone_units),  # after left QZ
    bx_to_px(quiet_zone_units + start_w),  # after START
    bx_to_px(quiet_zone_units + start_w + data_span),  # after DATA
    bx_to_px(quiet_zone_units + start_w + data_span + check_w),  # after CHECK
    bx_to_px(x_total - quiet_zone_units),  # before right QZ
]
div_ticks_js = "\n                        ".join(
    f"c.renderer.rect({x:.1f},{annot_y - 20},1,42,0).attr({{fill:'#C8C5B8','stroke-width':0}}).add();" for x in div_xs
)

# Download Highcharts core + xrange module (inline for headless Chrome)
hc_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/12.2.0/highcharts.js"
hc_xrange_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/12.2.0/modules/xrange.js"
with urllib.request.urlopen(hc_url, timeout=30) as r:
    highcharts_js = r.read().decode("utf-8")
with urllib.request.urlopen(hc_xrange_url, timeout=30) as r:
    highcharts_xrange_js = r.read().decode("utf-8")

bars_data_json = json.dumps(bars_data)

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
            plotBackgroundColor: '#FFFFFF',
            plotBorderWidth: 1,
            plotBorderColor: '#DDDDCC',
            margin: [{MARGIN_T}, {MARGIN_R}, {MARGIN_B}, {MARGIN_L}],
            events: {{
                load: function() {{
                    var c = this;

                    /* ── Zone divider ticks ── */
                    {div_ticks_js}

                    /* ── Zone labels (annotation strip) ── */
                    c.renderer.text('← Quiet Zone', {qz_left_cx:.1f}, {annot_y})
                        .attr({{align:'center'}})
                        .css({{fontSize:'28px',color:'#999990',fontStyle:'italic'}})
                        .add();
                    c.renderer.text('START B', {start_cx:.1f}, {annot_y})
                        .attr({{align:'center'}})
                        .css({{fontSize:'28px',color:'#555550',fontWeight:'bold',letterSpacing:'2px'}})
                        .add();
                    c.renderer.text('DATA  ({len(content)} chars · Subset B)', {data_cx:.1f}, {annot_y})
                        .attr({{align:'center'}})
                        .css({{fontSize:'28px',color:'#444440'}})
                        .add();
                    c.renderer.text('CHK', {check_cx:.1f}, {annot_y})
                        .attr({{align:'center'}})
                        .css({{fontSize:'28px',color:'#777770'}})
                        .add();
                    c.renderer.text('STOP', {stop_cx:.1f}, {annot_y})
                        .attr({{align:'center'}})
                        .css({{fontSize:'28px',color:'#555550',fontWeight:'bold',letterSpacing:'2px'}})
                        .add();
                    c.renderer.text('Quiet Zone →', {qz_right_cx:.1f}, {annot_y})
                        .attr({{align:'center'}})
                        .css({{fontSize:'28px',color:'#999990',fontStyle:'italic'}})
                        .add();

                    /* ── Human-readable text ── */
                    c.renderer.text('{content}', {W // 2}, {human_y})
                        .attr({{align:'center'}})
                        .css({{fontSize:'54px',fontFamily:'"Courier New",Courier,monospace',
                               fontWeight:'bold',color:'#000000',letterSpacing:'8px'}})
                        .add();

                    /* ── Technical footer ── */
                    c.renderer.text(
                        'Code 128B · Subset B encodes ASCII 32–126 (printable) · Subset C encodes numeric pairs (2× density) · Check digit: mod 103',
                        {W // 2}, {footer_y})
                        .attr({{align:'center'}})
                        .css({{fontSize:'34px',color:'{INK_SOFT}'}})
                        .add();
                }}
            }}
        }},
        title: {{
            text: 'barcode-code128 · python · highcharts · anyplot.ai',
            style: {{fontSize:'66px',fontWeight:'bold',color:'{INK}'}},
            margin: 30
        }},
        tooltip: {{enabled: false}},
        credits: {{enabled: false}},
        legend: {{enabled: false}},
        xAxis: {{
            min: 0,
            max: {x_total},
            visible: false
        }},
        yAxis: {{
            min: -0.5,
            max: 0.5,
            visible: false
        }},
        plotOptions: {{
            xrange: {{
                pointWidth: {POINT_WIDTH},
                borderWidth: 0,
                grouping: false,
                states: {{hover: {{enabled: false}}}}
            }}
        }},
        series: [{{
            type: 'xrange',
            name: 'Code 128B Barcode',
            data: {bars_data_json}
        }}]
    }});
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome
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

# Normalize to exact canvas dimensions
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.size != (W, H):
    norm = Image.new("RGB", (W, H), PAGE_BG)
    norm.paste(img, ((W - img.size[0]) // 2, (H - img.size[1]) // 2))
    norm.save(f"plot-{THEME}.png")
