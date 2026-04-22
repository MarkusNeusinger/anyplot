""" pyplots.ai
barcode-ean13: EAN-13 Barcode
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-19
"""

import altair as alt
import pandas as pd


# EAN-13 encoding patterns (7 modules per digit)
# L-codes (left side, odd parity) - pattern: space, bar, space, bar
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

# G-codes (left side, even parity) - pattern: space, bar, space, bar
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

# R-codes (right side) - pattern: bar, space, bar, space
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


# Calculate EAN-13 check digit
def calc_check_digit(code12):
    total = 0
    for i, digit in enumerate(code12):
        weight = 1 if i % 2 == 0 else 3
        total += int(digit) * weight
    return str((10 - (total % 10)) % 10)


# Data - Example EAN-13 code (German product)
code = "4006381333931"

# If only 12 digits, calculate check digit
if len(code) == 12:
    code = code + calc_check_digit(code)

first_digit = code[0]
left_digits = code[1:7]
right_digits = code[7:13]

# Build barcode pattern
bars_data = []
x_pos = 0

# Quiet zone (9 modules minimum)
quiet_zone = 9

# Start with quiet zone
x_pos = quiet_zone

# Start guard: 101 (bar, space, bar)
start_guard = [1, 1, 1]
is_bar = True
for width in start_guard:
    if is_bar:
        bars_data.append({"x": x_pos, "x2": x_pos + width, "y": 0, "y2": 1.1, "is_guard": True})
    x_pos += width
    is_bar = not is_bar

# Get encoding pattern based on first digit
encoding_pattern = FIRST_DIGIT_PATTERNS[first_digit]

# Encode left 6 digits (using L or G codes based on first digit)
is_bar = False  # L and G codes start with space
for i, digit in enumerate(left_digits):
    if encoding_pattern[i] == "L":
        widths = L_CODES[digit]
    else:
        widths = G_CODES[digit]
    for width in widths:
        if is_bar:
            bars_data.append({"x": x_pos, "x2": x_pos + width, "y": 0, "y2": 1.0, "is_guard": False})
        x_pos += width
        is_bar = not is_bar

# Center guard: 01010 (space, bar, space, bar, space)
center_guard = [1, 1, 1, 1, 1]
is_bar = False
for width in center_guard:
    if is_bar:
        bars_data.append({"x": x_pos, "x2": x_pos + width, "y": 0, "y2": 1.1, "is_guard": True})
    x_pos += width
    is_bar = not is_bar

# Encode right 6 digits (using R codes, starting with bar)
is_bar = True
for digit in right_digits:
    widths = R_CODES[digit]
    for width in widths:
        if is_bar:
            bars_data.append({"x": x_pos, "x2": x_pos + width, "y": 0, "y2": 1.0, "is_guard": False})
        x_pos += width
        is_bar = not is_bar

# End guard: 101 (bar, space, bar)
end_guard = [1, 1, 1]
is_bar = True
for width in end_guard:
    if is_bar:
        bars_data.append({"x": x_pos, "x2": x_pos + width, "y": 0, "y2": 1.1, "is_guard": True})
    x_pos += width
    is_bar = not is_bar

# Add right quiet zone
total_width = x_pos + quiet_zone

# Create DataFrame for bars
df_bars = pd.DataFrame(bars_data)

# Create text labels for human-readable digits
# First digit is positioned outside the left guard
# Left group (6 digits) centered under left half
# Right group (6 digits) centered under right half
text_data = [
    {"x": quiet_zone - 3, "y": -0.12, "text": first_digit},  # First digit outside
    {"x": quiet_zone + 3 + 21, "y": -0.12, "text": left_digits},  # Left 6 digits
    {"x": quiet_zone + 3 + 42 + 5 + 21, "y": -0.12, "text": right_digits},  # Right 6 digits
]
df_text = pd.DataFrame(text_data)

# Create barcode bars chart
bars_chart = (
    alt.Chart(df_bars)
    .mark_rect(color="black")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, total_width]), axis=None),
        x2="x2:Q",
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-0.25, 1.3]), axis=None),
        y2="y2:Q",
    )
)

# Create human-readable text below barcode
text_chart = (
    alt.Chart(df_text)
    .mark_text(fontSize=42, font="monospace", fontWeight="bold")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Combine charts
chart = (
    (bars_chart + text_chart)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("barcode-ean13 · altair · pyplots.ai", fontSize=32, anchor="middle", offset=20),
    )
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
