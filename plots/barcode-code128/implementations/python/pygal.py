"""anyplot.ai
barcode-code128: Code 128 Barcode
Library: pygal 3.1.0 | Python 3.13.13
Quality: 78/100 | Updated: 2026-05-21
"""

import os

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6"  # barcode must stay on a light surface for scan reliability
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Code 128B character table: SP(0) through ~(94)
CODE128B_CHARS = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

# 107 Code 128 bar/space patterns (indices 0-106); STOP (106) has 7 elements
CODE128_PATTERNS = [
    (2, 1, 2, 2, 2, 2),
    (2, 2, 2, 1, 2, 2),
    (2, 2, 2, 2, 2, 1),
    (1, 2, 1, 2, 2, 3),
    (1, 2, 1, 3, 2, 2),
    (1, 3, 1, 2, 2, 2),
    (1, 2, 2, 2, 1, 3),
    (1, 2, 2, 3, 1, 2),
    (1, 3, 2, 2, 1, 2),
    (2, 2, 1, 2, 1, 3),
    (2, 2, 1, 3, 1, 2),
    (2, 3, 1, 2, 1, 2),
    (1, 1, 2, 2, 3, 2),
    (1, 2, 2, 1, 3, 2),
    (1, 2, 2, 2, 3, 1),
    (1, 1, 3, 2, 2, 2),
    (1, 2, 3, 1, 2, 2),
    (1, 2, 3, 2, 2, 1),
    (2, 2, 3, 2, 1, 1),
    (2, 2, 1, 1, 3, 2),
    (2, 2, 1, 2, 3, 1),
    (2, 1, 3, 2, 1, 2),
    (2, 2, 3, 1, 1, 2),
    (3, 1, 2, 1, 3, 1),
    (3, 1, 1, 2, 2, 2),
    (3, 2, 1, 1, 2, 2),
    (3, 2, 1, 2, 2, 1),
    (3, 1, 2, 2, 1, 2),
    (3, 2, 2, 1, 1, 2),
    (3, 2, 2, 2, 1, 1),
    (2, 1, 2, 1, 2, 3),
    (2, 1, 2, 3, 2, 1),
    (2, 3, 2, 1, 2, 1),
    (1, 1, 1, 3, 2, 3),
    (1, 3, 1, 1, 2, 3),
    (1, 3, 1, 3, 2, 1),
    (1, 1, 2, 3, 1, 3),
    (1, 3, 2, 1, 1, 3),
    (1, 3, 2, 3, 1, 1),
    (2, 1, 1, 3, 1, 3),
    (2, 3, 1, 1, 1, 3),
    (2, 3, 1, 3, 1, 1),
    (1, 1, 2, 1, 3, 3),
    (1, 1, 2, 3, 3, 1),
    (1, 3, 2, 1, 3, 1),
    (1, 1, 3, 1, 2, 3),
    (1, 1, 3, 3, 2, 1),
    (1, 3, 3, 1, 2, 1),
    (3, 1, 3, 1, 2, 1),
    (2, 1, 1, 3, 3, 1),
    (2, 3, 1, 1, 3, 1),
    (2, 1, 3, 1, 1, 3),
    (2, 1, 3, 3, 1, 1),
    (2, 1, 3, 1, 3, 1),
    (3, 1, 1, 1, 2, 3),
    (3, 1, 1, 3, 2, 1),
    (3, 3, 1, 1, 2, 1),
    (3, 1, 2, 1, 1, 3),
    (3, 1, 2, 3, 1, 1),
    (3, 3, 2, 1, 1, 1),
    (3, 1, 4, 1, 1, 1),
    (2, 2, 1, 4, 1, 1),
    (4, 3, 1, 1, 1, 1),
    (1, 1, 1, 2, 2, 4),
    (1, 1, 1, 4, 2, 2),
    (1, 2, 1, 1, 2, 4),
    (1, 2, 1, 4, 2, 1),
    (1, 4, 1, 1, 2, 2),
    (1, 4, 1, 2, 2, 1),
    (1, 1, 2, 2, 1, 4),
    (1, 1, 2, 4, 1, 2),
    (1, 2, 2, 1, 1, 4),
    (1, 2, 2, 4, 1, 1),
    (1, 4, 2, 1, 1, 2),
    (1, 4, 2, 2, 1, 1),
    (2, 4, 1, 2, 1, 1),
    (2, 2, 1, 1, 1, 4),
    (4, 1, 3, 1, 1, 1),
    (2, 4, 1, 1, 1, 2),
    (1, 3, 4, 1, 1, 1),
    (1, 1, 1, 2, 4, 2),
    (1, 2, 1, 1, 4, 2),
    (1, 2, 1, 2, 4, 1),
    (1, 1, 4, 2, 1, 2),
    (1, 2, 4, 1, 1, 2),
    (1, 2, 4, 2, 1, 1),
    (4, 1, 1, 2, 1, 2),
    (4, 2, 1, 1, 1, 2),
    (4, 2, 1, 2, 1, 1),
    (2, 1, 2, 1, 4, 1),
    (2, 1, 4, 1, 2, 1),
    (4, 1, 2, 1, 2, 1),
    (1, 1, 1, 1, 4, 3),
    (1, 1, 1, 3, 4, 1),
    (1, 3, 1, 1, 4, 1),
    (1, 1, 4, 1, 1, 3),
    (1, 1, 4, 3, 1, 1),
    (4, 1, 1, 1, 1, 3),
    (4, 1, 1, 3, 1, 1),
    (1, 1, 3, 1, 4, 1),
    (1, 1, 4, 1, 3, 1),
    (3, 1, 1, 1, 4, 1),
    (4, 1, 1, 1, 3, 1),
    (2, 1, 1, 4, 1, 2),
    (2, 1, 1, 2, 1, 4),
    (2, 1, 1, 2, 3, 2),
    (2, 3, 3, 1, 1, 1, 2),  # STOP (106): 7 elements
]

