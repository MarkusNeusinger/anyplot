"""anyplot.ai
point-and-figure-basic: Point and Figure Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-20
"""

import os as _os
import sys as _sys


# This file is named pygal.py — remove its directory from sys.path first so
# Python resolves `pygal` to the installed package, not this file itself.
_here = _os.path.abspath(_os.path.dirname(__file__))
_sys.path = [p for p in _sys.path if _os.path.abspath(p or ".") != _here]

import os
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")
X_COLOR = IMPRINT_PALETTE[0]  # rising, green
O_COLOR = IMPRINT_PALETTE[4]  # falling, red (semantic exception)

# Constants
RISE, FALL = "X", "O"  # column symbols
REVERSAL = 3  # boxes needed to start a new column
TREND_COLUMNS = 6  # columns each 45-degree trend line spans

DATE = "Date"  # role: date
HIGH = "High ($)"  # role: high
LOW = "Low ($)"  # role: low
CLOSE = "Close ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
rng = np.random.default_rng(2024)
n_days = 260
rally = 110
close_path = np.empty(n_days)
close_path[0] = 96.0
for day in range(1, n_days):
    if day < rally:
        # sharp advance with noise
        close_path[day] = close_path[day - 1] + 0.12 + rng.normal(0, 1.9)
    else:
        # consolidation: mean-reverting around the level reached
        close_path[day] = (
            close_path[day - 1] + 0.12 * (close_path[rally - 1] - close_path[day - 1]) + rng.normal(0, 2.0)
        )
df = pd.DataFrame(
    {
        DATE: pd.bdate_range("2025-01-02", periods=n_days),
        HIGH: close_path + np.abs(rng.normal(0, 0.8, n_days)),
        LOW: close_path - np.abs(rng.normal(0, 0.8, n_days)),
        CLOSE: close_path,
    }
)

# Plot
BOX_SIZE = float(f"{df[CLOSE].median() * 0.02:.1g}")  # price per box, 2% of the median close to one digit
# P&F algorithm: close prices snapped to boxes, reversal of REVERSAL boxes starts a new column
columns = []
direction = None
col_start = col_end = np.floor(df[CLOSE].iloc[0] / BOX_SIZE) * BOX_SIZE

for price in df[CLOSE].iloc[1:]:
    box = np.floor(price / BOX_SIZE) * BOX_SIZE
    if direction is None:
        if box >= col_end + BOX_SIZE:
            direction, col_end = RISE, box
        elif box <= col_end - BOX_SIZE:
            direction, col_end = FALL, box
    elif direction == RISE:
        if box >= col_end + BOX_SIZE:
            col_end = box
        elif box <= col_end - REVERSAL * BOX_SIZE:
            columns.append((col_start, col_end, RISE))
            col_start, col_end, direction = col_end - BOX_SIZE, box, FALL
    else:
        if box <= col_end - BOX_SIZE:
            col_end = box
        elif box >= col_end + REVERSAL * BOX_SIZE:
            columns.append((col_start, col_end, FALL))
            col_start, col_end, direction = col_end + BOX_SIZE, box, RISE
if direction:
    columns.append((col_start, col_end, direction))

levels = [p for start, end, _ in columns for p in (start, end)]
y_min = min(levels) - BOX_SIZE
y_max = max(levels) + BOX_SIZE
y_labels = list(np.arange(y_min, y_max + BOX_SIZE, BOX_SIZE))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=(X_COLOR, O_COLOR, IMPRINT_PALETTE[2], IMPRINT_PALETTE[3]),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="point-and-figure-basic · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    show_y_guides=True,
    show_x_guides=False,
    x_title="Column (Reversal)",
    y_title=CLOSE,
    margin=80,
    margin_bottom=200,
    margin_left=220,
    margin_top=120,
    margin_right=100,
    y_labels=y_labels,
    range=(y_min, y_max),
    dots_size=18,
)

x_points = []
o_points = []
for col_idx, (start, end, kind) in enumerate(columns):
    low, high = min(start, end), max(start, end)
    box_levels = np.arange(low, high + BOX_SIZE * 0.5, BOX_SIZE)
    target = x_points if kind == RISE else o_points
    target.extend((col_idx, float(lv)) for lv in box_levels)

chart.add("X (Rising)", x_points, stroke=False)
chart.add("O (Falling)", o_points, stroke=False)

# 45-degree trend lines: one box of price per column
support_lows = [(ci, min(s, e)) for ci, (s, e, k) in enumerate(columns) if k == FALL]
resistance_highs = [(ci, max(s, e)) for ci, (s, e, k) in enumerate(columns) if k == RISE]

if support_lows:
    c0, p0 = support_lows[0]
    c1 = min(c0 + TREND_COLUMNS, len(columns) - 1)
    chart.add(
        "Support (45°)",
        [(c0, p0), (c1, p0 + (c1 - c0) * BOX_SIZE)],
        stroke=True,
        dots_size=4,
        stroke_style={"width": 4, "dasharray": "8, 6"},
    )

if resistance_highs:
    c0, p0 = resistance_highs[0]
    c1 = min(c0 + TREND_COLUMNS, len(columns) - 1)
    chart.add(
        "Resistance (45°)",
        [(c0, p0), (c1, p0 - (c1 - c0) * BOX_SIZE)],
        stroke=True,
        dots_size=4,
        stroke_style={"width": 4, "dasharray": "8, 6"},
    )


def add_pnf_text_markers(svg_bytes, glyph_size):
    """Hide the circle markers of the X/O series and draw X and O glyphs in their place."""
    svg_ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", svg_ns)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

    root = ET.fromstring(svg_bytes)
    parent_map = {child: parent for parent in root.iter() for child in parent}
    series_symbols = {0: (RISE, X_COLOR), 1: (FALL, O_COLOR)}

    for serie_idx, (symbol, color) in series_symbols.items():
        for g in root.iter(f"{{{svg_ns}}}g"):
            parts = g.get("class", "").split()
            if "series" not in parts or f"serie-{serie_idx}" not in parts:
                continue
            for circle in g.iter(f"{{{svg_ns}}}circle"):
                cx, cy = circle.get("cx"), circle.get("cy")
                if cx is None or cy is None:
                    continue
                # circle stays in the DOM (invisible) so hover tooltips still work in the HTML
                circle.set("opacity", "0")
                text = ET.Element(f"{{{svg_ns}}}text")
                text.set("x", cx)
                text.set("y", cy)
                text.set("text-anchor", "middle")
                text.set("dominant-baseline", "central")
                text.set("font-size", str(glyph_size))
                text.set("font-weight", "bold")
                text.set("style", f"fill:{color};stroke:none")
                text.set("font-family", "monospace, sans-serif")
                text.text = symbol
                parent_map[circle].append(text)

    return ET.tostring(root, encoding="unicode").encode("utf-8")


# Glyph size follows the box height on the canvas (about 1250 px of plot height)
glyph_size = int(min(60, max(24, 1250 / len(y_labels) * 0.9)))
svg_modified = add_pnf_text_markers(chart.render(), glyph_size)

with open(f"plot-{THEME}.png", "wb") as f:
    cairosvg.svg2png(bytestring=svg_modified, write_to=f)

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(svg_modified)
