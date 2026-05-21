""" anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-21
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    geom_rect,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    scale_fill_identity,
    theme,
    theme_void,
    xlim,
    ylim,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BAR_COLOR = "#1A1A17" if THEME == "light" else "#F0EFE8"

# EAN-13 encoding patterns (L, G, R codes — 7 modules each)
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
# Parity patterns for left-side digits based on first digit
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


def calculate_check_digit(digits_12):
    total = 0
    for i, d in enumerate(digits_12):
        weight = 1 if i % 2 == 0 else 3
        total += int(d) * weight
    return str((10 - (total % 10)) % 10)


def encode_ean13(code):
    if len(code) == 12:
        code = code + calculate_check_digit(code)
    elif len(code) != 13:
        raise ValueError("EAN-13 code must be 12 or 13 digits")

    first_digit = code[0]
    left_digits = code[1:7]
    right_digits = code[7:13]
    pattern = FIRST_DIGIT_PATTERNS[first_digit]

    # Start guard: 101
    bars = "101"
    for i, digit in enumerate(left_digits):
        bars += L_CODES[digit] if pattern[i] == "L" else G_CODES[digit]
    # Center guard: 01010
    bars += "01010"
    for digit in right_digits:
        bars += R_CODES[digit]
    # End guard: 101
    bars += "101"

    return bars, code


def generate_barcode_bars(code, bar_y_min, bar_y_max, guard_y_max, module_width, bar_color):
    bars_pattern, full_code = encode_ean13(code)

    # Guard bar bit positions (start, center, end) — extend lower than regular bars
    guard_positions = set(range(3))  # Start guard: bits 0-2
    guard_positions.update(range(45, 50))  # Center guard: bits 45-49
    guard_positions.update(range(92, 95))  # End guard: bits 92-94

    all_bars = []
    x_pos = 9 * module_width  # quiet zone

    for i, bit in enumerate(bars_pattern):
        if bit == "1":
            y_max = guard_y_max if i in guard_positions else bar_y_max
            all_bars.append(
                {
                    "xmin": float(x_pos),
                    "xmax": float(x_pos + module_width),
                    "ymin": float(bar_y_min),
                    "ymax": float(y_max),
                    "fill": bar_color,
                }
            )
        x_pos += module_width

    total_width = x_pos + 9 * module_width  # add right quiet zone
    return all_bars, total_width, full_code


# Data — German product EAN-13
code = "4006381333931"
module_width = 3
bar_y_min = 35
bar_y_max = bar_y_min + 80  # 80-unit bar height
guard_y_max = bar_y_max + 10  # guard bars extend 10 units lower

bars_data, total_width, full_code = generate_barcode_bars(
    code, bar_y_min, bar_y_max, guard_y_max, module_width, BAR_COLOR
)
df_bars = pd.DataFrame(bars_data)

# Digit label positions
quiet_zone = 9 * module_width
start_guard_end = quiet_zone + 3 * module_width  # left edge of left digits
left_digit_width = 7 * module_width
center_guard_start = start_guard_end + 42 * module_width
right_start = center_guard_start + 5 * module_width

text_y = bar_y_min - 15
digit_labels = []

# First digit sits outside the left guard
digit_labels.append({"x": quiet_zone - 5 * module_width, "y": text_y, "label": full_code[0]})

# Left-side digits (positions 1-6)
for i, digit in enumerate(full_code[1:7]):
    x = start_guard_end + (i + 0.5) * left_digit_width
    digit_labels.append({"x": x, "y": text_y, "label": digit})

# Right-side digits (positions 7-12)
for i, digit in enumerate(full_code[7:13]):
    x = right_start + (i + 0.5) * left_digit_width
    digit_labels.append({"x": x, "y": text_y, "label": digit})

df_digits = pd.DataFrame(digit_labels)

title_str = "barcode-ean13 · python · letsplot · anyplot.ai"
df_title = pd.DataFrame({"x": [total_width / 2], "y": [guard_y_max + 25], "label": [title_str]})

# Plot
plot = (
    ggplot()
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"), data=df_bars)
    + scale_fill_identity()
    + geom_text(aes(x="x", y="y", label="label"), data=df_digits, size=16, family="monospace", color=INK)
    + geom_text(aes(x="x", y="y", label="label"), data=df_title, size=11, color=INK_SOFT)
    + xlim(0, total_width)
    + ylim(0, guard_y_max + 45)
    + theme_void()
    + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG), panel_background=element_rect(fill=PAGE_BG))
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
