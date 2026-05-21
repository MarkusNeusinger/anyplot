""" anyplot.ai
barcode-code128: Code 128 Barcode
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-21
"""

import os
import sys


sys.path = sys.path[1:]  # prevent this file from shadowing the installed matplotlib package

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Code 128B encoding: each character → 6 bar/space widths (alternating)
CODE128_B = {
    " ": [2, 1, 2, 2, 2, 2],
    "!": [2, 2, 2, 1, 2, 2],
    '"': [2, 2, 2, 2, 2, 1],
    "#": [1, 2, 1, 2, 2, 3],
    "$": [1, 2, 1, 3, 2, 2],
    "%": [1, 3, 1, 2, 2, 2],
    "&": [1, 2, 2, 2, 1, 3],
    "'": [1, 2, 2, 3, 1, 2],
    "(": [1, 3, 2, 2, 1, 2],
    ")": [2, 2, 1, 2, 1, 3],
    "*": [2, 2, 1, 3, 1, 2],
    "+": [2, 3, 1, 2, 1, 2],
    ",": [1, 1, 2, 2, 3, 2],
    "-": [1, 2, 2, 1, 3, 2],
    ".": [1, 2, 2, 2, 3, 1],
    "/": [1, 1, 3, 2, 2, 2],
    "0": [1, 2, 3, 1, 2, 2],
    "1": [1, 2, 3, 2, 2, 1],
    "2": [2, 2, 3, 2, 1, 1],
    "3": [2, 2, 1, 1, 3, 2],
    "4": [2, 2, 1, 2, 3, 1],
    "5": [2, 1, 3, 2, 1, 2],
    "6": [2, 2, 3, 1, 1, 2],
    "7": [3, 1, 2, 1, 3, 1],
    "8": [3, 1, 1, 2, 2, 2],
    "9": [3, 2, 1, 1, 2, 2],
    ":": [3, 2, 1, 2, 2, 1],
    ";": [3, 1, 2, 2, 1, 2],
    "<": [3, 2, 2, 1, 1, 2],
    "=": [3, 2, 2, 2, 1, 1],
    ">": [2, 1, 2, 1, 2, 3],
    "?": [2, 1, 2, 3, 2, 1],
    "@": [2, 3, 2, 1, 2, 1],
    "A": [1, 1, 1, 3, 2, 3],
    "B": [1, 3, 1, 1, 2, 3],
    "C": [1, 3, 1, 3, 2, 1],
    "D": [1, 1, 2, 3, 1, 3],
    "E": [1, 3, 2, 1, 1, 3],
    "F": [1, 3, 2, 3, 1, 1],
    "G": [2, 1, 1, 3, 1, 3],
    "H": [2, 3, 1, 1, 1, 3],
    "I": [2, 3, 1, 3, 1, 1],
    "J": [1, 1, 2, 1, 3, 3],
    "K": [1, 1, 2, 3, 3, 1],
    "L": [1, 3, 2, 1, 3, 1],
    "M": [1, 1, 3, 1, 2, 3],
    "N": [1, 1, 3, 3, 2, 1],
    "O": [1, 3, 3, 1, 2, 1],
    "P": [3, 1, 3, 1, 2, 1],
    "Q": [2, 1, 1, 3, 3, 1],
    "R": [2, 3, 1, 1, 3, 1],
    "S": [2, 1, 3, 1, 1, 3],
    "T": [2, 1, 3, 3, 1, 1],
    "U": [2, 1, 3, 1, 3, 1],
    "V": [3, 1, 1, 1, 2, 3],
    "W": [3, 1, 1, 3, 2, 1],
    "X": [3, 3, 1, 1, 2, 1],
    "Y": [3, 1, 2, 1, 1, 3],
    "Z": [3, 1, 2, 3, 1, 1],
    "[": [3, 3, 2, 1, 1, 1],
    "\\": [3, 1, 4, 1, 1, 1],
    "]": [2, 2, 1, 4, 1, 1],
    "^": [4, 3, 1, 1, 1, 1],
    "_": [1, 1, 1, 2, 2, 4],
    "`": [1, 1, 1, 4, 2, 2],
    "a": [1, 2, 1, 1, 2, 4],
    "b": [1, 2, 1, 4, 2, 1],
    "c": [1, 4, 1, 1, 2, 2],
    "d": [1, 4, 1, 2, 2, 1],
    "e": [1, 1, 2, 2, 1, 4],
    "f": [1, 1, 2, 4, 1, 2],
    "g": [1, 2, 2, 1, 1, 4],
    "h": [1, 2, 2, 4, 1, 1],
    "i": [1, 4, 2, 1, 1, 2],
    "j": [1, 4, 2, 2, 1, 1],
    "k": [2, 4, 1, 2, 1, 1],
    "l": [2, 2, 1, 1, 1, 4],
    "m": [4, 1, 3, 1, 1, 1],
    "n": [2, 4, 1, 1, 1, 2],
    "o": [1, 3, 4, 1, 1, 1],
    "p": [1, 1, 1, 2, 4, 2],
    "q": [1, 2, 1, 1, 4, 2],
    "r": [1, 2, 1, 2, 4, 1],
    "s": [1, 1, 4, 2, 1, 2],
    "t": [1, 2, 4, 1, 1, 2],
    "u": [1, 2, 4, 2, 1, 1],
    "v": [4, 1, 1, 2, 1, 2],
    "w": [4, 2, 1, 1, 1, 2],
    "x": [4, 2, 1, 2, 1, 1],
    "y": [2, 1, 2, 1, 4, 1],
    "z": [2, 1, 4, 1, 2, 1],
    "{": [4, 1, 2, 1, 2, 1],
    "|": [1, 1, 1, 1, 4, 3],
    "}": [1, 1, 1, 3, 4, 1],
    "~": [1, 3, 1, 1, 4, 1],
}

