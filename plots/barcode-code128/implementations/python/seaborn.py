"""anyplot.ai
barcode-code128: Code 128 Barcode
Library: seaborn | Python 3.13
Quality: pending | Updated: 2026-05-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

sns.set_theme(
    style="white",
    rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "axes.edgecolor": INK_SOFT, "text.color": INK},
)

# Code 128 encoding tables (subset B — full printable ASCII)
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

# Patterns for check digit values 95–105 (no ASCII mapping)
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

START_B = "11010010000"
STOP = "1100011101011"

# Data
content = "SHIP-2024-ABC123"

# Encode using Code 128 subset B with modulo-103 check digit
barcode_binary = START_B
checksum = 104
for i, char in enumerate(content):
    barcode_binary += CODE128_B_PATTERNS[char]
    checksum += CODE128_VALUES[char] * (i + 1)

check_value = checksum % 103
if check_value < 95:
    for char, val in CODE128_VALUES.items():
        if val == check_value:
            barcode_binary += CODE128_B_PATTERNS[char]
            break
else:
    barcode_binary += CHECK_PATTERNS[check_value - 95]

barcode_binary += STOP

quiet_zone = "0" * 10
barcode_with_quiet = quiet_zone + barcode_binary + quiet_zone

# Build 2D array: repeat rows to give bars proper height
barcode_array = np.array([[int(bit) for bit in barcode_with_quiet]])
barcode_data = np.repeat(barcode_array, 40, axis=0)

# Plot
cmap = LinearSegmentedColormap.from_list("barcode", [PAGE_BG, INK])

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.heatmap(barcode_data, cmap=cmap, cbar=False, xticklabels=False, yticklabels=False, linewidths=0, ax=ax)

for spine in ax.spines.values():
    spine.set_visible(False)

# Style
ax.set_title("barcode-code128 · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=12)

fig.text(
    0.5, 0.07, content, ha="center", va="center", fontsize=10, fontfamily="monospace", fontweight="bold", color=INK
)

fig.subplots_adjust(top=0.88, bottom=0.16, left=0.02, right=0.98)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
