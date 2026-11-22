""" anyplot.ai
kagi-basic: Basic Kagi Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"

# Imprint palette: green for yang (bullish), red for yin (bearish)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
YANG_COLOR = IMPRINT_PALETTE[0]
YIN_COLOR = IMPRINT_PALETTE[4]

# Constants
REVERSAL = 0.04  # a Kagi line turns only when price reverses by this share
YANG_WIDTH = 12  # thick line: price above the previous shoulder
YIN_WIDTH = 4  # thin line: price below the previous waist

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 300
returns = np.random.normal(0.0006, 0.02, n_days)
df = pd.DataFrame({DATE: pd.bdate_range("2024-01-02", periods=n_days), CLOSE: 100 * np.cumprod(1 + returns)})

# Plot: Kagi construction from the closing prices
prices = df[CLOSE].to_numpy()

columns = []
current_direction = "up"
last_high = prices[0]
last_low = prices[0]
prev_swing_high = prices[0]
prev_swing_low = prices[0]
col_idx = 0
current_col = {"x": col_idx, "start": prices[0], "end": prices[0], "type": "yang"}

for price in prices[1:]:
    if current_direction == "up":
        if price > last_high:
            last_high = price
            current_col["end"] = price
            if price > prev_swing_high:
                current_col["type"] = "yang"
        elif price < last_high * (1 - REVERSAL):
            columns.append(current_col)
            prev_swing_high = last_high
            col_idx += 1
            current_col = {
                "x": col_idx,
                "start": columns[-1]["end"],
                "end": price,
                "type": "yin" if price < prev_swing_low else columns[-1]["type"],
            }
            current_direction = "down"
            last_low = price
    else:
        if price < last_low:
            last_low = price
            current_col["end"] = price
            if price < prev_swing_low:
                current_col["type"] = "yin"
        elif price > last_low * (1 + REVERSAL):
            columns.append(current_col)
            prev_swing_low = last_low
            col_idx += 1
            current_col = {
                "x": col_idx,
                "start": columns[-1]["end"],
                "end": price,
                "type": "yang" if price > prev_swing_high else columns[-1]["type"],
            }
            current_direction = "up"
            last_high = price

columns.append(current_col)

# Line segments per state: vertical moves joined by horizontal shoulders and waists
segments = []  # (is_yang, [(x1, y1), (x2, y2)]), one pygal series each: pygal joins points inside a series
prev_x = None
prev_y = None
for col in columns:
    is_yang = col["type"] == "yang"
    if prev_x is not None:
        segments.append((is_yang, [(prev_x, prev_y), (col["x"], prev_y)]))
    segments.append((is_yang, [(col["x"], col["start"]), (col["x"], col["end"])]))
    prev_x = col["x"]
    prev_y = col["end"]

y_values = [y for _, pts in segments for _, y in pts]
y_low, y_high = min(y_values), max(y_values)
y_span = y_high - y_low

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(YANG_COLOR if yang else YIN_COLOR for yang, _ in segments),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    guide_stroke_dasharray="4,4",
    opacity=1.0,
    opacity_hover=1.0,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="kagi-basic · python · pygal · anyplot.ai",
    x_title="Kagi line index",
    y_title=CLOSE,
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    show_legend=False,
    stroke=True,
    fill=False,
    margin=60,
    range=(y_low - 0.02 * y_span, y_high + 0.14 * y_span),  # headroom above the data for the legend
)
for is_yang, points in segments:
    chart.add(None, points, stroke_style={"width": YANG_WIDTH if is_yang else YIN_WIDTH, "linecap": "round"})

svg_str = chart.render().decode("utf-8")

# pygal's stylesheet gives every series one width and a faded stroke; pin each series' own
css_override = "".join(
    f".serie-{i} .line {{ stroke-width: {YANG_WIDTH if is_yang else YIN_WIDTH}px !important; "
    f"stroke: {YANG_COLOR if is_yang else YIN_COLOR} !important; stroke-opacity: 1 !important; }}\n"
    for i, (is_yang, _) in enumerate(segments)
)
svg_str = svg_str.replace("</style>", css_override + "</style>", 1)

# Manual legend: pygal's own swatches cannot show line weight
legend_svg = f"""
<g class="manual-legend" transform="translate(1860, 190)">
  <rect x="-24" y="-40" width="1180" height="80" fill="{ELEVATED_BG}" fill-opacity="0.95" rx="8"/>
  <line x1="0" y1="0" x2="70" y2="0" stroke="{YANG_COLOR}" stroke-width="{YANG_WIDTH}" stroke-linecap="round"/>
  <text x="95" y="13" font-size="36" fill="{INK}" font-family="Verdana, sans-serif">Yang (bullish) · thick</text>
  <line x1="600" y1="0" x2="670" y2="0" stroke="{YIN_COLOR}" stroke-width="{YIN_WIDTH}" stroke-linecap="round"/>
  <text x="695" y="13" font-size="36" fill="{INK}" font-family="Verdana, sans-serif">Yin (bearish) · thin</text>
</g>
"""
svg_str = svg_str.replace("</svg>", legend_svg + "</svg>")

# Save
cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), write_to=f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
