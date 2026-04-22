""" pyplots.ai
barcode-ean13: EAN-13 Barcode
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-19
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


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


def calculate_check_digit(code_12):
    """Calculate EAN-13 check digit"""
    total = 0
    for i, digit in enumerate(code_12):
        weight = 1 if i % 2 == 0 else 3
        total += int(digit) * weight
    return str((10 - (total % 10)) % 10)


def encode_ean13(code):
    """Encode EAN-13 barcode to binary string"""
    if len(code) == 12:
        code = code + calculate_check_digit(code)
    elif len(code) != 13:
        raise ValueError("Code must be 12 or 13 digits")

    binary = "101"  # Start guard
    pattern = FIRST_DIGIT_PATTERNS[code[0]]

    for i, digit in enumerate(code[1:7]):
        if pattern[i] == "L":
            binary += L_CODES[digit]
        else:
            binary += G_CODES[digit]

    binary += "01010"  # Center guard

    for digit in code[7:]:
        binary += R_CODES[digit]

    binary += "101"  # End guard

    return binary, code


# Data - Example EAN-13 code (German product)
code_input = "4006381333931"
binary_pattern, full_code = encode_ean13(code_input)

# Build bar data for Highcharts
# We'll use xrange series type for precise bar positioning
bar_width = 8  # Width of each module in pixels
bar_height = 1200  # Height of regular bars
guard_height = 1350  # Guard bars extend lower

# Create series data - each bar as a separate data point
bars_data = []
current_x = 0

# Quiet zone (9 modules)
quiet_zone = 9 * bar_width
current_x = quiet_zone

# Process binary pattern and create bars
for i, bit in enumerate(binary_pattern):
    # Determine if this is a guard bar (extends lower)
    is_guard = False
    if i < 3:  # Start guard
        is_guard = True
    elif i >= 45 and i < 50:  # Center guard
        is_guard = True
    elif i >= 92:  # End guard
        is_guard = True

    if bit == "1":
        bars_data.append({"x": current_x, "y": guard_height if is_guard else bar_height, "color": "#000000"})
    current_x += bar_width

# Calculate positions for digit labels
digit_positions = []
module_start = quiet_zone

# First digit - left of barcode
digit_positions.append({"digit": full_code[0], "x": quiet_zone - 60})

# Left side digits (positions 1-6)
left_start = quiet_zone + 3 * bar_width  # After start guard
for i in range(6):
    center = left_start + (i * 7 + 3.5) * bar_width
    digit_positions.append({"digit": full_code[i + 1], "x": center})

# Right side digits (positions 7-12)
right_start = quiet_zone + (3 + 42 + 5) * bar_width  # After start guard + left + center guard
for i in range(6):
    center = right_start + (i * 7 + 3.5) * bar_width
    digit_positions.append({"digit": full_code[i + 7], "x": center})

# Total width
total_width = quiet_zone * 2 + 95 * bar_width

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build SVG rectangles for bars (more precise than column chart)
svg_bars = ""
for bar in bars_data:
    svg_bars += (
        f'<rect x="{bar["x"]}" y="{1500 - bar["y"]}" width="{bar_width}" height="{bar["y"]}" fill="{bar["color"]}"/>\n'
    )

# Build text elements for digits
svg_digits = ""
for dp in digit_positions:
    svg_digits += f'<text x="{dp["x"]}" y="1580" font-size="80" font-family="Arial, sans-serif" font-weight="bold" text-anchor="middle">{dp["digit"]}</text>\n'

# Create custom HTML with SVG barcode and Highcharts styling
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #FFFFFF;
            font-family: Arial, sans-serif;
        }}
        .container {{
            width: 4800px;
            height: 2700px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background-color: #FFFFFF;
        }}
        .title {{
            font-size: 64px;
            font-weight: bold;
            color: #306998;
            margin-bottom: 20px;
        }}
        .subtitle {{
            font-size: 48px;
            color: #666666;
            margin-bottom: 80px;
        }}
        .barcode-container {{
            background-color: #FFFFFF;
            padding: 60px 120px;
            border-radius: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="title">barcode-ean13 · highcharts · pyplots.ai</div>
        <div class="subtitle">EAN-13: {full_code}</div>
        <div class="barcode-container">
            <svg width="{total_width}" height="1700" viewBox="0 0 {total_width} 1700">
                <!-- White background -->
                <rect x="0" y="0" width="{total_width}" height="1700" fill="#FFFFFF"/>

                <!-- Barcode bars -->
                {svg_bars}

                <!-- Human-readable digits -->
                {svg_digits}
            </svg>
        </div>
    </div>
</body>
</html>"""

# Save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
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
time.sleep(3)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
