"""anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-21
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

# Constants: EAN-13 encoding tables, guard patterns and module counts
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

# Constants (continued)
START_GUARD = "101"
CENTER_GUARD = "01010"
END_GUARD = "101"
QUIET_MODULES = 9  # minimum quiet zone on each side
BAR_ROWS = 60  # height of the data bars, in heatmap rows
GUARD_EXTRA_ROWS = 6  # how far the guard bars reach down between the digit groups

# Data: the number to encode, 12 digits (check digit added) or 13 digits
code = "4006381333931"

# Plot
if len(code) == 12:
    odd_sum = sum(int(d) for d in code[0::2])
    even_sum = sum(int(d) for d in code[1::2])
    code += str((10 - (odd_sum + even_sum * 3) % 10) % 10)

pattern = FIRST_DIGIT_PATTERNS[code[0]]
left = "".join((L_CODES if p == "L" else G_CODES)[d] for p, d in zip(pattern, code[1:7], strict=True))
right = "".join(R_CODES[d] for d in code[7:13])
modules = "0" * QUIET_MODULES + START_GUARD + left + CENTER_GUARD + right + END_GUARD + "0" * QUIET_MODULES
bars = np.array([int(m) for m in modules])

# Guard columns, derived from the symbol structure; they are drawn longer than the data bars
start = QUIET_MODULES
center = start + len(START_GUARD) + len(left)
end = center + len(CENTER_GUARD) + len(right)
is_guard = np.zeros(len(bars), dtype=bool)
for first, guard in ((start, START_GUARD), (center, CENTER_GUARD), (end, END_GUARD)):
    is_guard[first : first + len(guard)] = True

barcode_data = np.vstack([np.tile(bars, (BAR_ROWS, 1)), np.tile(bars * is_guard, (GUARD_EXTRA_ROWS, 1))])

sns.set_theme(style="white", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

cmap = sns.color_palette([PAGE_BG, INK], as_cmap=True)
sns.heatmap(barcode_data, cmap=cmap, cbar=False, xticklabels=False, yticklabels=False, linewidths=0, ax=ax)

for spine in ax.spines.values():
    spine.set_visible(False)

# Digits: first one left of the start guard, the rest centered under the two halves
digit_y = BAR_ROWS + 2
text_kw = {"fontsize": 18, "fontfamily": "monospace", "fontweight": "bold", "va": "top", "color": INK}
ax.text(start / 2, digit_y, code[0], ha="center", **text_kw)
ax.text((start + len(START_GUARD) + center) / 2, digit_y, code[1:7], ha="center", **text_kw)
ax.text((center + len(CENTER_GUARD) + end) / 2, digit_y, code[7:], ha="center", **text_kw)

ax.set_xlim(-3, len(bars) + 3)
ax.set_ylim(BAR_ROWS + 12, -3)

ax.set_title("barcode-ean13 · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
