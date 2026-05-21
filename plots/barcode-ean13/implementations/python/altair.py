"""anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: altair | Python 3.13
Quality: pending | Updated: 2026-05-21
"""

import os
import sys


# Remove this script's directory from sys.path to prevent self-import
# (Python adds the script dir to sys.path[0], which would shadow the altair package)
_d = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _d]
del _d

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# EAN-13 encoding patterns (7 modules per digit)
# L-codes (left side, odd parity): space, bar, space, bar
L_CODES = {
    "0": [3, 2, 1, 1],
    "1": [2, 2, 2, 1],
    "2": [2, 1, 2, 2],
    "3": [1, 4, 1, 1],
    "4": [1, 1, 3, 2],
    "5": [1, 2, 3, 1],
    "6": [1, 1, 1, 4],
    "7": [1, 3, 1, 2],
    "8": [1, 2, 1, 3],
    "9": [3, 1, 1, 2],
}
# G-codes (left side, even parity): space, bar, space, bar
G_CODES = {
    "0": [1, 1, 2, 3],
    "1": [1, 2, 2, 2],
    "2": [2, 2, 1, 2],
    "3": [1, 1, 4, 1],
    "4": [2, 3, 1, 1],
    "5": [1, 3, 2, 1],
    "6": [4, 1, 1, 1],
    "7": [2, 1, 3, 1],
    "8": [3, 1, 2, 1],
    "9": [2, 1, 1, 3],
}
# R-codes (right side): bar, space, bar, space
R_CODES = {
    "0": [3, 2, 1, 1],
    "1": [2, 2, 2, 1],
    "2": [2, 1, 2, 2],
    "3": [1, 4, 1, 1],
    "4": [1, 1, 3, 2],
    "5": [1, 2, 3, 1],
    "6": [1, 1, 1, 4],
    "7": [1, 3, 1, 2],
    "8": [1, 2, 1, 3],
    "9": [3, 1, 1, 2],
}
# First digit determines L/G pattern for left 6 digits
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

# Data - German product EAN-13 code
code = "4006381333931"

# Inline check digit calculation (no function)
if len(code) == 12:
    _total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(code))
    code = code + str((10 - (_total % 10)) % 10)

first_digit = code[0]
left_digits = code[1:7]
right_digits = code[7:13]

# Build barcode bar data
bars_data = []
quiet_zone = 9
x_pos = quiet_zone

# Start guard: 101 (bar, space, bar)
for i, width in enumerate([1, 1, 1]):
    if i % 2 == 0:
        bars_data.append({"x": x_pos, "x2": x_pos + width, "y": 0, "y2": 1.1})
    x_pos += width

# Left 6 digits using L or G codes per first-digit pattern
encoding_pattern = FIRST_DIGIT_PATTERNS[first_digit]
is_bar = False
for i, digit in enumerate(left_digits):
    widths = L_CODES[digit] if encoding_pattern[i] == "L" else G_CODES[digit]
    for width in widths:
        if is_bar:
            bars_data.append({"x": x_pos, "x2": x_pos + width, "y": 0, "y2": 1.0})
        x_pos += width
        is_bar = not is_bar

# Center guard: 01010 (space, bar, space, bar, space)
for i, width in enumerate([1, 1, 1, 1, 1]):
    if i % 2 == 1:
        bars_data.append({"x": x_pos, "x2": x_pos + width, "y": 0, "y2": 1.1})
    x_pos += width

# Right 6 digits using R codes
is_bar = True
for digit in right_digits:
    for width in R_CODES[digit]:
        if is_bar:
            bars_data.append({"x": x_pos, "x2": x_pos + width, "y": 0, "y2": 1.0})
        x_pos += width
        is_bar = not is_bar

# End guard: 101 (bar, space, bar)
for i, width in enumerate([1, 1, 1]):
    if i % 2 == 0:
        bars_data.append({"x": x_pos, "x2": x_pos + width, "y": 0, "y2": 1.1})
    x_pos += width

total_width = x_pos + quiet_zone
df_bars = pd.DataFrame(bars_data)

# Human-readable digit labels positioned below barcode
text_data = [
    {"x": quiet_zone - 3, "y": -0.12, "text": first_digit},
    {"x": quiet_zone + 3 + 21, "y": -0.12, "text": left_digits},
    {"x": quiet_zone + 3 + 42 + 5 + 21, "y": -0.12, "text": right_digits},
]
df_text = pd.DataFrame(text_data)

# Barcode bars chart
bars_chart = (
    alt.Chart(df_bars)
    .mark_rect(color=INK)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, total_width]), axis=None),
        x2="x2:Q",
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-0.25, 1.3]), axis=None),
        y2="y2:Q",
    )
)

# Digit labels below barcode
text_chart = (
    alt.Chart(df_text)
    .mark_text(fontSize=16, font="monospace", fontWeight="bold", color=INK)
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Combined chart with canonical landscape canvas
TITLE = "barcode-ean13 · python · altair · anyplot.ai"
chart = (
    (bars_chart + text_chart)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(TITLE, fontSize=16, anchor="middle", offset=20, color=INK),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_title(color=INK)
)

# Save PNG with padding to exact 3200×1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
