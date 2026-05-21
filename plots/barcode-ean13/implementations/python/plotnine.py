""" anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-21
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

# Data: German product EAN-13 code
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

# Build bar rectangles (guards extend to ymin=0, data bars start at ymin=5)
quiet_zone = 9
bars = []
x_pos = quiet_zone
for i, bit in enumerate(binary):
    if bit == "1":
        is_guard = i < 3 or i >= len(binary) - 3 or (45 <= i < 50)
        bars.append({"xmin": x_pos, "xmax": x_pos + 1, "ymin": 0 if is_guard else 5, "ymax": 70})
    x_pos += 1

df_bars = pd.DataFrame(bars)
total_width = quiet_zone * 2 + len(binary)

# Digit label positions
digit_labels = [{"x": quiet_zone - 4, "y": -8, "label": first_digit}]
left_start = quiet_zone + 3
for i, digit in enumerate(left_digits):
    digit_labels.append({"x": left_start + i * 7 + 3.5, "y": -8, "label": digit})
right_start = quiet_zone + 3 + 42 + 5
for i, digit in enumerate(right_digits):
    digit_labels.append({"x": right_start + i * 7 + 3.5, "y": -8, "label": digit})

df_labels = pd.DataFrame(digit_labels)

# Plot
plot = (
    ggplot()
    + geom_rect(df_bars, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill=INK, color=INK)
    + geom_text(df_labels, aes(x="x", y="y", label="label"), size=14, color=INK, family="monospace", fontweight="bold")
    + labs(title="barcode-ean13 · python · plotnine · anyplot.ai")
    + coord_cartesian(xlim=(-2, total_width + 2), ylim=(-14, 74))
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, color=INK, ha="center", margin={"t": 6, "b": 2}),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
