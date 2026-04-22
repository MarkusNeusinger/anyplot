""" pyplots.ai
barcode-ean13: EAN-13 Barcode
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-19
"""

import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    theme,
    theme_void,
)


# EAN-13 encoding patterns
# L-codes (left side, odd parity)
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

# G-codes (left side, even parity)
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

# R-codes (right side)
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

# First digit determines left side encoding pattern (L=0, G=1)
FIRST_DIGIT_PATTERN = {
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

# Guard patterns
START_GUARD = "101"
CENTER_GUARD = "01010"
END_GUARD = "101"

# EAN-13 code to encode (German product example)
code = "4006381333931"

# Calculate check digit if only 12 digits provided
if len(code) == 12:
    odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
    even_sum = sum(int(code[i]) for i in range(1, 12, 2))
    check = (10 - (odd_sum + even_sum * 3) % 10) % 10
    code = code + str(check)

# Build binary pattern
first_digit = code[0]
left_digits = code[1:7]
right_digits = code[7:13]
pattern = FIRST_DIGIT_PATTERN[first_digit]

binary = START_GUARD
for i, digit in enumerate(left_digits):
    if pattern[i] == "L":
        binary += L_CODES[digit]
    else:
        binary += G_CODES[digit]

binary += CENTER_GUARD

for digit in right_digits:
    binary += R_CODES[digit]

binary += END_GUARD

# Create bar data for plotnine
quiet_zone = 9  # Module widths
bars = []
x_pos = quiet_zone

for i, bit in enumerate(binary):
    if bit == "1":
        # Determine bar height (guards extend lower)
        is_guard = i < 3 or i >= len(binary) - 3 or (45 <= i < 50)
        bars.append({"xmin": x_pos, "xmax": x_pos + 1, "ymin": 0 if is_guard else 5, "ymax": 70})
    x_pos += 1

df_bars = pd.DataFrame(bars)

# Total width
total_width = quiet_zone * 2 + len(binary)

# Create digit labels with positions
digit_labels = []

# First digit (outside left guard)
digit_labels.append({"x": quiet_zone - 4, "y": -8, "label": first_digit})

# Left side digits (under bars, between start and center guards)
left_start = quiet_zone + 3  # After start guard
for i, digit in enumerate(left_digits):
    x = left_start + i * 7 + 3.5
    digit_labels.append({"x": x, "y": -8, "label": digit})

# Right side digits (under bars, between center and end guards)
right_start = quiet_zone + 3 + 42 + 5  # After center guard
for i, digit in enumerate(right_digits):
    x = right_start + i * 7 + 3.5
    digit_labels.append({"x": x, "y": -8, "label": digit})

df_labels = pd.DataFrame(digit_labels)

# Create plot
plot = (
    ggplot()
    + geom_rect(df_bars, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill="#000000", color="#000000")
    + geom_text(df_labels, aes(x="x", y="y", label="label"), size=14, family="monospace", fontweight="bold")
    + labs(title="barcode-ean13 · plotnine · pyplots.ai")
    + coord_fixed(ratio=1, xlim=(-2, total_width + 2), ylim=(-20, 85))
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", margin={"t": 20, "b": 20}),
        plot_background=element_blank(),
        panel_background=element_blank(),
    )
)

plot.save("plot.png", dpi=300)
