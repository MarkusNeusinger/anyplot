"""anyplot.ai
barcode-code128: Code 128 Barcode
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-21
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    geom_rect,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    layer_tooltips,
    scale_fill_identity,
    theme,
    theme_void,
    xlim,
    ylim,
)


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Code 128 encoding patterns: each digit is the width of alternating bar/space elements
CODE128_PATTERNS = {
    0: "212222",
    1: "222122",
    2: "222221",
    3: "121223",
    4: "121322",
    5: "131222",
    6: "122213",
    7: "122312",
    8: "132212",
    9: "221213",
    10: "221312",
    11: "231212",
    12: "112232",
    13: "122132",
    14: "122231",
    15: "113222",
    16: "123122",
    17: "123221",
    18: "223211",
    19: "221132",
    20: "221231",
    21: "213212",
    22: "223112",
    23: "312131",
    24: "311222",
    25: "321122",
    26: "321221",
    27: "312212",
    28: "322112",
    29: "322211",
    30: "212123",
    31: "212321",
    32: "232121",
    33: "111323",
    34: "131123",
    35: "131321",
    36: "112313",
    37: "132113",
    38: "132311",
    39: "211313",
    40: "231113",
    41: "231311",
    42: "112133",
    43: "112331",
    44: "132131",
    45: "113123",
    46: "113321",
    47: "133121",
    48: "313121",
    49: "211331",
    50: "231131",
    51: "213113",
    52: "213311",
    53: "213131",
    54: "311123",
    55: "311321",
    56: "331121",
    57: "312113",
    58: "312311",
    59: "332111",
    60: "314111",
    61: "221411",
    62: "431111",
    63: "111224",
    64: "111422",
    65: "121124",
    66: "121421",
    67: "141122",
    68: "141221",
    69: "112214",
    70: "112412",
    71: "122114",
    72: "122411",
    73: "142112",
    74: "142211",
    75: "241211",
    76: "221114",
    77: "413111",
    78: "241112",
    79: "134111",
    80: "111242",
    81: "121142",
    82: "121241",
    83: "114212",
    84: "124112",
    85: "124211",
    86: "411212",
    87: "421112",
    88: "421211",
    89: "212141",
    90: "214121",
    91: "412121",
    92: "111143",
    93: "111341",
    94: "131141",
    95: "114113",
    96: "114311",
    97: "411113",
    98: "411311",
    99: "113141",
    100: "114131",
    101: "311141",
    102: "411131",
    103: "211412",  # Start Code A
    104: "211214",  # Start Code B
    105: "211232",  # Start Code C
    106: "2331112",  # Stop (7 elements, 13 units)
}

# Code 128B maps ASCII 32–126 (printable chars) to values 0–94
CODE128B_CHARS = {chr(i + 32): i for i in range(95)}

# Data — shipping label barcode
content = "SHIP-2024-ABC123"

# Encode each character to its Code 128B symbol value
char_values = [CODE128B_CHARS.get(c, 0) for c in content]

# Checksum: start-B constant (104) plus each value weighted by position (1-indexed)
checksum = 104
for i, v in enumerate(char_values):
    checksum += v * (i + 1)
checksum = checksum % 103

# Full symbol sequence: start-B + data symbols + check digit + stop
sequence = [104] + char_values + [checksum, 106]

# Rasterize symbols into bar rectangles; spaces are implicit gaps
quiet_zone = 10
x_pos = quiet_zone
bar_ymin, bar_ymax = 32.0, 98.0
bars = []

for sym_idx, code in enumerate(sequence):
    if sym_idx == 0:
        sym_label = "Start Code B"
    elif sym_idx == len(sequence) - 1:
        sym_label = "Stop"
    elif sym_idx == len(sequence) - 2:
        sym_label = f"Check digit: {checksum}"
    else:
        char = content[sym_idx - 1]
        sym_label = f"'{char}'  pos {sym_idx}  Code 128B value {char_values[sym_idx - 1]}"
    is_bar = True
    for ch in CODE128_PATTERNS[code]:
        w = int(ch)
        if is_bar:
            bars.append(
                {
                    "xmin": float(x_pos),
                    "xmax": float(x_pos + w),
                    "ymin": bar_ymin,
                    "ymax": bar_ymax,
                    "fill": "#000000",
                    "symbol": sym_label,
                }
            )
        x_pos += w
        is_bar = not is_bar

total_width = x_pos + quiet_zone
cx = total_width / 2

df_bars = pd.DataFrame(bars)

# White background rectangle ensures barcode contrast on both light and dark themes
df_barcode_bg = pd.DataFrame(
    {
        "xmin": [0.0],
        "xmax": [float(total_width)],
        "ymin": [bar_ymin - 4.0],
        "ymax": [bar_ymax + 4.0],
        "fill": ["#FFFFFF"],
    }
)

df_text = pd.DataFrame({"x": [cx], "y": [18.0], "label": [content]})
df_annotation = pd.DataFrame(
    {"x": [cx], "y": [7.0], "label": [f"{len(content)} chars · Code 128B · check digit: {checksum}"]}
)
df_subtitle = pd.DataFrame(
    {"x": [cx], "y": [118.0], "label": [f"Shipping label · Code 128B · {len(content)} characters"]}
)
df_title = pd.DataFrame({"x": [cx], "y": [127.0], "label": ["barcode-code128 · python · letsplot · anyplot.ai"]})

# Plot
plot = (
    ggplot()
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"), data=df_barcode_bg, color="#FFFFFF"
    )
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"),
        data=df_bars,
        tooltips=layer_tooltips().line("@{symbol}"),
    )
    + scale_fill_identity()
    + geom_text(aes(x="x", y="y", label="label"), data=df_text, size=14, color=INK)
    + geom_text(aes(x="x", y="y", label="label"), data=df_annotation, size=9, color=INK_SOFT)
    + geom_text(aes(x="x", y="y", label="label"), data=df_subtitle, size=9, color=INK_SOFT)
    + geom_text(aes(x="x", y="y", label="label"), data=df_title, size=11, color=INK_SOFT)
    + xlim(0, total_width)
    + ylim(0, 135)
    + theme_void()
    + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG), panel_background=element_rect(fill=PAGE_BG))
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
