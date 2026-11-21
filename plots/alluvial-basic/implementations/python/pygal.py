"""anyplot.ai
alluvial-basic: Basic Alluvial Diagram
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import cairosvg
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
STAGE = "Quarter"  # role: time_point
TIER = "Subscription tier"  # role: category
NEXT_STAGE = "Next quarter"  # role: extra
NEXT_TIER = "Next-quarter tier"  # role: extra
VALUE = "Customers (hundreds)"  # role: value
FLOW = "Customers moving (hundreds)"  # role: flow

# Data: replace this block with your own edge list, one row per band between neighboring columns
tiers = ["Free", "Basic", "Pro", "Churned"]
quarters = ["Q1", "Q2", "Q3", "Q4"]
transitions = [
    [[376, 68, 12, 24], [21, 234, 29, 16], [3, 8, 149, 10], [0, 0, 0, 50]],
    [[307, 64, 11, 18], [20, 246, 31, 13], [3, 10, 168, 9], [0, 0, 0, 100]],
    [[249, 59, 10, 12], [18, 260, 32, 10], [3, 11, 188, 8], [0, 0, 0, 140]],
]
df = pd.DataFrame(
    [
        {STAGE: quarters[t], TIER: tiers[i], NEXT_STAGE: quarters[t + 1], NEXT_TIER: tiers[j], FLOW: matrix[i][j]}
        for t, matrix in enumerate(transitions)
        for i in range(len(tiers))
        for j in range(len(tiers))
        if matrix[i][j] > 0
    ]
)
df[VALUE] = df.groupby([STAGE, TIER])[FLOW].transform("sum")

# Plot: reads only df and the constants above
stages = list(dict.fromkeys(df[STAGE])) + [df[NEXT_STAGE].iloc[-1]]
categories = list(dict.fromkeys(list(df[TIER]) + list(df[NEXT_TIER])))
tier_color = {c: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, c in enumerate(categories)}

# Block size per column: outgoing flow, and incoming flow for the last column
outgoing = df.groupby([STAGE, TIER], sort=False)[FLOW].sum()
incoming = df.groupby([NEXT_STAGE, NEXT_TIER], sort=False)[FLOW].sum()
size = {(s, c): float(outgoing.get((s, c), 0.0)) for s in stages[:-1] for c in categories}
size.update({(stages[-1], c): float(incoming.get((stages[-1], c), 0.0)) for c in categories})

W, H = 3200, 1800
title = "alluvial-basic · python · pygal · anyplot.ai"
style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
)

# pygal draws the canvas and the title; the alluvial geometry is injected as SVG
chart = pygal.XY(
    width=W,
    height=H,
    style=style,
    title=title,
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    dots_size=0,
    stroke=False,
)
chart.add("", [(0, 0)])
base_svg = chart.render().decode("utf-8")

# Geometry: one scale for the whole diagram, so a band is as thick at both ends as its flow
margin_x = 330
top, bottom = 220, 1560
block_w = 230
gap = 36
x_pos = [margin_x + i * (W - 2 * margin_x) / (len(stages) - 1) for i in range(len(stages))]
col_total = {s: sum(size[(s, c)] for c in categories) for s in stages}
scale = min((bottom - top - gap * (len(categories) - 1)) / col_total[s] for s in stages if col_total[s] > 0)

nodes = {}
for s in stages:
    y = top
    for c in categories:
        h = size[(s, c)] * scale
        nodes[(s, c)] = (y, y + h)
        y += h + gap


def label_ink(hex_color):
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return "#1A1A17" if 0.299 * r + 0.587 * g + 0.114 * b > 150 else "#FFFFFF"


parts = []

# Bands: stacked on each block in the order of the opposite end, colored by source
for s, nxt in zip(stages[:-1], stages[1:], strict=True):
    edges = df[df[STAGE] == s]
    src_cursor = {c: nodes[(s, c)][0] for c in categories}
    dst_cursor = {c: nodes[(nxt, c)][0] for c in categories}
    x0 = x_pos[stages.index(s)] + block_w / 2
    x1 = x_pos[stages.index(nxt)] - block_w / 2
    cx0 = x0 + 0.4 * (x1 - x0)
    cx1 = x0 + 0.6 * (x1 - x0)
    for src in categories:
        for dst in categories:
            row = edges[(edges[TIER] == src) & (edges[NEXT_TIER] == dst)]
            if row.empty:
                continue
            band = float(row[FLOW].iloc[0]) * scale
            ya, yb = src_cursor[src], dst_cursor[dst]
            src_cursor[src] += band
            dst_cursor[dst] += band
            path = (
                f"M {x0:.1f},{ya:.1f} C {cx0:.1f},{ya:.1f} {cx1:.1f},{yb:.1f} {x1:.1f},{yb:.1f} "
                f"L {x1:.1f},{yb + band:.1f} C {cx1:.1f},{yb + band:.1f} {cx0:.1f},{ya + band:.1f} {x0:.1f},{ya + band:.1f} Z"
            )
            parts.append(f'<path d="{path}" fill="{tier_color[src]}" fill-opacity="0.38" stroke="none"/>')

# Blocks with category labels in every column, and a header per time point
for s in stages:
    x = x_pos[stages.index(s)]
    for c in categories:
        y0, y1 = nodes[(s, c)]
        parts.append(
            f'<rect x="{x - block_w / 2:.1f}" y="{y0:.1f}" width="{block_w}" height="{y1 - y0:.1f}" '
            f'fill="{tier_color[c]}" stroke="{PAGE_BG}" stroke-width="3"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{(y0 + y1) / 2:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="40" font-weight="bold" font-family="sans-serif" fill="{label_ink(tier_color[c])}">{c}</text>'
        )
    parts.append(
        f'<text x="{x:.1f}" y="{bottom + 90}" text-anchor="middle" font-size="56" font-weight="bold" '
        f'font-family="sans-serif" fill="{INK}">{s}</text>'
    )

parts.append(
    f'<text x="{W / 2}" y="{bottom + 180}" text-anchor="middle" font-size="44" font-family="sans-serif" '
    f'fill="{INK_SOFT}">{VALUE} by {TIER.lower()}, band width = {FLOW.lower()}</text>'
)

svg = base_svg.replace("</svg>", "<g>" + "".join(parts) + "</g></svg>")

# Output
with open(f"plot-{THEME}.svg", "w", encoding="utf-8") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title>'
        f"<style>body{{margin:0;background:{PAGE_BG}}}svg{{width:100%;height:auto}}</style></head>"
        f"<body>{svg}</body></html>"
    )
