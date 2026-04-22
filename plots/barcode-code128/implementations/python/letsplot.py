""" pyplots.ai
barcode-code128: Code 128 Barcode
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-19
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    geom_rect,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    scale_fill_identity,
    theme,
    theme_void,
    xlim,
    ylim,
)


LetsPlot.setup_html()

# Code 128 encoding tables
# Each character is encoded as 6 alternating bars and spaces with varying widths (1-4 units)
# Total width per character: 11 units (except stop: 13 units)

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
    106: "2331112",  # Stop pattern (7 elements, total 13 units)
}

# Code 128B character to value mapping (ASCII 32-127 printable characters)
CODE128B_CHARS = {chr(i + 32): i for i in range(95)}
CODE128B_CHARS["FNC1"] = 102
CODE128B_CHARS["FNC2"] = 97
CODE128B_CHARS["FNC3"] = 96
CODE128B_CHARS["FNC4"] = 100


def encode_code128b(text):
    """Encode text using Code 128B (ASCII printable characters)."""
    values = []
    for char in text:
        if char in CODE128B_CHARS:
            values.append(CODE128B_CHARS[char])
        else:
            values.append(0)
    return values


def calculate_checksum(values):
    """Calculate Code 128 check digit using modulo 103."""
    checksum = 104  # Start code B value
    for i, value in enumerate(values):
        checksum += value * (i + 1)
    return checksum % 103


def pattern_to_bars(pattern):
    """Convert pattern string to list of (is_bar, width) tuples."""
    bars = []
    is_bar = True
    for width in pattern:
        bars.append((is_bar, int(width)))
        is_bar = not is_bar
    return bars


def generate_barcode_bars(text, bar_y_min, bar_y_max):
    """Generate complete barcode bar data."""
    values = encode_code128b(text)
    checksum = calculate_checksum(values)
    sequence = [104] + values + [checksum, 106]

    all_bars = []
    quiet_zone = 10
    x_pos = quiet_zone

    for code in sequence:
        pattern = CODE128_PATTERNS[code]
        bars = pattern_to_bars(pattern)
        for is_bar, width in bars:
            if is_bar:
                all_bars.append(
                    {
                        "xmin": float(x_pos),
                        "xmax": float(x_pos + width),
                        "ymin": float(bar_y_min),
                        "ymax": float(bar_y_max),
                        "fill": "#000000",
                    }
                )
            x_pos += width

    total_width = x_pos + quiet_zone
    return all_bars, total_width


# Data - Example shipping label content
content = "SHIP-2024-ABC123"

# Bar dimensions
bar_height = 80
bar_y_min = 20
bar_y_max = bar_y_min + bar_height

# Generate barcode bars
bars_data, total_width = generate_barcode_bars(content, bar_y_min, bar_y_max)

# Create DataFrame for bars
df_bars = pd.DataFrame(bars_data)

# Create DataFrame for text labels
df_content = pd.DataFrame({"x": [total_width / 2], "y": [8], "label": [content]})

df_title = pd.DataFrame(
    {"x": [total_width / 2], "y": [bar_y_max + 15], "label": ["barcode-code128 · letsplot · pyplots.ai"]}
)

# Create plot
plot = (
    ggplot()
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"), data=df_bars)
    + scale_fill_identity()
    + geom_text(aes(x="x", y="y", label="label"), data=df_content, size=18)
    + geom_text(aes(x="x", y="y", label="label"), data=df_title, size=14)
    + xlim(0, total_width)
    + ylim(0, bar_y_max + 30)
    + theme_void()
    + theme(plot_background=element_blank(), panel_background=element_blank())
    + ggsize(1600, 900)
)

# Save outputs
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")
