"""anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Created: 2026-05-21
"""

import os
import sys


# Remove this file's directory from sys.path so 'import pygal' finds the
# installed library, not this file (pygal.py) itself.
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p not in ("", ".") and not (p and os.path.abspath(p) == _this_dir)]

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
# Barcode bars use ink tokens (not Okabe-Ito): monochrome is correct for EAN-13 semantics
BAR_COLOR = "#1A1A17" if THEME == "light" else "#F0EFE8"

# EAN-13 encoding tables
L_CODE = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"]
G_CODE = ["0100111", "0110011", "0011011", "0100001", "0011101", "0111001", "0000101", "0010001", "0001001", "0010111"]
R_CODE = ["1110010", "1100110", "1101100", "1000010", "1011100", "1001110", "1010000", "1000100", "1001000", "1110100"]

# Parity pattern: first digit selects which L/G codes to use for left 6 digits
PARITY = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]

# Data: German product barcode (pre-validated 13 digits with correct check digit)
product_code = "4006381333931"
digits = [int(c) for c in product_code]
parity_pattern = PARITY[digits[0]]

# Encode EAN-13 to binary bit string (95 modules total)
bits = "101"  # start guard
for i, d in enumerate(digits[1:7]):
    bits += L_CODE[d] if parity_pattern[i] == "L" else G_CODE[d]
bits += "01010"  # center guard
for d in digits[7:]:
    bits += R_CODE[d]
bits += "101"  # end guard

# Plot: one stacked column per module. The body series rises above the baseline for a dark module;
# the guard series hangs below it, so the three guard patterns reach down between the digit groups.
QUIET = 9  # quiet-zone modules on each side (spec minimum)
GUARD_MODULES = set(range(0, 3)) | set(range(45, 50)) | set(range(92, 95))
modules = [0] * QUIET + [int(b) for b in bits] + [0] * QUIET
body = [{"value": 6 if m else 0, "color": BAR_COLOR} for m in modules]
guard = [
    {"value": -0.9 if m and (i - QUIET) in GUARD_MODULES else 0, "color": BAR_COLOR} for i, m in enumerate(modules)
]

# Human-readable digits: the first one in the left quiet zone, the rest centered under their 7-module group
digit_labels = [""] * len(modules)
digit_labels[QUIET - 5] = str(digits[0])
for k, d in enumerate(digits[1:]):
    group_start = QUIET + 3 + 7 * k if k < 6 else QUIET + 3 + 5 + 7 * k
    digit_labels[group_start + 3] = str(d)

# Caption: the left-half parity pattern chosen by the first digit, and the right half's fixed code
x_label = f"Left half parity {parity_pattern} (set by first digit {digits[0]}) · right half R-code"
title = "barcode-ean13 · python · pygal · anyplot.ai"

# Chart style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BAR_COLOR, BAR_COLOR),
    title_font_size=66,
    label_font_size=84,
    major_label_font_size=84,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=0,
    opacity=1,
    opacity_hover=1,
    guide_stroke_color=PAGE_BG,
    major_guide_stroke_color=PAGE_BG,
)

# Chart — landscape 3200×1800 (hard contract)
chart = pygal.StackedBar(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=x_label,
    show_legend=False,
    show_x_labels=True,
    x_labels=digit_labels,
    x_label_rotation=0,
    show_minor_x_labels=True,
    range=(-1.0, 6.0),
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    margin=80,
    print_values=False,
)

chart.add("bars", body)
chart.add("guards", guard)

# Save PNG and interactive HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
