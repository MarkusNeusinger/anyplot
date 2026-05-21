"""anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: plotly 6.7.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-21
"""

import os
import sys


# Prevent this file (plotly.py) from shadowing the installed plotly package
sys.path = [p for p in sys.path if p not in ("", os.path.dirname(os.path.abspath(__file__)))]

import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BAR_COLOR = INK

# EAN-13 encoding patterns
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

# First digit determines L/G parity pattern for left side
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

# German product EAN-13
ean_code = "4006381333931"

code = ean_code
if len(code) == 12:
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(code))
    code = code + str((10 - (total % 10)) % 10)

first_digit = code[0]
left_digits = code[1:7]
right_digits = code[7:13]

# Encode to binary
binary_pattern = "101"

lg_pattern = FIRST_DIGIT_PATTERNS[first_digit]
for i, digit in enumerate(left_digits):
    if lg_pattern[i] == "L":
        binary_pattern += L_CODES[digit]
    else:
        binary_pattern += G_CODES[digit]

binary_pattern += "01010"

for digit in right_digits:
    binary_pattern += R_CODES[digit]

binary_pattern += "101"

# Bar dimensions (in plot units)
module_width = 3
bar_height = 200
guard_height = 220
quiet_zone = 9 * module_width

# Guard bar positions: start (0-2), center (45-49), end (92-94)
guard_positions = set(range(0, 3)) | set(range(45, 50)) | set(range(92, 95))

fig = go.Figure()

x_pos = quiet_zone
for i, bit in enumerate(binary_pattern):
    if bit == "1":
        height = guard_height if i in guard_positions else bar_height
        fig.add_shape(
            type="rect", x0=x_pos, y0=0, x1=x_pos + module_width, y1=height, fillcolor=BAR_COLOR, line={"width": 0}
        )
    x_pos += module_width

total_width = quiet_zone * 2 + len(binary_pattern) * module_width

# Human-readable digits
digit_y = -35
font_size = 18

# First digit (outside left guard)
fig.add_annotation(
    x=quiet_zone - module_width * 4,
    y=digit_y,
    text=code[0],
    showarrow=False,
    font={"size": font_size, "family": "monospace", "color": INK},
)

# Left group: digits 2–7 under left bars
left_start = quiet_zone + 3 * module_width
for i, digit in enumerate(code[1:7]):
    x = left_start + (i + 0.5) * 7 * module_width
    fig.add_annotation(
        x=x, y=digit_y, text=digit, showarrow=False, font={"size": font_size, "family": "monospace", "color": INK}
    )

# Right group: digits 8–13 under right bars
right_start = quiet_zone + 3 * module_width + 42 * module_width + 5 * module_width
for i, digit in enumerate(code[7:13]):
    x = right_start + (i + 0.5) * 7 * module_width
    fig.add_annotation(
        x=x, y=digit_y, text=digit, showarrow=False, font={"size": font_size, "family": "monospace", "color": INK}
    )

# Segment labels: Country (GS1 prefix), Manufacturer, Product, Check
segment_y = -65
x_first = quiet_zone - module_width * 4
x_country = (x_first + left_start + 0.5 * 7 * module_width + left_start + 1.5 * 7 * module_width) / 3
x_manuf = left_start + 4.0 * 7 * module_width
x_product = right_start + 2.5 * 7 * module_width
x_check = right_start + 5.5 * 7 * module_width
for x, label in [(x_country, "Country"), (x_manuf, "Manufacturer"), (x_product, "Product"), (x_check, "Check")]:
    fig.add_annotation(x=x, y=segment_y, text=label, showarrow=False, font={"size": 9, "color": INK_SOFT})

fig.update_layout(
    autosize=False,
    title={
        "text": "barcode-ean13 · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"visible": False, "range": [-20, total_width + 20]},
    yaxis={"visible": False, "range": [-100, guard_height + 20]},
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    width=800,
    height=450,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
