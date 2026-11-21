""" anyplot.ai
upset-basic: UpSet Plot for Multi-Set Intersection Analysis
Library: pygal 3.1.3 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os
import re
from collections import Counter

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
GRID = "#D9D6CA" if THEME == "light" else "#3A3A35"  # faint row bands and guides
EMPTY_DOT = "#CFCCBF" if THEME == "light" else "#46463F"  # non-member dots: present but muted

# Imprint palette: one color per intersection degree, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
TOP_N = 10  # the number of largest intersections shown as columns

# Columns: set these to your table's column names
SUBSCRIBER = "Subscriber"  # role: element
ADDON = "Add-on subscribed"  # role: sets

# Data: replace this block with your own table, for example df = pd.read_csv("memberships.csv")
# One row per (subscriber, add-on) membership; a subscriber with several add-ons has several rows.
np.random.seed(42)
n_subscribers = 1500
addon_names = ["Movies", "Series", "Live Sports", "Music", "Kids"]
addon_share = [0.42, 0.50, 0.20, 0.30, 0.17]
member = np.column_stack([np.random.rand(n_subscribers) < p for p in addon_share])
rows, cols = np.nonzero(member)
df = pd.DataFrame({SUBSCRIBER: [f"S{i:04d}" for i in rows], ADDON: [addon_names[j] for j in cols]})

# Plot: reads only df and the constants above
combos = df.groupby(SUBSCRIBER, sort=False)[ADDON].agg(frozenset)
top = Counter(combos).most_common(TOP_N)  # sorted by size, descending
set_size = df.groupby(ADDON).size().sort_values(ascending=False)
sets = list(set_size.index)  # matrix rows, largest set first
n_sets, n_int = len(sets), len(top)
degrees = sorted({len(c) for c, _ in top})

W, H = 3200, 1800
# Target plot areas (x, y, width, height): the three charts share these edges, so bars, rows and columns line up
col_w = 160
BAR_BOX = (1180, 290, col_w * n_int, 620)  # intersection bars
MAT_BOX = (BAR_BOX[0], 990, BAR_BOX[2], 120 * n_sets)  # dot matrix
SET_BOX = (520, MAT_BOX[1], 560, MAT_BOX[3])  # set-size bars


def style(colors, background="transparent", stroke_width=2.5, value_colors=(INK_SOFT,) * 8):
    return Style(
        stroke_width=stroke_width,
        background=background,
        colors=colors,
        plot_background="transparent",
        foreground=INK_SOFT,
        foreground_strong=INK,
        foreground_subtle=GRID,
        opacity="1",
        opacity_hover="1",
        title_font_size=60,
        label_font_size=44,
        major_label_font_size=44,
        legend_font_size=44,
        value_font_size=40,
        value_colors=value_colors,
        font_family="Arial, Helvetica, sans-serif",
    )


def plot_rect(svg):
    """Return (x, y, w, h) of the plot area inside a rendered pygal SVG."""
    m = re.search(
        r'<g transform="translate\(([\d.]+), ([\d.]+)\)" class="plot"><rect[^>]*width="([\d.]+)" height="([\d.]+)"', svg
    )
    return tuple(float(v) for v in m.groups())


def place(build, box):
    """Render a pygal chart so that its plot area lands exactly on `box` (x, y, w, h) of the canvas."""
    tx, ty, tw, th = box
    margins = {"margin_left": 0, "margin_top": 0, "margin_right": 0, "margin_bottom": 0}
    for _ in range(4):
        chart = build()
        chart.margin_left = margins["margin_left"]
        chart.margin_top = margins["margin_top"]
        chart.margin_right = margins["margin_right"]
        chart.margin_bottom = margins["margin_bottom"]
        svg = chart.render(is_unicode=True)
        px, py, pw, ph = plot_rect(svg)
        # Margins make up what the labels, title and legend leave over; repeat until the plot area sits on the box
        delta = {
            "margin_left": tx - px,
            "margin_top": ty - py,
            "margin_right": (px + pw) - (tx + tw),
            "margin_bottom": (py + ph) - (ty + th),
        }
        if max(abs(v) for v in delta.values()) < 1.5:
            break
        margins = {k: max(int(round(margins[k] + delta[k])), 0) for k in margins}
    return svg


# Intersection bars: one stacked series per degree gives the degree coloring and a native legend
def build_bars():
    chart = pygal.StackedBar(
        width=W,
        height=H,
        style=style(tuple(IMPRINT_PALETTE[d - 1] for d in degrees), background=PAGE_BG),
        title="Subscription Add-on Overlap · upset-basic · python · pygal · anyplot.ai",
        y_title="Intersection size",
        value_formatter=lambda v: str(int(v)) if v else "",
        show_x_labels=False,
        show_y_guides=True,
        show_x_guides=False,
        print_values=True,
        print_values_position="top",
        legend_at_bottom=False,
        legend_box_size=36,
        range=(0, None),
        min_scale=4,
        spacing=30,
    )
    chart.x_labels = [str(i) for i in range(n_int)]
    for d in degrees:
        counts = [n if len(c) == d else None for c, n in top]
        chart.add("1 add-on" if d == 1 else f"{d} add-ons", counts)
    return chart


# Dot matrix: an XY chart, one connected line per intersection plus a muted series for the empty dots
def build_matrix():
    chart = pygal.XY(
        width=W,
        height=H,
        style=style((EMPTY_DOT, *[IMPRINT_PALETTE[len(c) - 1] for c, _ in top]), stroke_width=22),
        show_legend=False,
        show_x_labels=False,
        show_y_labels=False,
        show_x_guides=False,
        show_y_guides=False,
        xrange=(0, n_int),
        range=(0, n_sets),
    )
    empty = [(i + 0.5, n_sets - r - 0.5) for i, (c, _) in enumerate(top) for r, s in enumerate(sets) if s not in c]
    chart.add("Not in set", empty, stroke=False, dots_size=24)
    for i, (c, _n) in enumerate(top):
        rows_in = sorted(sets.index(s) for s in c)
        pts = [(i + 0.5, n_sets - r - 0.5) for r in rows_in]
        chart.add(str(i), pts, stroke_style={"width": 22, "linecap": "round"}, dots_size=40)
    return chart


# Set-size bars: horizontal bars, one row per set, named on the left
def build_sets():
    chart = pygal.HorizontalBar(
        width=W,
        height=H,
        style=style((IMPRINT_PALETTE[0],), value_colors=(PAGE_BG,) * 8),
        show_legend=False,
        y_title="Set size",
        y_labels=list(range(0, int(set_size.max()) + 1, 200)),
        show_y_guides=True,
        show_x_guides=False,
        print_values=True,
        range=(0, None),
        min_scale=3,
        spacing=30,
    )
    chart.x_labels = sets[::-1]  # pygal draws the first category at the bottom
    chart.add("Set size", [int(set_size[s]) for s in sets[::-1]])
    return chart


def inner(svg):
    return svg[svg.index("<svg") :].replace("<svg ", '<svg x="0" y="0" width="100%" height="100%" ', 1)


svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
    + "".join(
        inner(place(b, box)) for b, box in [(build_bars, BAR_BOX), (build_sets, SET_BOX), (build_matrix, MAT_BOX)]
    )
    + "</svg>"
)

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>body{{margin:0;background:{PAGE_BG}}}</style></head><body>{svg}</body></html>"
    )
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=W, output_height=H)
