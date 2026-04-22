""" pyplots.ai
barcode-ean13: EAN-13 Barcode
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-19
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt


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

# First digit encoding pattern (determines L/G pattern for left side)
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


def calculate_check_digit(code_12):
    """Calculate EAN-13 check digit from first 12 digits."""
    total = 0
    for i, digit in enumerate(code_12):
        weight = 1 if i % 2 == 0 else 3
        total += int(digit) * weight
    return str((10 - (total % 10)) % 10)


def encode_ean13(code):
    """Encode a 12 or 13 digit code into EAN-13 barcode pattern."""
    if len(code) == 12:
        code = code + calculate_check_digit(code)
    elif len(code) != 13:
        raise ValueError("Code must be 12 or 13 digits")

    # Start guard: 101
    pattern = "101"

    # Left side (6 digits, encoded using L or G based on first digit)
    first_digit = code[0]
    lg_pattern = FIRST_DIGIT_PATTERN[first_digit]

    for i, digit in enumerate(code[1:7]):
        if lg_pattern[i] == "L":
            pattern += L_CODES[digit]
        else:
            pattern += G_CODES[digit]

    # Center guard: 01010
    pattern += "01010"

    # Right side (6 digits, all R-codes)
    for digit in code[7:13]:
        pattern += R_CODES[digit]

    # End guard: 101
    pattern += "101"

    return pattern, code


# Data - Example EAN-13 code (German product)
input_code = "4006381333931"
barcode_pattern, full_code = encode_ean13(input_code)

# Create figure with appropriate aspect ratio for barcode
fig, ax = plt.subplots(figsize=(16, 9))

# Barcode dimensions
module_width = 3  # Width of each module (bar unit)
bar_height = 180  # Height of regular bars
guard_height = 200  # Height of guard bars (slightly taller)
quiet_zone = module_width * 11  # Quiet zone width
start_x = quiet_zone
start_y = 100

# Draw the barcode
x = start_x
guard_positions = set()

# Mark guard bar positions (start: 0-2, center: 45-49, end: 92-94)
for i in range(3):
    guard_positions.add(i)
for i in range(45, 50):
    guard_positions.add(i)
for i in range(92, 95):
    guard_positions.add(i)

for i, bit in enumerate(barcode_pattern):
    if bit == "1":
        height = guard_height if i in guard_positions else bar_height
        y_offset = start_y if i in guard_positions else start_y + (guard_height - bar_height)
        rect = patches.Rectangle((x, y_offset), module_width, height, linewidth=0, edgecolor="none", facecolor="black")
        ax.add_patch(rect)
    x += module_width

# Calculate total barcode width
total_width = len(barcode_pattern) * module_width

# Draw human-readable digits
digit_y = start_y - 40
digit_fontsize = 28

# First digit (outside left guard)
ax.text(
    start_x - module_width * 4,
    digit_y,
    full_code[0],
    fontsize=digit_fontsize,
    ha="center",
    va="top",
    fontfamily="monospace",
    fontweight="bold",
)

# Left side digits (6 digits after first digit)
left_start = start_x + 3 * module_width  # After start guard
left_width = 6 * 7 * module_width  # 6 digits × 7 modules each
for i, digit in enumerate(full_code[1:7]):
    digit_x = left_start + (i + 0.5) * 7 * module_width
    ax.text(
        digit_x,
        digit_y,
        digit,
        fontsize=digit_fontsize,
        ha="center",
        va="top",
        fontfamily="monospace",
        fontweight="bold",
    )

# Right side digits (6 digits)
right_start = start_x + (3 + 42 + 5) * module_width  # After center guard
for i, digit in enumerate(full_code[7:13]):
    digit_x = right_start + (i + 0.5) * 7 * module_width
    ax.text(
        digit_x,
        digit_y,
        digit,
        fontsize=digit_fontsize,
        ha="center",
        va="top",
        fontfamily="monospace",
        fontweight="bold",
    )

# Set axis limits with quiet zones
ax.set_xlim(0, start_x + total_width + quiet_zone)
ax.set_ylim(0, start_y + guard_height + 80)

# Remove axes for clean barcode look
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.text(
    (start_x + total_width / 2),
    start_y + guard_height + 50,
    "barcode-ean13 · matplotlib · pyplots.ai",
    fontsize=24,
    ha="center",
    va="bottom",
    fontweight="bold",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
