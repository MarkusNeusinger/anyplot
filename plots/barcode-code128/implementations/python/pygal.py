"""anyplot.ai
barcode-code128: Code 128 Barcode
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-21
"""

import os

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Code 128B character table: space (value 0) through ~ (value 94)
CODE128B_CHARS = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

# 107 Code 128 bar/space patterns (indices 0–106); each tuple is (b,s,b,s,b,s) widths
# Index 106 is the STOP pattern with 7 elements
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
    (2, 3, 3, 1, 1, 1, 2),
]

# Data — laboratory specimen tracking ID
content = "SPECIMEN-LAB-2024"

# Encode with Code 128B: START_B=104, data chars, modulo-103 checksum, STOP=106
values = [104]
for ch in content:
    values.append(CODE128B_CHARS.index(ch) if ch in CODE128B_CHARS else 0)

checksum = values[0]
for i, v in enumerate(values[1:], 1):
    checksum += i * v
values.append(checksum % 103)
values.append(106)

# Expand encoded values to bar-module widths
bar_pattern = []
for val in values:
    bar_pattern.extend(CODE128_PATTERNS[val])

# Build per-module height list; even indices = bars (black=100), odd = spaces (white=0)
quiet_zone = 10
bar_heights = [0] * quiet_zone
for idx, width in enumerate(bar_pattern):
    bar_heights.extend([100 if idx % 2 == 0 else 0] * width)
bar_heights.extend([0] * quiet_zone)

# Style — barcode area stays white for scannability; outer bg follows theme
custom_style = Style(
    background=PAGE_BG,
    plot_background="#FFFFFF",
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

# Plot
chart = pygal.Bar(
    width=3200,
    height=1800,
    style=custom_style,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    spacing=0,
    margin_top=200,
    margin_bottom=400,
    margin_left=400,
    margin_right=400,
    title="barcode-code128 · python · pygal · anyplot.ai",
    print_values=False,
    range=(0, 100),
)

chart.add("", bar_heights)
chart.x_title = content

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
