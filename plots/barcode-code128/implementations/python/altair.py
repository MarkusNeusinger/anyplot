"""anyplot.ai
barcode-code128: Code 128 Barcode
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-21
"""

import os

import altair as alt
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Code 128 encoding tables (subset B - ASCII printable characters)
# Each pattern is a sequence of bar widths: [bar, space, bar, space, bar, space] in units
CODE128_PATTERNS = {
    " ": [2, 1, 2, 2, 2, 2],
    "!": [2, 2, 2, 1, 2, 2],
    '"': [2, 2, 2, 2, 2, 1],
    "#": [1, 2, 1, 2, 2, 3],
    "$": [1, 2, 1, 3, 2, 2],
    "%": [1, 3, 1, 2, 2, 2],
    "&": [1, 2, 2, 2, 1, 3],
    "'": [1, 2, 2, 3, 1, 2],
    "(": [1, 3, 2, 2, 1, 2],
    ")": [2, 2, 1, 2, 1, 3],
    "*": [2, 2, 1, 3, 1, 2],
    "+": [2, 3, 1, 2, 1, 2],
    ",": [1, 1, 2, 2, 3, 2],
    "-": [1, 2, 2, 1, 3, 2],
    ".": [1, 2, 2, 2, 3, 1],
    "/": [1, 1, 3, 2, 2, 2],
    "0": [1, 2, 3, 1, 2, 2],
    "1": [1, 2, 3, 2, 2, 1],
    "2": [2, 2, 3, 2, 1, 1],
    "3": [2, 2, 1, 1, 3, 2],
    "4": [2, 2, 1, 2, 3, 1],
    "5": [2, 1, 3, 2, 1, 2],
    "6": [2, 2, 3, 1, 1, 2],
    "7": [3, 1, 2, 1, 3, 1],
    "8": [3, 1, 1, 2, 2, 2],
    "9": [3, 2, 1, 1, 2, 2],
    ":": [3, 2, 1, 2, 2, 1],
    ";": [3, 1, 2, 2, 1, 2],
    "<": [3, 2, 2, 1, 1, 2],
    "=": [3, 2, 2, 2, 1, 1],
    ">": [2, 1, 2, 1, 2, 3],
    "?": [2, 1, 2, 3, 2, 1],
    "@": [2, 3, 2, 1, 2, 1],
    "A": [1, 1, 1, 3, 2, 3],
    "B": [1, 3, 1, 1, 2, 3],
    "C": [1, 3, 1, 3, 2, 1],
    "D": [1, 1, 2, 3, 1, 3],
    "E": [1, 3, 2, 1, 1, 3],
    "F": [1, 3, 2, 3, 1, 1],
    "G": [2, 1, 1, 3, 1, 3],
    "H": [2, 3, 1, 1, 1, 3],
    "I": [2, 3, 1, 3, 1, 1],
    "J": [1, 1, 2, 1, 3, 3],
    "K": [1, 1, 2, 3, 3, 1],
    "L": [1, 3, 2, 1, 3, 1],
    "M": [1, 1, 3, 1, 2, 3],
    "N": [1, 1, 3, 3, 2, 1],
    "O": [1, 3, 3, 1, 2, 1],
    "P": [3, 1, 3, 1, 2, 1],
    "Q": [2, 1, 1, 3, 3, 1],
    "R": [2, 3, 1, 1, 3, 1],
    "S": [2, 1, 3, 1, 1, 3],
    "T": [2, 1, 3, 3, 1, 1],
    "U": [2, 1, 3, 1, 3, 1],
    "V": [3, 1, 1, 1, 2, 3],
    "W": [3, 1, 1, 3, 2, 1],
    "X": [3, 3, 1, 1, 2, 1],
    "Y": [3, 1, 2, 1, 1, 3],
    "Z": [3, 1, 2, 3, 1, 1],
    "[": [3, 3, 2, 1, 1, 1],
    "\\": [3, 1, 4, 1, 1, 1],
    "]": [2, 2, 1, 4, 1, 1],
    "^": [4, 3, 1, 1, 1, 1],
    "_": [1, 1, 1, 2, 2, 4],
    "`": [1, 1, 1, 4, 2, 2],
    "a": [1, 2, 1, 1, 2, 4],
    "b": [1, 2, 1, 4, 2, 1],
    "c": [1, 4, 1, 1, 2, 2],
    "d": [1, 4, 1, 2, 2, 1],
    "e": [1, 1, 2, 2, 1, 4],
    "f": [1, 1, 2, 4, 1, 2],
    "g": [1, 2, 2, 1, 1, 4],
    "h": [1, 2, 2, 4, 1, 1],
    "i": [1, 4, 2, 1, 1, 2],
    "j": [1, 4, 2, 2, 1, 1],
    "k": [2, 4, 1, 2, 1, 1],
    "l": [2, 2, 1, 1, 1, 4],
    "m": [4, 1, 3, 1, 1, 1],
    "n": [2, 4, 1, 1, 1, 2],
    "o": [1, 3, 4, 1, 1, 1],
    "p": [1, 1, 1, 2, 4, 2],
    "q": [1, 2, 1, 1, 4, 2],
    "r": [1, 2, 1, 2, 4, 1],
    "s": [1, 1, 4, 2, 1, 2],
    "t": [1, 2, 4, 1, 1, 2],
    "u": [1, 2, 4, 2, 1, 1],
    "v": [4, 1, 1, 2, 1, 2],
    "w": [4, 2, 1, 1, 1, 2],
    "x": [4, 2, 1, 2, 1, 1],
    "y": [2, 1, 2, 1, 4, 1],
    "z": [2, 1, 4, 1, 2, 1],
    "{": [4, 1, 2, 1, 2, 1],
    "|": [1, 1, 1, 1, 4, 3],
    "}": [1, 1, 1, 3, 4, 1],
    "~": [1, 3, 1, 1, 4, 1],
}

