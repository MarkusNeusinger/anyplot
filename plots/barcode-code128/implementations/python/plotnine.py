"""anyplot.ai
barcode-code128: Code 128 Barcode
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-05-21
"""

import os

import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_rect,
    element_text,
    geom_rect,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Code 128 Subset B patterns (binary: 1=bar, 0=space), 11 modules each, symbols 0-102
CODE128 = [
    "11011001100",
    "11001101100",
    "11001100110",
    "10010011000",
    "10010001100",
    "10001001100",
    "10011001000",
    "10011000100",
    "10001100100",
    "11001001000",
    "11001000100",
    "11000100100",
    "10110011100",
    "10011011100",
    "10011001110",
    "10111001100",
    "10011101100",
    "10011100110",
    "11001110010",
    "11001011100",
    "11001001110",
    "11011100100",
    "11001110100",
    "11101101110",
    "11101001100",
    "11100101100",
    "11100100110",
    "11101100100",
    "11100110100",
    "11100110010",
    "11011011000",
    "11011000110",
    "11000110110",
    "10100011000",
    "10001011000",
    "10001000110",
    "10110001000",
    "10001101000",
    "10001100010",
    "11010001000",
    "11000101000",
    "11000100010",
    "10110111000",
    "10110001110",
    "10001101110",
    "10111011000",
    "10111000110",
    "10001110110",
    "11101110110",
    "11010001110",
    "11000101110",
    "11011101000",
    "11011100010",
    "11011101110",
    "11101011000",
    "11101000110",
    "11100010110",
    "11101101000",
    "11101100010",
    "11100011010",
    "11101111010",
    "11001000010",
    "11110001010",
    "10100110000",
    "10100001100",
    "10010110000",
    "10010000110",
    "10000101100",
    "10000100110",
    "10110010000",
    "10110000100",
    "10011010000",
    "10011000010",
    "10000110100",
    "10000110010",
    "11000010010",
    "11001010000",
    "11110111010",
    "11000010100",
    "10001111010",
    "10100111100",
    "10010111100",
    "10010011110",
    "10111100100",
    "10011110100",
    "10011110010",
    "11110100100",
    "11110010100",
    "11110010010",
    "11011011110",
    "11011110110",
    "11110110110",
    "10101111000",
    "10100011110",
    "10001011110",
    "10111101000",
    "10111100010",
    "11110101000",
    "11110100010",
    "10111011110",
    "10111101110",
    "11101011110",
    "11110101110",
]
START_B = "11010010000"
STOP = "1100011101011"

# Encode specimen label using Code 128 Subset B (ASCII 32-127, symbol = ASCII - 32)
text = "SPECIMEN-2024-B047"
symbol_vals = [ord(c) - 32 for c in text]

check = 104  # Start B value
for i, v in enumerate(symbol_vals):
    check += (i + 1) * v
check %= 103

binary = START_B + "".join(CODE128[v] for v in symbol_vals) + CODE128[check] + STOP

# Convert binary string to bar segments (group consecutive 1-runs)
QUIET = 10
BAR_Y1, BAR_Y2 = 0.28, 0.82

bar_rows = []
i = 0
x = QUIET
while i < len(binary):
    bit = binary[i]
    j = i + 1
    while j < len(binary) and binary[j] == bit:
        j += 1
    run = j - i
    if bit == "1":
        bar_rows.append({"xmin": float(x), "xmax": float(x + run), "ymin": BAR_Y1, "ymax": BAR_Y2})
    x += run
    i = j

total_w = float(x + QUIET)
df_bars = pd.DataFrame(bar_rows)

# White label background (barcode always black-on-white for contrast)
df_bg = pd.DataFrame({"xmin": [2.0], "xmax": [total_w - 2.0], "ymin": [0.06], "ymax": [0.93]})

plot = (
    ggplot()
    + geom_rect(
        data=df_bg, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill="#FFFFFF", colour="none"
    )
    + geom_rect(
        data=df_bars, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill="#1A1A17", colour="none"
    )
    + annotate("text", x=total_w / 2, y=0.15, label=text, colour="#1A1A17", size=9, family="monospace")
    + scale_x_continuous(limits=(0, total_w), expand=(0, 0))
    + scale_y_continuous(limits=(0, 1), expand=(0, 0))
    + labs(title="Specimen Label · barcode-code128 · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, colour=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_title=element_blank(),
        plot_title=element_text(colour=INK, size=12, hjust=0.5),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
