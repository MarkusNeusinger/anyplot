""" pyplots.ai
barcode-ean13: EAN-13 Barcode
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-19
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


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

# First digit encoding pattern (L = L-code, G = G-code)
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

# Guard patterns
START_GUARD = "101"
CENTER_GUARD = "01010"
END_GUARD = "101"

# Data - Example EAN-13 code (German product)
code = "4006381333931"

# Calculate check digit if only 12 digits provided
if len(code) == 12:
    odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
    even_sum = sum(int(code[i]) for i in range(1, 12, 2))
    check = (10 - (odd_sum + even_sum * 3) % 10) % 10
    code = code + str(check)

# Encode the barcode
first_digit = code[0]
left_digits = code[1:7]
right_digits = code[7:13]

# Build binary pattern
barcode_binary = START_GUARD

# Encode left side using L/G pattern determined by first digit
pattern = FIRST_DIGIT_PATTERNS[first_digit]
for i, digit in enumerate(left_digits):
    if pattern[i] == "L":
        barcode_binary += L_CODES[digit]
    else:
        barcode_binary += G_CODES[digit]

barcode_binary += CENTER_GUARD

# Encode right side using R-codes
for digit in right_digits:
    barcode_binary += R_CODES[digit]

barcode_binary += END_GUARD

# Add quiet zones (9 modules on each side as per spec)
quiet_zone = "0" * 9
barcode_with_quiet = quiet_zone + barcode_binary + quiet_zone

# Convert binary string to numpy array for seaborn heatmap
barcode_array = np.array([[int(bit) for bit in barcode_with_quiet]])
# Repeat rows to create proper bar height
barcode_data = np.repeat(barcode_array, 60, axis=0)

# Set seaborn style
sns.set_theme(style="white")

# Create figure with proper aspect ratio
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn heatmap to render the barcode
# Binary colormap: white (0) and Python blue (1)
cmap = sns.color_palette(["white", "#306998"], as_cmap=True)
sns.heatmap(
    barcode_data, cmap=cmap, cbar=False, xticklabels=False, yticklabels=False, linewidths=0, linecolor="none", ax=ax
)

# Remove axis spines for clean look
for spine in ax.spines.values():
    spine.set_visible(False)

# Format human-readable text with spaces for EAN-13 standard display
# First digit, then 6 digits, then 6 digits
display_text = f"{code[0]}  {code[1:7]}  {code[7:13]}"

# Add human-readable text below barcode
ax.text(
    len(barcode_with_quiet) / 2,
    barcode_data.shape[0] + 12,
    display_text,
    fontsize=32,
    fontfamily="monospace",
    fontweight="bold",
    ha="center",
    va="top",
    color="#306998",
)

# Add title above the barcode
ax.text(
    len(barcode_with_quiet) / 2,
    -8,
    "barcode-ean13 · seaborn · pyplots.ai",
    fontsize=28,
    fontweight="bold",
    ha="center",
    va="bottom",
    color="#333333",
)

# Adjust plot limits to show text and provide balanced margins
ax.set_xlim(-5, len(barcode_with_quiet) + 5)
ax.set_ylim(barcode_data.shape[0] + 25, -15)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