CODE128_B_VALUES = {
    char: i
    for i, char in enumerate(
        " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
    )
}

START_B = [2, 1, 1, 4, 1, 2]
START_B_VALUE = 104
STOP = [2, 3, 3, 1, 1, 1, 2]

# Checksum symbol patterns (indices 0–102 for modulo-103 calculation)
CHECKSUM_PATTERNS = [
    [2, 1, 2, 2, 2, 2],
    [2, 2, 2, 1, 2, 2],
    [2, 2, 2, 2, 2, 1],
    [1, 2, 1, 2, 2, 3],
    [1, 2, 1, 3, 2, 2],
    [1, 3, 1, 2, 2, 2],
    [1, 2, 2, 2, 1, 3],
    [1, 2, 2, 3, 1, 2],
    [1, 3, 2, 2, 1, 2],
    [2, 2, 1, 2, 1, 3],
    [2, 2, 1, 3, 1, 2],
    [2, 3, 1, 2, 1, 2],
    [1, 1, 2, 2, 3, 2],
    [1, 2, 2, 1, 3, 2],
    [1, 2, 2, 2, 3, 1],
    [1, 1, 3, 2, 2, 2],
    [1, 2, 3, 1, 2, 2],
    [1, 2, 3, 2, 2, 1],
    [2, 2, 3, 2, 1, 1],
    [2, 2, 1, 1, 3, 2],
    [2, 2, 1, 2, 3, 1],
    [2, 1, 3, 2, 1, 2],
    [2, 2, 3, 1, 1, 2],
    [3, 1, 2, 1, 3, 1],
    [3, 1, 1, 2, 2, 2],
    [3, 2, 1, 1, 2, 2],
    [3, 2, 1, 2, 2, 1],
    [3, 1, 2, 2, 1, 2],
    [3, 2, 2, 1, 1, 2],
    [3, 2, 2, 2, 1, 1],
    [2, 1, 2, 1, 2, 3],
    [2, 1, 2, 3, 2, 1],
    [2, 3, 2, 1, 2, 1],
    [1, 1, 1, 3, 2, 3],
    [1, 3, 1, 1, 2, 3],
    [1, 3, 1, 3, 2, 1],
    [1, 1, 2, 3, 1, 3],
    [1, 3, 2, 1, 1, 3],
    [1, 3, 2, 3, 1, 1],
    [2, 1, 1, 3, 1, 3],
    [2, 3, 1, 1, 1, 3],
    [2, 3, 1, 3, 1, 1],
    [1, 1, 2, 1, 3, 3],
    [1, 1, 2, 3, 3, 1],
    [1, 3, 2, 1, 3, 1],
    [1, 1, 3, 1, 2, 3],
    [1, 1, 3, 3, 2, 1],
    [1, 3, 3, 1, 2, 1],
    [3, 1, 3, 1, 2, 1],
    [2, 1, 1, 3, 3, 1],
    [2, 3, 1, 1, 3, 1],
    [2, 1, 3, 1, 1, 3],
    [2, 1, 3, 3, 1, 1],
    [2, 1, 3, 1, 3, 1],
    [3, 1, 1, 1, 2, 3],
    [3, 1, 1, 3, 2, 1],
    [3, 3, 1, 1, 2, 1],
    [3, 1, 2, 1, 1, 3],
    [3, 1, 2, 3, 1, 1],
    [3, 3, 2, 1, 1, 1],
    [3, 1, 4, 1, 1, 1],
    [2, 2, 1, 4, 1, 1],
    [4, 3, 1, 1, 1, 1],
    [1, 1, 1, 2, 2, 4],
    [1, 1, 1, 4, 2, 2],
    [1, 2, 1, 1, 2, 4],
    [1, 2, 1, 4, 2, 1],
    [1, 4, 1, 1, 2, 2],
    [1, 4, 1, 2, 2, 1],
    [1, 1, 2, 2, 1, 4],
    [1, 1, 2, 4, 1, 2],
    [1, 2, 2, 1, 1, 4],
    [1, 2, 2, 4, 1, 1],
    [1, 4, 2, 1, 1, 2],
    [1, 4, 2, 2, 1, 1],
    [2, 4, 1, 2, 1, 1],
    [2, 2, 1, 1, 1, 4],
    [4, 1, 3, 1, 1, 1],
    [2, 4, 1, 1, 1, 2],
    [1, 3, 4, 1, 1, 1],
    [1, 1, 1, 2, 4, 2],
    [1, 2, 1, 1, 4, 2],
    [1, 2, 1, 2, 4, 1],
    [1, 1, 4, 2, 1, 2],
    [1, 2, 4, 1, 1, 2],
    [1, 2, 4, 2, 1, 1],
    [4, 1, 1, 2, 1, 2],
    [4, 2, 1, 1, 1, 2],
    [4, 2, 1, 2, 1, 1],
    [2, 1, 2, 1, 4, 1],
    [2, 1, 4, 1, 2, 1],
    [4, 1, 2, 1, 2, 1],
    [1, 1, 1, 1, 4, 3],
    [1, 1, 1, 3, 4, 1],
    [1, 3, 1, 1, 4, 1],
    [1, 1, 4, 1, 1, 3],
    [1, 1, 4, 3, 1, 1],
    [4, 1, 1, 1, 1, 3],
    [4, 1, 1, 3, 1, 1],
    [1, 1, 3, 1, 4, 1],
    [1, 1, 4, 1, 3, 1],
    [3, 1, 1, 1, 4, 1],
    [4, 1, 1, 1, 3, 1],
    [2, 1, 1, 4, 1, 2],
    [2, 1, 1, 2, 1, 4],
    [2, 1, 1, 2, 3, 2],
]

