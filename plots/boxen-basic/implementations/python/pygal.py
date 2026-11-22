""" anyplot.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: pygal 3.1.3 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import importlib
import os
import sys

import numpy as np
import pandas as pd


script_dir = sys.path[0]
sys.path.pop(0)
pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style
sys.path.insert(0, script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Tail fraction where each letter-value box ends, innermost (quartiles) first
LEVEL_TAILS = [0.25, 0.125, 0.0625, 0.03125]
LEVEL_NAMES = ["Quartiles (25-75%)", "Eighths (12.5-87.5%)", "Sixteenths (6.25-93.75%)", "Thirty-seconds (3.1-96.9%)"]
BOX_WIDTHS = [300, 230, 160, 90]  # stroke width in px, narrower for each deeper level

# Columns: set these to your table's column names
ENDPOINT = "Endpoint"  # role: category
RESPONSE = "Response Time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("responses.csv")
np.random.seed(42)
endpoint_params = [
    ("API-Auth", 2.0, 20, 200, 1000),
    ("API-Search", 1.5, 30, 300, 1200),
    ("API-Report", 2.5, 25, 250, 900),
    ("API-Download", 2.0, 35, 400, 1500),
]
df = pd.concat(
    [
        pd.DataFrame(
            {
                ENDPOINT: name,
                RESPONSE: np.concatenate(
                    [np.random.gamma(shape=shape, scale=scale, size=3500), np.random.uniform(lo, hi, size=200)]
                ),
            }
        )
        for name, shape, scale, lo, hi in endpoint_params
    ],
    ignore_index=True,
)

# Plot
endpoints = df[ENDPOINT].unique().tolist()
groups = [df.loc[df[ENDPOINT] == name, RESPONSE].dropna().to_numpy() for name in endpoints]
n_levels = len(LEVEL_TAILS)
deepest = LEVEL_TAILS[-1]

# Series order: deepest (narrowest) level first, so wider inner boxes sit on top at the seams
level_order = list(range(n_levels - 1, -1, -1))

# One pygal series per box segment (pygal XY cannot break a line); only the first of a level has a legend title
segments = []  # (level, title, [(x, y), (x, y)])
for level in level_order:
    tail = LEVEL_TAILS[level]
    inner_tail = LEVEL_TAILS[level - 1] if level > 0 else None
    first = True
    for x, values in enumerate(groups):
        lo, hi = np.quantile(values, [tail, 1 - tail])
        if inner_tail is None:
            spans = [(lo, hi)]
        else:
            inner_lo, inner_hi = np.quantile(values, [inner_tail, 1 - inner_tail])
            spans = [(lo, inner_lo), (inner_hi, hi)]
        for y0, y1 in spans:
            segments.append((level, LEVEL_NAMES[level] if first else None, [(x, float(y0)), (x, float(y1))]))
            first = False

series_colors = [IMPRINT_PALETTE[level] for level, _, _ in segments] + [INK] * len(groups) + [INK_MUTED]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(series_colors),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=48,
    legend_font_size=40,
    value_font_size=36,
    stroke_width=4,
)

chart = pygal.XY(
    title="boxen-basic · python · pygal · anyplot.ai",
    x_title=ENDPOINT,
    y_title=RESPONSE,
    width=3200,
    height=1800,
    style=custom_style,
    show_legend=True,
    legend_box_size=30,
    range=(0, float(df[RESPONSE].max()) * 1.04),
    xrange=(-0.6, len(endpoints) - 0.4),
    show_x_guides=False,
    show_y_guides=True,
    stroke=True,
    show_dots=False,
    dots_size=5,
    truncate_legend=-1,
    truncate_label=-1,
    x_labels=list(range(len(endpoints))),
    x_value_formatter=lambda v: (
        endpoints[int(round(v))] if abs(v - round(v)) < 1e-6 and 0 <= round(v) < len(endpoints) else ""
    ),
    css=[
        "file://style.css",
        "file://graph.css",
        "inline:.series .line { stroke-linecap: butt !important; stroke-width: inherit !important; stroke-opacity: 1 !important; }",
    ],
)

# Box segments: each level draws the slab between its edge and the next-inner edge on each side
for level, title, points in segments:
    chart.add(title, points, stroke_style={"width": BOX_WIDTHS[level], "linecap": "butt"})

# Median mark across the innermost box
half = 0.5 * BOX_WIDTHS[0] / (3200 * 0.86 / (len(endpoints) + 0.2))
for x, values in enumerate(groups):
    m = float(np.median(values))
    chart.add(
        "Median" if x == 0 else None, [(x - half, m), (x + half, m)], stroke_style={"width": 7, "linecap": "butt"}
    )

# Observations beyond the deepest letter value
outlier_points = []
for x, values in enumerate(groups):
    lo, hi = np.quantile(values, [deepest, 1 - deepest])
    outlier_points += [(x, float(v)) for v in values if v < lo or v > hi]
chart.add("Beyond deepest level", outlier_points, stroke=False, show_dots=True, dots_size=6)

chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
