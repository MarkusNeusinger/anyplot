"""anyplot.ai
barcode-code128: Code 128 Barcode
Library: altair 6.3.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-26
"""

import os

import altair as alt
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Code 128 patterns indexed by symbol value: 0-102 data/check values (subset B value = ord(char) - 32),
# 103-105 start A/B/C, 106 stop. Each string lists bar, space, bar, space, ... widths in modules.
CODE128_PATTERNS = [
    "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312",
    "132212", "221213", "221312", "231212", "112232", "122132", "122231", "113222",
    "123122", "123221", "223211", "221132", "221231", "213212", "223112", "312131",
    "311222", "321122", "321221", "312212", "322112", "322211", "212123", "212321",
    "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
    "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121",
    "313121", "211331", "231131", "213113", "213311", "213131", "311123", "311321",
    "331121", "312113", "312311", "332111", "314111", "221411", "431111", "111224",
    "111422", "121124", "121421", "141122", "141221", "112214", "112412", "122114",
    "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
    "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112",
    "421211", "212141", "214121", "412121", "111143", "111341", "131141", "114113",
    "114311", "411113", "411311", "113141", "114131", "311141", "411131", "211412",
    "211214", "211232", "2331112",
]  # fmt: skip
START_B, STOP = 104, 106

# Columns of the drawing tables
X0, X1, Y0, Y1 = "x", "x2", "y", "y2"
TEXT, ENCODED = "text", "encoded"

# Data — encode a shipping label
content = "SHIP-2024-ABC123"

# Build the barcode pattern: start B, data characters, mod-103 check character, stop
values = [ord(char) - 32 for char in content]
check_value = (START_B + sum(value * pos for pos, value in enumerate(values, start=1))) % 103
symbols = [START_B, *values, check_value, STOP]
pattern = [int(width) for symbol in symbols for width in CODE128_PATTERNS[symbol]]

# Convert pattern to bar rectangles
bars_data = []
x = 0
is_bar = True  # Start with bar (dark)
for width in pattern:
    if is_bar:
        bars_data.append({X0: x, X1: x + width, Y0: 0, Y1: 1, ENCODED: f"Code 128B: {content}"})
    x += width
    is_bar = not is_bar

total_width = x

# Add quiet zones (10% on each side)
quiet_zone = total_width * 0.1
for bar in bars_data:
    bar[X0] += quiet_zone
    bar[X1] += quiet_zone
total_width_with_zones = total_width + 2 * quiet_zone

# Plot
df_bars = pd.DataFrame(bars_data)
df_text = pd.DataFrame([{X0: total_width_with_zones / 2, Y0: -0.17, TEXT: content}])

# Scannable symbol: dark bars on a light tile in both themes (the spec asks for black on white).
# The tile spans the quiet zones; the page around it follows the theme.
TILE = "#FAF8F1"
BAR_INK = "#1A1A17"
margin = total_width_with_zones * 0.04
df_tile = pd.DataFrame([{X0: 0, X1: total_width_with_zones, Y0: -0.32, Y1: 1.1}])
x_scale = alt.Scale(domain=[-margin, total_width_with_zones + margin], nice=False)
y_scale = alt.Scale(domain=[-0.4, 1.18], nice=False)

tile_chart = (
    alt.Chart(df_tile)
    .mark_rect(color=TILE)
    .encode(
        x=alt.X(f"{X0}:Q", scale=x_scale, axis=None),
        x2=f"{X1}:Q",
        y=alt.Y(f"{Y0}:Q", scale=y_scale, axis=None),
        y2=f"{Y1}:Q",
    )
)

# Barcode bars, tooltip shows encoded content
bars_chart = (
    alt.Chart(df_bars)
    .mark_rect(color=BAR_INK)
    .encode(
        x=alt.X(f"{X0}:Q", scale=x_scale, axis=None),
        x2=f"{X1}:Q",
        y=alt.Y(f"{Y0}:Q", scale=y_scale, axis=None),
        y2=f"{Y1}:Q",
        tooltip=[alt.Tooltip(f"{ENCODED}:N", title="Encoded")],
    )
)

# Human-readable text below barcode
text_chart = (
    alt.Chart(df_text)
    .mark_text(fontSize=22, font="monospace", fontWeight="bold", color=BAR_INK)
    .encode(x=alt.X(f"{X0}:Q", scale=x_scale), y=alt.Y(f"{Y0}:Q", scale=y_scale), text=f"{TEXT}:N")
)

chart = (
    (tile_chart + bars_chart + text_chart)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title("barcode-code128 · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
