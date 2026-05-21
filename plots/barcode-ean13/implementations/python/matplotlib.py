""" anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-21
"""

import os
import sys


sys.path = sys.path[1:]  # prevent this file from shadowing the installed matplotlib package

import matplotlib.patches as patches
import matplotlib.pyplot as plt


# Theme
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

# Data — 12-digit input; check digit auto-calculated
input_code = "400638133393"
total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(input_code))
check_digit = str((10 - (total % 10)) % 10)
full_code = input_code + check_digit  # → "4006381333931"
ean_formatted = f"{full_code[0]} {full_code[1:7]} {full_code[7:]}"  # "4 006381 333931"

# Encode EAN-13 bit pattern
lg_pattern = FIRST_DIGIT_PATTERN[full_code[0]]
barcode_pattern = "101"  # start guard
for i, digit in enumerate(full_code[1:7]):
    barcode_pattern += L_CODES[digit] if lg_pattern[i] == "L" else G_CODES[digit]
barcode_pattern += "01010"  # center guard
for digit in full_code[7:13]:
    barcode_pattern += R_CODES[digit]
barcode_pattern += "101"  # end guard

# Guard bar bit indices: start (0–2), center (45–49), end (92–94)
guard_positions = set(range(3)) | set(range(45, 50)) | set(range(92, 95))

# Layout (data units — 1 unit = 1 module width)
quiet_zone = 9
start_x = quiet_zone
start_y = 7.0
bar_height = 14.0
guard_height = 17.0
total_modules = len(barcode_pattern)  # 95

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw barcode bars
for i, bit in enumerate(barcode_pattern):
    if bit == "1":
        is_guard = i in guard_positions
        h = guard_height if is_guard else bar_height
        y0 = start_y if is_guard else start_y + (guard_height - bar_height)
        ax.add_patch(patches.Rectangle((start_x + i, y0), 1, h, linewidth=0, edgecolor="none", facecolor=INK))

# Style — human-readable digits below bars
digit_y = start_y - 0.5
digit_fs = 10

# First digit — sits outside the left quiet zone
ax.text(
    start_x - 3.5,
    digit_y,
    full_code[0],
    fontsize=digit_fs,
    ha="center",
    va="top",
    fontfamily="monospace",
    fontweight="bold",
    color=INK,
)

# Left-side digits (positions 1–6); each digit spans 7 modules, after 3-bit start guard
for i, digit in enumerate(full_code[1:7]):
    dx = start_x + 3 + (i + 0.5) * 7
    ax.text(
        dx,
        digit_y,
        digit,
        fontsize=digit_fs,
        ha="center",
        va="top",
        fontfamily="monospace",
        fontweight="bold",
        color=INK,
    )

# Right-side digits (positions 7–12); start after start(3)+left(42)+center(5)=50 modules
for i, digit in enumerate(full_code[7:13]):
    dx = start_x + 50 + (i + 0.5) * 7
    ax.text(
        dx,
        digit_y,
        digit,
        fontsize=digit_fs,
        ha="center",
        va="top",
        fontfamily="monospace",
        fontweight="bold",
        color=INK,
    )

# Section labels — barcode anatomy guide below digit row
# Country (1–3): first digit at x=5.5, digits 2–3 at x=15.5, 22.5 → center=14.0
# Manufacturer (4–8): left digits 4–7 at x=29.5..50.5, right digit 8 at x=62.5 → center=46.0
# Product (9–12): right digits 9–12 at x=69.5..90.5 → center=80.0
# Check (13): right digit 13 at x=97.5
sections = [("Country (1–3)", 14.0), ("Manufacturer (4–8)", 46.0), ("Product (9–12)", 80.0), ("Check (13)", 97.5)]
for label, cx in sections:
    ax.text(cx, digit_y - 2.0, label, fontsize=7, ha="center", va="top", color=INK_SOFT)

# Axis bounds and clean presentation
x_max = start_x + total_modules + quiet_zone  # 9 + 95 + 9 = 113
y_max = start_y + guard_height + 5.0
ax.set_xlim(0, x_max)
ax.set_ylim(3.5, y_max)
ax.axis("off")

# Title
ax.text(
    start_x + total_modules / 2,
    start_y + guard_height + 2.0,
    "barcode-ean13 · python · matplotlib · anyplot.ai",
    fontsize=12,
    ha="center",
    va="bottom",
    fontweight="medium",
    color=INK,
)

# EAN-13 grouping format caption
ax.text(
    start_x + total_modules / 2,
    start_y + guard_height + 0.5,
    ean_formatted,
    fontsize=9,
    ha="center",
    va="bottom",
    fontfamily="monospace",
    color=INK_SOFT,
)

# Save
fig.subplots_adjust(left=0.03, right=0.97, top=0.97, bottom=0.03)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
