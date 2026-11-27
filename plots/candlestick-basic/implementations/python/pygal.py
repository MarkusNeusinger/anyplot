""" anyplot.ai
candlestick-basic: Basic Candlestick Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-27
"""

import os
import re
import sys
from datetime import datetime, timedelta


# This file is named 'pygal.py'; remove its own directory from sys.path so
# 'import pygal' resolves to the installed package rather than this script itself.
_self_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _self_dir]

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# --- Theme tokens (Imprint palette + theme-adaptive chrome) ---
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Finance semantic: bullish=green (Imprint pos 1), bearish=matte-red (Imprint pos 5)
BULL = IMPRINT_PALETTE[0]
BEAR = IMPRINT_PALETTE[4]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open"  # role: open
HIGH = "High"  # role: high
LOW = "Low"  # role: low
CLOSE = "Close"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=["Date"])
np.random.seed(42)
n_days = 30
dates = []
cur = datetime(2024, 1, 2)
for _ in range(n_days):
    while cur.weekday() >= 5:
        cur += timedelta(days=1)
    dates.append(cur)
    cur += timedelta(days=1)

base_price = 150.0
returns = np.random.randn(n_days) * 2.5
price_series = base_price * np.cumprod(1 + returns / 100)

rows = []
for i, close in enumerate(price_series):
    volatility = np.abs(np.random.randn()) * 2 + 0.5
    intraday_range = close * volatility / 100
    open_price = base_price if i == 0 else rows[-1][CLOSE]
    high = max(open_price, close) + np.random.rand() * intraday_range
    low = min(open_price, close) - np.random.rand() * intraday_range
    rows.append({DATE: dates[i], OPEN: open_price, HIGH: high, LOW: low, CLOSE: close})
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
# One candle per row at x = 1..n; bullish and bearish candles go to separate series (None = line break)
candles = df.reset_index(drop=True)
n_candles = len(candles)
bull_wicks, bear_wicks = [], []
bull_bodies, bear_bodies = [], []
for i, candle in candles.iterrows():
    x = i + 1
    wick = [(x, candle[LOW]), (x, candle[HIGH]), None]
    body = [(x, candle[OPEN]), (x, candle[CLOSE]), None]
    if candle[CLOSE] >= candle[OPEN]:
        bull_wicks.extend(wick)
        bull_bodies.extend(body)
    else:
        bear_wicks.extend(wick)
        bear_bodies.extend(body)

date_map = {i + 1: d for i, d in enumerate(candles[DATE])}
tick_positions = [1, *range(5, n_candles + 1, 5)]

# --- Style: Imprint palette + theme-adaptive chrome ---
# Series order: bull wicks, bear wicks, bull bodies, bear bodies
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=(BULL, BEAR, BULL, BEAR),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
)

# --- Chart: 3200×1800 landscape canvas ---
WICK_W, BODY_W = 13, 51

chart = pygal.XY(
    style=custom_style,
    width=3200,
    height=1800,
    title="candlestick-basic · python · pygal · anyplot.ai",
    x_title=DATE,
    y_title="Price ($)",
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    allow_interruptions=True,
    range=(candles[LOW].min() - 2, candles[HIGH].max() + 3),
    xrange=(0, n_candles + 1),
    legend_box_size=22,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    margin=36,
    spacing=20,
    tooltip_border_radius=8,
    truncate_legend=-1,
    value_formatter=lambda x: f"${x:.2f}",
)

chart.x_labels = tick_positions
chart.x_value_formatter = lambda x: date_map[int(round(x))].strftime("%b %d") if int(round(x)) in date_map else ""

# Series 0: bull wicks (hidden from legend)
chart.add(None, bull_wicks, stroke=True, show_dots=False, stroke_style={"width": WICK_W, "linecap": "butt"})
# Series 1: bear wicks (hidden from legend)
chart.add(None, bear_wicks, stroke=True, show_dots=False, stroke_style={"width": WICK_W, "linecap": "butt"})
# Series 2: bullish candle bodies
chart.add("Bullish (Up)", bull_bodies, stroke=True, show_dots=False, stroke_style={"width": BODY_W, "linecap": "butt"})
# Series 3: bearish candle bodies
chart.add(
    "Bearish (Down)", bear_bodies, stroke=True, show_dots=False, stroke_style={"width": BODY_W, "linecap": "butt"}
)

# --- Render: SVG post-processing for cairosvg and visual refinement ---
# cairosvg ignores CSS class-based stroke properties; inline them directly on each series group
svg = chart.render(is_unicode=True)

# 1. Inline stroke widths for cairosvg compatibility
series_strokes = {0: (WICK_W, "butt"), 1: (WICK_W, "butt"), 2: (BODY_W, "butt"), 3: (BODY_W, "butt")}
for sid, (width, cap) in series_strokes.items():
    style_attr = f' style="stroke-width:{width};stroke-linecap:{cap}"'
    svg = re.sub(
        rf'(class="series serie-{sid} color-{sid}"[^>]*>.*?</g>)',
        lambda m, s=style_attr: m.group(0).replace('class="line reactive nofill"', 'class="line reactive nofill"' + s),
        svg,
        count=1,
        flags=re.DOTALL,
    )

# 2. Grid lines: override dashed default with solid lines
svg = re.sub(r"stroke-dasharray\s*:\s*[\d.,\s]+", "stroke-dasharray:none", svg)

# 3. L-spine border: replace full-frame rect with left + bottom lines only
m = re.search(r'<g\b[^>]*class="plot"[^>]*>\s*(<rect\b[^>]*/?>)', svg)
if m:
    rect_tag = m.group(1)
    rx = re.search(r'\bx="([^"]+)"', rect_tag)
    ry = re.search(r'\by="([^"]+)"', rect_tag)
    rw = re.search(r'\bwidth="([^"]+)"', rect_tag)
    rh = re.search(r'\bheight="([^"]+)"', rect_tag)
    if rx and ry and rw and rh:
        x, y, w, h = float(rx.group(1)), float(ry.group(1)), float(rw.group(1)), float(rh.group(1))
        no_stroke = re.sub(r'\s*\bstroke="[^"]*"', "", rect_tag).replace("<rect", '<rect stroke="none"', 1)
        l_spine = (
            f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y + h:.1f}" '
            f'stroke="{INK_MUTED}" stroke-width="1.5"/>'
            f'<line x1="{x:.1f}" y1="{y + h:.1f}" x2="{x + w:.1f}" y2="{y + h:.1f}" '
            f'stroke="{INK_MUTED}" stroke-width="1.5"/>'
        )
        svg = svg.replace(rect_tag, no_stroke + l_spine, 1)

cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "w") as f:
    f.write(chart.render(is_unicode=True))
