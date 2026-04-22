""" pyplots.ai
barcode-ean13: EAN-13 Barcode
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-19
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
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

# EAN-13 encoding patterns
# L-codes (odd parity), G-codes (even parity), R-codes (right side)
# Each digit is encoded as 7 modules (bars/spaces)

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

# First digit encoding pattern (determines L/G pattern for digits 2-7)
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
    """Calculate EAN-13 check digit from first 12 digits."""
    total = 0
    for i, d in enumerate(digits_12):
        weight = 1 if i % 2 == 0 else 3
        total += int(d) * weight
    return str((10 - (total % 10)) % 10)


def encode_ean13(code):
    """Encode EAN-13 code to bar pattern string."""
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

    # Left side (digits 2-7, using L or G based on first digit)
    for i, digit in enumerate(left_digits):
        if pattern[i] == "L":
            bars += L_CODES[digit]
        else:
            bars += G_CODES[digit]

    # Center guard: 01010
    bars += "01010"

    # Right side (digits 8-13, always R-codes)
    for digit in right_digits:
        bars += R_CODES[digit]

    # End guard: 101
    bars += "101"

    return bars, code


def generate_barcode_bars(code, bar_y_min, bar_y_max, guard_y_max, module_width):
    """Generate barcode bar rectangles."""
    bars_pattern, full_code = encode_ean13(code)

    all_bars = []
    quiet_zone = 9 * module_width
    x_pos = quiet_zone

    # Track positions for guard bars (they extend lower)
    # Start guard: positions 0-2, Center guard: positions 45-49, End guard: positions 93-95
    guard_positions = set(range(3))  # Start guard
    guard_positions.update(range(45, 50))  # Center guard
    guard_positions.update(range(93, 96))  # End guard

    for i, bit in enumerate(bars_pattern):
        if bit == "1":
            y_max = guard_y_max if i in guard_positions else bar_y_max
            all_bars.append(
                {
                    "xmin": float(x_pos),
                    "xmax": float(x_pos + module_width),
                    "ymin": float(bar_y_min),
                    "ymax": float(y_max),
                    "fill": "#000000",
                }
            )
        x_pos += module_width

    total_width = x_pos + quiet_zone
    return all_bars, total_width, full_code


# Data - Example EAN-13 code (German product)
code = "4006381333931"

# Dimensions
module_width = 3
bar_y_min = 35
bar_height = 80
bar_y_max = bar_y_min + bar_height
guard_y_max = bar_y_max + 10  # Guard bars extend 10 units lower

# Generate barcode bars
bars_data, total_width, full_code = generate_barcode_bars(code, bar_y_min, bar_y_max, guard_y_max, module_width)

# Create DataFrame for bars
df_bars = pd.DataFrame(bars_data)

# Calculate digit positions for human-readable text
quiet_zone = 9 * module_width
start_guard_end = quiet_zone + 3 * module_width
left_start = start_guard_end
left_end = left_start + 42 * module_width
center_guard_end = left_end + 5 * module_width
right_start = center_guard_end
right_end = right_start + 42 * module_width

# Text labels for digits
text_y = bar_y_min - 15
digit_labels = []

# First digit (outside left guard)
digit_labels.append({"x": quiet_zone - 5 * module_width, "y": text_y, "label": full_code[0]})

# Left side digits (2-7)
left_digit_width = 7 * module_width
for i, digit in enumerate(full_code[1:7]):
    x = left_start + (i + 0.5) * left_digit_width
    digit_labels.append({"x": x, "y": text_y, "label": digit})

# Right side digits (8-13)
for i, digit in enumerate(full_code[7:13]):
    x = right_start + (i + 0.5) * left_digit_width
    digit_labels.append({"x": x, "y": text_y, "label": digit})

df_digits = pd.DataFrame(digit_labels)

# Title label
df_title = pd.DataFrame(
    {"x": [total_width / 2], "y": [guard_y_max + 25], "label": ["barcode-ean13 · letsplot · pyplots.ai"]}
)

# Create plot
plot = (
    ggplot()
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"), data=df_bars)
    + scale_fill_identity()
    + geom_text(aes(x="x", y="y", label="label"), data=df_digits, size=16, family="monospace")
    + geom_text(aes(x="x", y="y", label="label"), data=df_title, size=14)
    + xlim(0, total_width)
    + ylim(0, guard_y_max + 45)
    + theme_void()
    + theme(plot_background=element_blank(), panel_background=element_blank())
    + ggsize(1600, 900)
)

# Save outputs
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")