# Data
content = "SHIP-2024-ABC123"

# Encode: start + data + checksum + stop
bars = list(START_B)
checksum = START_B_VALUE
for i, char in enumerate(content):
    pattern = CODE128_B.get(char, CODE128_B[" "])
    bars.extend(pattern)
    checksum += CODE128_B_VALUES.get(char, 0) * (i + 1)

bars.extend(CHECKSUM_PATTERNS[checksum % 103])
bars.extend(STOP)

# Convert bar widths to binary (1=bar, 0=space)
binary_pattern = []
is_bar = True
for width in bars:
    binary_pattern.extend([1 if is_bar else 0] * width)
    is_bar = not is_bar

# Layout
barcode_height = 200
quiet_zone = 30
full_pattern = [0] * quiet_zone + binary_pattern + [0] * quiet_zone
barcode_width = len(full_pattern)
barcode_array = np.array([full_pattern] * barcode_height)

# Plot — landscape canvas: figsize=(8, 4.5) × dpi=400 → 3200×1800 px
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Theme-adaptive colormap: 0 (space) → PAGE_BG, 1 (bar) → INK
bar_cmap = LinearSegmentedColormap.from_list("barcode_cmap", [PAGE_BG, INK], N=2)
ax.imshow(barcode_array, cmap=bar_cmap, aspect="auto", interpolation="nearest", vmin=0, vmax=1)

ax.set_xticks([])
ax.set_yticks([])

# Human-readable text below barcode
ax.text(
    barcode_width / 2,
    barcode_height + 28,
    content,
    fontsize=16,
    ha="center",
    va="top",
    fontfamily="monospace",
    fontweight="bold",
    color=INK,
)

ax.set_xlim(-10, barcode_width + 10)
ax.set_ylim(barcode_height + 75, -35)

for spine in ax.spines.values():
    spine.set_visible(False)

# Style
ax.set_title("barcode-code128 · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)
ax.tick_params(colors=INK_SOFT)

fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.04)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
