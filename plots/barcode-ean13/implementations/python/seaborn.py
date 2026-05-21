"""anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# EAN-13 encoding tables
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

# Data
code = "4006381333931"

if len(code) == 12:
    odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
    even_sum = sum(int(code[i]) for i in range(1, 12, 2))
    check = (10 - (odd_sum + even_sum * 3) % 10) % 10
    code = code + str(check)

# Build binary barcode pattern
first_digit = code[0]
barcode_binary = "101"  # start guard
pattern = FIRST_DIGIT_PATTERNS[first_digit]
for i, digit in enumerate(code[1:7]):
    barcode_binary += L_CODES[digit] if pattern[i] == "L" else G_CODES[digit]
barcode_binary += "01010"  # center guard
for digit in code[7:13]:
    barcode_binary += R_CODES[digit]
barcode_binary += "101"  # end guard

quiet_zone = "0" * 9
barcode_with_quiet = quiet_zone + barcode_binary + quiet_zone
barcode_array = np.array([[int(b) for b in barcode_with_quiet]])
barcode_data = np.repeat(barcode_array, 60, axis=0)

# Set seaborn theme
sns.set_theme(style="white", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

# Plot — canonical 3200×1800 px
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

cmap = sns.color_palette([PAGE_BG, INK], as_cmap=True)
sns.heatmap(
    barcode_data, cmap=cmap, cbar=False, xticklabels=False, yticklabels=False, linewidths=0, linecolor="none", ax=ax
)

for spine in ax.spines.values():
    spine.set_visible(False)

# EAN-13 standard digit positioning:
#   code[0]  → left quiet zone (outside/left of start guard at col 9)
#   code[1:7] → centered below left data section (cols 12–53)
#   code[7:]  → centered below right data section (cols 59–100)
digit_y = barcode_data.shape[0] + 7
text_kw = {"fontsize": 10, "fontfamily": "monospace", "fontweight": "bold", "va": "top", "color": INK}

ax.text(4.5, digit_y, code[0], ha="center", **text_kw)
ax.text(33.0, digit_y, code[1:7], ha="center", **text_kw)
ax.text(80.0, digit_y, code[7:], ha="center", **text_kw)

ax.set_xlim(-5, len(barcode_with_quiet) + 5)
ax.set_ylim(barcode_data.shape[0] + 18, -5)

ax.set_title("barcode-ean13 · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
