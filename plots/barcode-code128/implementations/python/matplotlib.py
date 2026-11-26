"""anyplot.ai
barcode-code128: Code 128 Barcode
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-26
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# The symbol itself is black on white in both themes (scanners reject inverted codes):
# the dark theme gets a light tile behind the bars.
BAR_COLOR = "#1A1A17"
TILE_COLOR = "#FAF8F1"

# Code 128 symbol patterns by symbol value 0-105: six alternating bar/space widths each.
# Code set B maps ASCII 32-126 to values 0-94; 104 is Start B.
SYMBOL_PATTERNS = [
    [int(w) for w in p]
    for p in " ".join(
        (
            "212222 222122 222221 121223 121322 131222 122213 122312 132212 221213 ",
            "221312 231212 112232 122132 122231 113222 123122 123221 223211 221132 ",
            "221231 213212 223112 312131 311222 321122 321221 312212 322112 322211 ",
            "212123 212321 232121 111323 131123 131321 112313 132113 132311 211313 ",
            "231113 231311 112133 112331 132131 113123 113321 133121 313121 211331 ",
            "231131 213113 213311 213131 311123 311321 331121 312113 312311 332111 ",
            "314111 221411 431111 111224 111422 121124 121421 141122 141221 112214 ",
            "112412 122114 122411 142112 142211 241211 221114 413111 241112 134111 ",
            "111242 121142 121241 114212 124112 124211 411212 421112 421211 212141 ",
            "214121 412121 111143 111341 131141 114113 114311 411113 411311 113141 ",
            "114131 311141 411131 211412 211214 211232",
        )
    ).split()
]
START_B_VALUE = 104
STOP = [2, 3, 3, 1, 1, 1, 2]

# Data
content = "SHIP-2024-ABC123"

# Encode: start + data + checksum + stop
values = [ord(char) - 32 for char in content]  # Code B value of each character
checksum = (START_B_VALUE + sum(v * (i + 1) for i, v in enumerate(values))) % 103

bars = list(SYMBOL_PATTERNS[START_B_VALUE])
for v in values:
    bars.extend(SYMBOL_PATTERNS[v])
bars.extend(SYMBOL_PATTERNS[checksum])
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

# Zone boundaries for structural annotations
# Code 128 standard: every symbol (except STOP) = 11 modules; STOP = 13 modules
_sw = 11
_stop_w = sum(STOP)  # 13
_qz0_end = quiet_zone
_start_end = _qz0_end + _sw
_data_end = _start_end + len(content) * _sw
_check_end = _data_end + _sw
_stop_end = _check_end + _stop_w

zones = [
    (_qz0_end - quiet_zone, _qz0_end, "Quiet Zone"),
    (_qz0_end, _start_end, "Start"),
    (_start_end, _data_end, f"Data · Code B ({len(content)} chars)"),
    (_data_end, _check_end, "Check"),
    (_check_end, _stop_end, "Stop"),
    (_stop_end, barcode_width, "Quiet Zone"),
]

# Plot — landscape canvas: figsize=(8, 4.5) × dpi=400 → 3200×1800 px
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Binary colormap: 0 (space, quiet zone) → tile, 1 (bar) → black, identical in both themes
bar_cmap = LinearSegmentedColormap.from_list("barcode_cmap", [TILE_COLOR, BAR_COLOR], N=2)
ax.imshow(barcode_array, cmap=bar_cmap, aspect="auto", interpolation="nearest", vmin=0, vmax=1)

ax.set_xticks([])
ax.set_yticks([])

# Structural zone annotations above the barcode
y_tick_top = 0  # tick mark at barcode top edge
y_bracket = -9  # horizontal bracket line
y_labels = (-20, -34)  # two label rows; neighbouring zones alternate so narrow labels never collide

for k, (x0, x1, label) in enumerate(zones):
    cx = (x0 + x1) / 2
    y_label = y_labels[k % 2]
    ax.plot([x0, x1], [y_bracket, y_bracket], color=INK_MUTED, lw=0.6, solid_capstyle="butt")
    ax.plot([x0, x0], [y_tick_top, y_bracket], color=INK_MUTED, lw=0.6)
    ax.plot([x1, x1], [y_tick_top, y_bracket], color=INK_MUTED, lw=0.6)
    if k % 2:
        ax.plot([cx, cx], [y_bracket, y_label + 5], color=INK_MUTED, lw=0.6)
    ax.text(cx, y_label, label, fontsize=8, ha="center", va="center", color=INK_MUTED, fontfamily="monospace")

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
ax.set_ylim(barcode_height + 52, -46)

for spine in ax.spines.values():
    spine.set_visible(False)

# Style
ax.set_title("barcode-code128 · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=8)

fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.04)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
