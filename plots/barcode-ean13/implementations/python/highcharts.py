"""anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: highcharts | Python 3.13
Quality: 91/100 | Updated: 2026-05-21
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Barcode paper/ink: always high-contrast regardless of page theme
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

# Compute/verify check digit
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

# Barcode dimensions scaled for 3200×1800 canvas
bar_width = 17
bar_height = 700
guard_height = 820
bar_baseline = 880
quiet_zone = 9 * bar_width
total_barcode_width = quiet_zone * 2 + 95 * bar_width
svg_height = 1050

# Build SVG bar elements
bars_svg = ""
current_x = quiet_zone
for i, bit in enumerate(binary):
    is_guard = i < 3 or (45 <= i < 50) or i >= 92
    h = guard_height if is_guard else bar_height
    if bit == "1":
        bars_svg += (
            f'<rect x="{current_x}" y="{bar_baseline - h}" width="{bar_width}" height="{h}" fill="{BAR_COLOR}"/>\n'
        )
    current_x += bar_width

# Build SVG digit label elements
digit_font = 80
digit_y = 970
digits_svg = ""

# First digit — positioned left of the start guard
first_x = quiet_zone - 4 * bar_width
digits_svg += (
    f'<text x="{first_x}" y="{digit_y}" font-size="{digit_font}" '
    f'font-family="Arial, sans-serif" font-weight="bold" '
    f'text-anchor="middle" fill="{BAR_COLOR}">{full_code[0]}</text>\n'
)

# Left 6 digits (full_code[1:7])
left_start = quiet_zone + 3 * bar_width
for i in range(6):
    cx = left_start + (i * 7 + 3.5) * bar_width
    digits_svg += (
        f'<text x="{cx}" y="{digit_y}" font-size="{digit_font}" '
        f'font-family="Arial, sans-serif" font-weight="bold" '
        f'text-anchor="middle" fill="{BAR_COLOR}">{full_code[i + 1]}</text>\n'
    )

# Right 6 digits (full_code[7:13])
right_start = quiet_zone + (3 + 42 + 5) * bar_width
for i in range(6):
    cx = right_start + (i * 7 + 3.5) * bar_width
    digits_svg += (
        f'<text x="{cx}" y="{digit_y}" font-size="{digit_font}" '
        f'font-family="Arial, sans-serif" font-weight="bold" '
        f'text-anchor="middle" fill="{BAR_COLOR}">{full_code[i + 7]}</text>\n'
    )

# Download Highcharts JS for inline embedding (required in headless Chrome)
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/12.2.0/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build HTML — 3200×1800 flex container with theme-adaptive chrome
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div style="width:3200px; height:1800px; display:flex; flex-direction:column;
                align-items:center; justify-content:center; background:{PAGE_BG};">
        <div style="font-size:66px; font-weight:bold; color:{INK}; margin-bottom:30px;
                    text-align:center; font-family:Arial, sans-serif;">
            barcode-ean13 · python · highcharts · anyplot.ai
        </div>
        <div style="font-size:48px; color:{INK_SOFT}; margin-bottom:60px;
                    font-family:Arial, sans-serif;">
            EAN-13: {full_code}
        </div>
        <div style="background:{BARCODE_BG}; padding:60px 80px; border-radius:16px;
                    box-shadow:0 4px 24px rgba(0,0,0,0.12);">
            <svg width="{total_barcode_width}" height="{svg_height}"
                 viewBox="0 0 {total_barcode_width} {svg_height}">
                <rect x="0" y="0" width="{total_barcode_width}" height="{svg_height}"
                      fill="{BARCODE_BG}"/>
                {bars_svg}
                {digits_svg}
            </svg>
        </div>
    </div>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take PNG screenshot via Selenium with exact viewport control
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 3200×1800 (safety net for ±1-2 px rounding)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.size != (3200, 1800):
    norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    norm.paste(img, ((3200 - img.size[0]) // 2, (1800 - img.size[1]) // 2))
    norm.save(f"plot-{THEME}.png")
