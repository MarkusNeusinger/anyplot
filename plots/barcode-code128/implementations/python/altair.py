""" anyplot.ai
barcode-code128: Code 128 Barcode
Library: altair 6.1.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-21
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


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
        bars_data.append({"x": x, "x2": x + width, "y": 0, "y2": 1, "encoded": f"Code 128B: {content}"})
    x += width
    is_bar = not is_bar

total_width = x

# Add quiet zones (10% on each side)
quiet_zone = total_width * 0.1
for bar in bars_data:
    bar["x"] += quiet_zone
    bar["x2"] += quiet_zone
total_width_with_zones = total_width + 2 * quiet_zone

df_bars = pd.DataFrame(bars_data)
df_text = pd.DataFrame([{"x": total_width_with_zones / 2, "y": -0.15, "text": content}])

# Barcode bars — theme-adaptive INK color, tooltip shows encoded content
bars_chart = (
    alt.Chart(df_bars)
    .mark_rect(color="#1A1A17")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, total_width_with_zones]), axis=None),
        x2="x2:Q",
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-0.3, 1.1]), axis=None),
        y2="y2:Q",
        tooltip=[alt.Tooltip("encoded:N", title="Encoded")],
    )
)

# Human-readable text below barcode
text_chart = (
    alt.Chart(df_text)
    .mark_text(fontSize=20, font="monospace", fontWeight="bold", color="#1A1A17")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

chart = (
    (bars_chart + text_chart)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        title=alt.Title("barcode-code128 · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .interactive()
    .configure_view(strokeWidth=0, fill="#FAF8F1", continuousWidth=620, continuousHeight=320)
    .configure_title(color=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# PAD to canonical 3200×1800 — vl-convert leaves chart undersized; never crop
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