# Code 128 value mapping for subset B (characters to values for checksum)
CODE128_VALUES = {chr(i + 32): i for i in range(95)}

# Special patterns
START_B = [2, 1, 1, 2, 1, 4]  # Start Code B (value 104)
STOP = [2, 3, 3, 1, 1, 1, 2]  # Stop pattern

# Check digit patterns (values 0-102)
CHECK_PATTERNS = [
    [2, 1, 2, 2, 2, 2],
    [2, 2, 2, 1, 2, 2],
    [2, 2, 2, 2, 2, 1],
    [1, 2, 1, 2, 2, 3],
    [1, 2, 1, 3, 2, 2],
    [1, 3, 1, 2, 2, 2],
    [1, 2, 2, 2, 1, 3],
    [1, 2, 2, 3, 1, 2],
    [1, 3, 2, 2, 1, 2],
    [2, 2, 1, 2, 1, 3],
    [2, 2, 1, 3, 1, 2],
    [2, 3, 1, 2, 1, 2],
    [1, 1, 2, 2, 3, 2],
    [1, 2, 2, 1, 3, 2],
    [1, 2, 2, 2, 3, 1],
    [1, 1, 3, 2, 2, 2],
    [1, 2, 3, 1, 2, 2],
    [1, 2, 3, 2, 2, 1],
    [2, 2, 3, 2, 1, 1],
    [2, 2, 1, 1, 3, 2],
    [2, 2, 1, 2, 3, 1],
    [2, 1, 3, 2, 1, 2],
    [2, 2, 3, 1, 1, 2],
    [3, 1, 2, 1, 3, 1],
    [3, 1, 1, 2, 2, 2],
    [3, 2, 1, 1, 2, 2],
    [3, 2, 1, 2, 2, 1],
    [3, 1, 2, 2, 1, 2],
    [3, 2, 2, 1, 1, 2],
    [3, 2, 2, 2, 1, 1],
    [2, 1, 2, 1, 2, 3],
    [2, 1, 2, 3, 2, 1],
    [2, 3, 2, 1, 2, 1],
    [1, 1, 1, 3, 2, 3],
    [1, 3, 1, 1, 2, 3],
    [1, 3, 1, 3, 2, 1],
    [1, 1, 2, 3, 1, 3],
    [1, 3, 2, 1, 1, 3],
    [1, 3, 2, 3, 1, 1],
    [2, 1, 1, 3, 1, 3],
    [2, 3, 1, 1, 1, 3],
    [2, 3, 1, 3, 1, 1],
    [1, 1, 2, 1, 3, 3],
    [1, 1, 2, 3, 3, 1],
    [1, 3, 2, 1, 3, 1],
    [1, 1, 3, 1, 2, 3],
    [1, 1, 3, 3, 2, 1],
    [1, 3, 3, 1, 2, 1],
    [3, 1, 3, 1, 2, 1],
    [2, 1, 1, 3, 3, 1],
    [2, 3, 1, 1, 3, 1],
    [2, 1, 3, 1, 1, 3],
    [2, 1, 3, 3, 1, 1],
    [2, 1, 3, 1, 3, 1],
    [3, 1, 1, 1, 2, 3],
    [3, 1, 1, 3, 2, 1],
    [3, 3, 1, 1, 2, 1],
    [3, 1, 2, 1, 1, 3],
    [3, 1, 2, 3, 1, 1],
    [3, 3, 2, 1, 1, 1],
    [3, 1, 4, 1, 1, 1],
    [2, 2, 1, 4, 1, 1],
    [4, 3, 1, 1, 1, 1],
    [1, 1, 1, 2, 2, 4],
    [1, 1, 1, 4, 2, 2],
    [1, 2, 1, 1, 2, 4],
    [1, 2, 1, 4, 2, 1],
    [1, 4, 1, 1, 2, 2],
    [1, 4, 1, 2, 2, 1],
    [1, 1, 2, 2, 1, 4],
    [1, 1, 2, 4, 1, 2],
    [1, 2, 2, 1, 1, 4],
    [1, 2, 2, 4, 1, 1],
    [1, 4, 2, 1, 1, 2],
    [1, 4, 2, 2, 1, 1],
    [2, 4, 1, 2, 1, 1],
    [2, 2, 1, 1, 1, 4],
    [4, 1, 3, 1, 1, 1],
    [2, 4, 1, 1, 1, 2],
    [1, 3, 4, 1, 1, 1],
    [1, 1, 1, 2, 4, 2],
    [1, 2, 1, 1, 4, 2],
    [1, 2, 1, 2, 4, 1],
    [1, 1, 4, 2, 1, 2],
    [1, 2, 4, 1, 1, 2],
    [1, 2, 4, 2, 1, 1],
    [4, 1, 1, 2, 1, 2],
    [4, 2, 1, 1, 1, 2],
    [4, 2, 1, 2, 1, 1],
    [2, 1, 2, 1, 4, 1],
    [2, 1, 4, 1, 2, 1],
    [4, 1, 2, 1, 2, 1],
    [1, 1, 1, 1, 4, 3],
    [1, 1, 1, 3, 4, 1],
    [1, 3, 1, 1, 4, 1],
    [1, 1, 4, 1, 1, 3],
    [1, 1, 4, 3, 1, 1],
    [4, 1, 1, 1, 1, 3],
    [4, 1, 1, 3, 1, 1],
    [1, 1, 3, 1, 4, 1],
    [1, 1, 4, 1, 3, 1],
    [3, 1, 1, 1, 4, 1],
    [4, 1, 1, 1, 3, 1],
]

# Columns of the drawing tables
X0, X1, Y0, Y1 = "x", "x2", "y", "y2"
TEXT, ENCODED = "text", "encoded"

# Data — encode a shipping label
content = "SHIP-2024-ABC123"

# Build the barcode pattern
pattern = []
pattern.extend(START_B)

checksum = 104  # Start B value
for i, char in enumerate(content):
    if char in CODE128_PATTERNS:
        pattern.extend(CODE128_PATTERNS[char])
        checksum += CODE128_VALUES.get(char, 0) * (i + 1)

check_value = checksum % 103
if check_value < len(CHECK_PATTERNS):
    pattern.extend(CHECK_PATTERNS[check_value])

pattern.extend(STOP)

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
