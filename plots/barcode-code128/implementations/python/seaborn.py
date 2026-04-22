""" pyplots.ai
barcode-code128: Code 128 Barcode
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-19
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Code 128 encoding tables
CODE128_B_PATTERNS = {
    " ": "11011001100",
    "!": "11001101100",
    '"': "11001100110",
    "#": "10010011000",
    "$": "10010001100",
    "%": "10001001100",
    "&": "10011001000",
    "'": "10011000100",
    "(": "10001100100",
    ")": "11001001000",
    "*": "11001000100",
    "+": "11000100100",
    ",": "10110011100",
    "-": "10011011100",
    ".": "10011001110",
    "/": "10111001100",
    "0": "10011101100",
    "1": "10011100110",
    "2": "11001110010",
    "3": "11001011100",
    "4": "11001001110",
    "5": "11011100100",
    "6": "11001110100",
    "7": "11101101110",
    "8": "11101001100",
    "9": "11100101100",
    ":": "11100100110",
    ";": "11101100100",
    "<": "11100110100",
    "=": "11100110010",
    ">": "11011011000",
    "?": "11011000110",
    "@": "11000110110",
    "A": "10100011000",
    "B": "10001011000",
    "C": "10001000110",
    "D": "10110001000",
    "E": "10001101000",
    "F": "10001100010",
    "G": "11010001000",
    "H": "11000101000",
    "I": "11000100010",
    "J": "10110111000",
    "K": "10110001110",
    "L": "10001101110",
    "M": "10111011000",
    "N": "10111000110",
    "O": "10001110110",
    "P": "11101110110",
    "Q": "11010001110",
    "R": "11000101110",
    "S": "11011101000",
    "T": "11011100010",
    "U": "11011101110",
    "V": "11101011000",
    "W": "11101000110",
    "X": "11100010110",
    "Y": "11101101000",
    "Z": "11101100010",
    "[": "11100011010",
    "\\": "11101111010",
    "]": "11001000010",
    "^": "11110001010",
    "_": "10100110000",
    "`": "10100001100",
    "a": "10010110000",
    "b": "10010000110",
    "c": "10000101100",
    "d": "10000100110",
    "e": "10110010000",
    "f": "10110000100",
    "g": "10011010000",
    "h": "10011000010",
    "i": "10000110100",
    "j": "10000110010",
    "k": "11000010010",
    "l": "11001010000",
    "m": "11110111010",
    "n": "11000010100",
    "o": "10001111010",
    "p": "10100111100",
    "q": "10010111100",
    "r": "10010011110",
    "s": "10111100100",
    "t": "10011110100",
    "u": "10011110010",
    "v": "11110100100",
    "w": "11110010100",
    "x": "11110010010",
    "y": "11011011110",
    "z": "11011110110",
    "{": "11110110110",
    "|": "10101111000",
    "}": "10100011110",
    "~": "10001011110",
}

CODE128_VALUES = {
    " ": 0,
    "!": 1,
    '"': 2,
    "#": 3,
    "$": 4,
    "%": 5,
    "&": 6,
    "'": 7,
    "(": 8,
    ")": 9,
    "*": 10,
    "+": 11,
    ",": 12,
    "-": 13,
    ".": 14,
    "/": 15,
    "0": 16,
    "1": 17,
    "2": 18,
    "3": 19,
    "4": 20,
    "5": 21,
    "6": 22,
    "7": 23,
    "8": 24,
    "9": 25,
    ":": 26,
    ";": 27,
    "<": 28,
    "=": 29,
    ">": 30,
    "?": 31,
    "@": 32,
    "A": 33,
    "B": 34,
    "C": 35,
    "D": 36,
    "E": 37,
    "F": 38,
    "G": 39,
    "H": 40,
    "I": 41,
    "J": 42,
    "K": 43,
    "L": 44,
    "M": 45,
    "N": 46,
    "O": 47,
    "P": 48,
    "Q": 49,
    "R": 50,
    "S": 51,
    "T": 52,
    "U": 53,
    "V": 54,
    "W": 55,
    "X": 56,
    "Y": 57,
    "Z": 58,
    "[": 59,
    "\\": 60,
    "]": 61,
    "^": 62,
    "_": 63,
    "`": 64,
    "a": 65,
    "b": 66,
    "c": 67,
    "d": 68,
    "e": 69,
    "f": 70,
    "g": 71,
    "h": 72,
    "i": 73,
    "j": 74,
    "k": 75,
    "l": 76,
    "m": 77,
    "n": 78,
    "o": 79,
    "p": 80,
    "q": 81,
    "r": 82,
    "s": 83,
    "t": 84,
    "u": 85,
    "v": 86,
    "w": 87,
    "x": 88,
    "y": 89,
    "z": 90,
    "{": 91,
    "|": 92,
    "}": 93,
    "~": 94,
}

# Check digit patterns (values 95-105)
CHECK_PATTERNS = [
    "11110101000",
    "11110100010",
    "10111011110",
    "10111101110",
    "10111110110",
    "11101011110",
    "11110101110",
    "11010000100",
    "11010010000",
    "11010011100",
    "11000111010",
]

START_B = "11010010000"  # Start Code B (value 104)
STOP = "1100011101011"  # Stop pattern

# Data
content = "SHIP-2024-ABC123"

# Encode content using Code 128 subset B
barcode_binary = START_B
checksum = 104  # Start B value
for i, char in enumerate(content):
    barcode_binary += CODE128_B_PATTERNS[char]
    checksum += CODE128_VALUES[char] * (i + 1)

# Add check digit
check_value = checksum % 103
if check_value < 95:
    for char, val in CODE128_VALUES.items():
        if val == check_value:
            barcode_binary += CODE128_B_PATTERNS[char]
            break
else:
    barcode_binary += CHECK_PATTERNS[check_value - 95]

barcode_binary += STOP

# Add quiet zones (10 modules of white space on each side)
quiet_zone = "0" * 10
barcode_with_quiet = quiet_zone + barcode_binary + quiet_zone

# Convert binary string to numpy array for seaborn heatmap
# Create a 2D array where each row is the same barcode pattern
barcode_array = np.array([[int(bit) for bit in barcode_with_quiet]])
# Repeat rows to create proper bar height (aspect ratio for barcode)
barcode_data = np.repeat(barcode_array, 60, axis=0)

# Set seaborn style
sns.set_theme(style="white")

# Create figure with proper aspect ratio
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn heatmap to render the barcode
# Binary colormap: white (0) and blue (1)
cmap = sns.color_palette(["white", "#306998"], as_cmap=True)
sns.heatmap(
    barcode_data, cmap=cmap, cbar=False, xticklabels=False, yticklabels=False, linewidths=0, linecolor="none", ax=ax
)

# Remove axis spines for clean look
for spine in ax.spines.values():
    spine.set_visible(False)

# Add human-readable text below barcode
ax.text(
    len(barcode_with_quiet) / 2,
    barcode_data.shape[0] + 12,
    content,
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
    "barcode-code128 · seaborn · pyplots.ai",
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