# Special symbol indices
START_B = 104
CODE_C = 99  # switch to Code C (digit-pair encoding)
STOP = 106

# Content: alpha prefix in Code B, digit suffix in Code C (demonstrates subset switching)
alpha_part = "SHIP-"
digit_part = "20240101"
content = alpha_part + digit_part

# Encode: START_B → Code B chars → CODE_C switch → digit pairs → checksum → STOP
raw_values = [START_B]
for ch in alpha_part:
    raw_values.append(CODE128B_CHARS.index(ch))
raw_values.append(CODE_C)
for i in range(0, len(digit_part), 2):
    raw_values.append(int(digit_part[i : i + 2]))

checksum_val = raw_values[0]
for pos, v in enumerate(raw_values[1:], 1):
    checksum_val += pos * v
check_digit = checksum_val % 103

values = raw_values + [check_digit, STOP]

# Expand encoded values to bar-module widths
bar_pattern = []
for val in values:
    bar_pattern.extend(CODE128_PATTERNS[val])

# Build module heights: even idx = bar (100), odd idx = space (0), with quiet zones
quiet_zone = 10
bar_heights = [0] * quiet_zone
for idx, width in enumerate(bar_pattern):
    bar_heights.extend([100 if idx % 2 == 0 else 0] * width)
bar_heights.extend([0] * quiet_zone)

# Style — elevated warm-white panel for barcode area; outer bg follows theme
custom_style = Style(
    background=PAGE_BG,
    plot_background=ELEVATED_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=("#000000",),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=0,
    tooltip_font_size=0,
)

# Square canvas suits barcode layout; tight bottom margin eliminates dead space
chart = pygal.Bar(
    width=2400,
    height=2400,
    style=custom_style,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    spacing=0,
    margin_top=200,
    margin_bottom=100,
    margin_left=300,
    margin_right=300,
    title="barcode-code128 · python · pygal · anyplot.ai",
    print_values=False,
    range=(0, 100),
)

chart.add("", bar_heights)
# Human-readable text + encoding metadata: content, subset path, char count, check digit
chart.x_title = f"{content}  |  Subset: Code B→C  |  {len(content)} chars  |  Check: {check_digit}"

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
