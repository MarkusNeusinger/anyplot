""" anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-26
"""

import os

import pandas as pd
from plotnine import (
    aes,
    coord_cartesian,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    theme,
    theme_void,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

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

# Columns: names of the drawn tables
XMIN = "xmin"  # role: extra
XMAX = "xmax"  # role: extra
YMIN = "ymin"  # role: extra
YMAX = "ymax"  # role: extra
X = "x"  # role: extra
Y = "y"  # role: extra
LABEL = "label"  # role: extra

# Data: replace with your own 12 or 13 digit code (German product)
code = "4006381333931"

if len(code) == 12:
    odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
    even_sum = sum(int(code[i]) for i in range(1, 12, 2))
    check = (10 - (odd_sum + even_sum * 3) % 10) % 10
    code = code + str(check)

first_digit = code[0]
left_digits = code[1:7]
right_digits = code[7:13]
parity_pattern = FIRST_DIGIT_PATTERN[first_digit]

binary = "101"
for i, digit in enumerate(left_digits):
    binary += L_CODES[digit] if parity_pattern[i] == "L" else G_CODES[digit]
binary += "01010"
for digit in right_digits:
    binary += R_CODES[digit]
binary += "101"

# Plot
# Build bar rectangles (guards reach down to the digit baseline, data bars stop above the digit row)
quiet_zone = 9
DIGIT_Y = 0
DIGIT_BASE = -5
bars = []
x_pos = quiet_zone
for i, bit in enumerate(binary):
    if bit == "1":
        is_guard = i < 3 or i >= len(binary) - 3 or (45 <= i < 50)
        ymin = DIGIT_BASE if is_guard else 5
        if bars and bars[-1][XMAX] == x_pos and bars[-1][YMIN] == ymin:
            bars[-1][XMAX] = x_pos + 1  # merge a run of modules into one bar: no seams
        else:
            bars.append({XMIN: x_pos, XMAX: x_pos + 1, YMIN: ymin, YMAX: 70})
    x_pos += 1

df_bars = pd.DataFrame(bars)
total_width = quiet_zone * 2 + len(binary)

# Digit label positions
digit_labels = [{X: quiet_zone - 4, Y: DIGIT_Y, LABEL: first_digit}]
left_start = quiet_zone + 3
for i, digit in enumerate(left_digits):
    digit_labels.append({X: left_start + i * 7 + 3.5, Y: DIGIT_Y, LABEL: digit})
right_start = quiet_zone + 3 + 42 + 5
for i, digit in enumerate(right_digits):
    digit_labels.append({X: right_start + i * 7 + 3.5, Y: DIGIT_Y, LABEL: digit})

df_labels = pd.DataFrame(digit_labels)

plot = (
    ggplot()
    + geom_rect(df_bars, aes(xmin=XMIN, xmax=XMAX, ymin=YMIN, ymax=YMAX), fill=INK, color="none")
    + geom_text(df_labels, aes(x=X, y=Y, label=LABEL), size=14, color=INK, family="monospace", fontweight="bold")
    + labs(title="barcode-ean13 · python · plotnine · anyplot.ai")
    + coord_cartesian(xlim=(-2, total_width + 2), ylim=(-10, 74))
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, color=INK, ha="center", margin={"t": 6, "b": 2}),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
