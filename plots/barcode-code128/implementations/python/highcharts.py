""" pyplots.ai
barcode-code128: Code 128 Barcode
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-19
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Code 128 encoding tables
# Each character is represented by a pattern of bar widths (alternating black/white)
# Pattern format: 6 elements representing bar widths (1-4 units each)
CODE128_PATTERNS = {
    # value: (pattern, Code A char, Code B char, Code C value)
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
    106: ("2331112", "STOP", "STOP", "STOP"),  # Stop pattern is 7 elements
}

# Build reverse lookup for Code B characters
CODE_B_LOOKUP = {}
for value, (_pattern, _char_a, char_b, _char_c) in CODE128_PATTERNS.items():
    if value < 103:  # Exclude special codes
        CODE_B_LOOKUP[char_b] = value


def encode_code128(content):
    """Encode a string to Code 128B barcode pattern."""
    # Use Code 128B (standard ASCII printable characters)
    values = [104]  # Start with Code B start character

    # Encode each character
    for char in content:
        if char in CODE_B_LOOKUP:
            values.append(CODE_B_LOOKUP[char])
        else:
            # For characters not in lookup, use space
            values.append(0)

    # Calculate check digit (modulo 103)
    checksum = values[0]  # Start character
    for i, value in enumerate(values[1:], start=1):
        checksum += i * value
    check_digit = checksum % 103
    values.append(check_digit)

    # Add stop character
    values.append(106)

    return values


def values_to_bars(values):
    """Convert Code 128 values to bar widths."""
    bars = []
    for value in values:
        pattern = CODE128_PATTERNS[value][0]
        for width in pattern:
            bars.append(int(width))
    return bars


# Data - Code 128 barcode content
content = "SHIP-2024-ABC123"

# Encode the content
encoded_values = encode_code128(content)
bar_widths = values_to_bars(encoded_values)

# Convert bar widths to actual bar data for rendering
# Each bar alternates between black and white, starting with black
bars = []
x_pos = 0
is_black = True

for width in bar_widths:
    if is_black:
        bars.append({"x": x_pos, "width": width, "color": "#000000"})
    x_pos += width
    is_black = not is_black

total_barcode_width = x_pos

# Chart dimensions
chart_width = 4800
chart_height = 2700

# Calculate scaling to fit barcode nicely in chart
quiet_zone = 400  # Quiet zones on each side
available_width = chart_width - (2 * quiet_zone)
scale_factor = available_width / total_barcode_width

# Barcode dimensions on chart
bar_height = 1400
bar_top = 500  # Y position for top of bars

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build JavaScript to render barcode bars as rectangles
bars_js = ""
for bar in bars:
    scaled_x = quiet_zone + (bar["x"] * scale_factor)
    scaled_width = max(bar["width"] * scale_factor, 3)  # Minimum 3px for visibility
    bars_js += f"""
    chart.renderer.rect({scaled_x}, {bar_top}, {scaled_width}, {bar_height}, 0)
        .attr({{fill: '{bar["color"]}', 'stroke-width': 0}})
        .add();
    """

# Human-readable text position
text_y = bar_top + bar_height + 120
text_x = chart_width / 2

# Generate HTML with Highcharts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        body {{ margin: 0; padding: 0; background: #ffffff; }}
        #container {{ width: 4800px; height: 2700px; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script>
        var chart = Highcharts.chart('container', {{
            chart: {{
                width: 4800,
                height: 2700,
                backgroundColor: '#ffffff',
                events: {{
                    load: function() {{
                        var chart = this;
                        // Render barcode bars as rectangles
                        {bars_js}
                        // Add human-readable text
                        chart.renderer.text('{content}', {text_x}, {text_y})
                            .attr({{align: 'center'}})
                            .css({{
                                fontSize: '72px',
                                fontFamily: '"Courier New", Courier, monospace',
                                fontWeight: 'bold',
                                color: '#000000',
                                letterSpacing: '8px'
                            }})
                            .add();
                    }}
                }}
            }},
            title: {{
                text: 'barcode-code128 \\u00b7 highcharts \\u00b7 pyplots.ai',
                style: {{fontSize: '48px', fontWeight: 'bold', color: '#333333'}},
                y: 100
            }},
            subtitle: {{
                text: 'Code 128 Barcode Visualization',
                style: {{fontSize: '32px', color: '#666666'}},
                y: 160
            }},
            credits: {{enabled: false}},
            legend: {{enabled: false}},
            xAxis: {{visible: false}},
            yAxis: {{visible: false}}
        }});
    </script>
</body>
</html>"""

# Save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Take screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
