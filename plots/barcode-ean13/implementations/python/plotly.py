"""anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: plotly 7.1.0 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os
import sys
from itertools import groupby


# Prevent this file (plotly.py) from shadowing the installed plotly package
sys.path = [p for p in sys.path if p not in ("", os.path.dirname(os.path.abspath(__file__)))]

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Constants: the EAN-13 standard, true for any code
L_CODES = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"]
G_CODES = ["0100111", "0110011", "0011011", "0100001", "0011101", "0111001", "0000101", "0010001", "0001001", "0010111"]
R_CODES = ["1110010", "1100110", "1101100", "1000010", "1011100", "1001110", "1010000", "1000100", "1001000", "1110100"]
# The first digit selects the L/G parity of the six left digits
PARITY = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]
START_GUARD = "101"
CENTER_GUARD = "01010"
END_GUARD = "101"
QUIET_MODULES = 9  # minimum quiet zone on each side, in modules

# Data: replace with your own 12 or 13 digit code (the check digit is added to a 12 digit code)
EAN_CODE = "4006381333931"  # German product

# Plot: encode the code into modules, then draw one rectangle per bar
code = EAN_CODE
if len(code) == 12:
    weighted = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(code))
    code += str((10 - weighted % 10) % 10)

parity = PARITY[int(code[0])]
left = "".join((L_CODES if p == "L" else G_CODES)[int(d)] for p, d in zip(parity, code[1:7], strict=True))
right = "".join(R_CODES[int(d)] for d in code[7:])
pattern = START_GUARD + left + CENTER_GUARD + right + END_GUARD

# Module index ranges of the three guards
center_start = len(START_GUARD) + len(left)
guards = (
    set(range(len(START_GUARD)))
    | set(range(center_start, center_start + len(CENTER_GUARD)))
    | set(range(len(pattern) - len(END_GUARD), len(pattern)))
)

module = 3  # width of one module in plot units
bar_top = 200
bar_bottom = 0
guard_bottom = -30  # guard bars reach down between the digit groups
quiet = QUIET_MODULES * module
total_width = 2 * quiet + len(pattern) * module

fig = go.Figure()
for is_bar, run in groupby(enumerate(pattern), key=lambda m: m[1] == "1"):
    if is_bar:
        # One rectangle per bar (a run of consecutive 1-modules); guards never touch digit bars
        modules = [i for i, _ in run]
        x0 = quiet + modules[0] * module
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x0 + len(modules) * module,
            y0=guard_bottom if modules[0] in guards else bar_bottom,
            y1=bar_top,
            fillcolor=INK,
            line={"width": 0},
        )

# Human-readable digits: the first outside the left guard, six under each half
digit_y = -48
digit_font = {"size": 22, "family": "monospace", "color": INK}
digit_width = 7 * module
left_start = quiet + len(START_GUARD) * module
right_start = quiet + (center_start + len(CENTER_GUARD)) * module
first_x = quiet - 4 * module
digit_xs = (
    [first_x]
    + [left_start + (i + 0.5) * digit_width for i in range(6)]
    + [right_start + (i + 0.5) * digit_width for i in range(6)]
)
for x, digit in zip(digit_xs, code, strict=True):
    fig.add_annotation(x=x, y=digit_y, text=digit, showarrow=False, font=digit_font)

# Segment labels: country prefix, manufacturer, product, check digit
segment_y = -80
segments = [
    ((digit_xs[0] + digit_xs[2]) / 2, "Country"),
    (left_start + 4.0 * digit_width, "Manufacturer"),
    (right_start + 2.5 * digit_width, "Product"),
    (right_start + 5.5 * digit_width, "Check"),
]
for x, label in segments:
    fig.add_annotation(x=x, y=segment_y, text=label, showarrow=False, font={"size": 14, "color": INK_SOFT})

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "barcode-ean13 · python · plotly · anyplot.ai",
        "font": {"size": 20, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"visible": False, "range": [0, total_width]},
    yaxis={"visible": False, "range": [segment_y - 18, bar_top + 12]},
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    margin={"l": 40, "r": 40, "t": 60, "b": 30},
    width=800,
    height=450,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
