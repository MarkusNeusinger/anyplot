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
FROM_TIME = "From election"  # role: extra
TO_TIME = "To election"  # role: time_point
SOURCE = "Party before"  # role: extra
TARGET = "Party after"  # role: category
FLOW = "Voters (millions)"  # role: flow

# Data: replace this block with your own edge list, for example df = pd.read_csv("flows.csv")
# Voter migration between parties across four US elections: one row per band
_flows = {
    ("2012", "2016"): {
        "Democratic": [58.0, 4.5, 2.5, 0.9],
        "Republican": [3.0, 55.0, 1.5, 1.4],
        "Independent": [3.2, 2.8, 2.0, 0.5],
        "Other": [1.6, 0.7, 0.3, 0.4],
    },
    ("2016", "2020"): {
        "Democratic": [60.0, 2.5, 2.0, 1.3],
        "Republican": [3.5, 58.0, 1.0, 0.5],
        "Independent": [5.5, 1.5, 0.5, 0.3],
        "Other": [2.0, 1.5, 0.5, 0.5],
    },
    ("2020", "2024"): {
        "Democratic": [65.0, 10.0, 4.5, 1.8],
        "Republican": [5.5, 62.0, 1.2, 0.5],
        "Independent": [1.0, 3.0, 0.7, 0.5],
        "Other": [0.5, 2.0, 0.1, 0.7],
    },
}
_targets = ["Democratic", "Republican", "Independent", "Other"]
df = pd.DataFrame(
    [
        {FROM_TIME: t0, TO_TIME: t1, SOURCE: src, TARGET: tgt, FLOW: value}
        for (t0, t1), by_source in _flows.items()
        for src, values in by_source.items()
        for tgt, value in zip(_targets, values, strict=True)
    ]
)

# Plot: reads only df and the constants above
times = list(dict.fromkeys(list(df[FROM_TIME]) + list(df[TO_TIME])))
parties = list(dict.fromkeys(list(df[SOURCE]) + list(df[TARGET])))
party_color = {party: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, party in enumerate(parties)}
edges = df[df[FLOW] > 0]

# Canvas and layout in SVG pixels
WIDTH, HEIGHT = 3200, 1800
margin_x, top, bottom = 480, 330, 200
bar_w = 90
gap = 22
col_x = [margin_x + i * (WIDTH - 2 * margin_x) / (len(times) - 1) for i in range(len(times))]

# Block size per party and time point: the larger of what leaves and what arrives
size = {}
for i, t in enumerate(times):
    out_sum = edges[edges[FROM_TIME] == t].groupby(SOURCE)[FLOW].sum()
    in_sum = edges[edges[TO_TIME] == t].groupby(TARGET)[FLOW].sum()
    for party in parties:
        size[(i, party)] = max(out_sum.get(party, 0.0), in_sum.get(party, 0.0))

# One scale for the whole diagram, so a band's width carries its flow everywhere
avail = HEIGHT - top - bottom
scale = min((avail - gap * (len(parties) - 1)) / sum(size[(i, p)] for p in parties) for i in range(len(times)))

block = {}
for i in range(len(times)):
    y = top
    for party in parties:
        h = size[(i, party)] * scale
        block[(i, party)] = (y, h)
        y += h + gap

# pygal draws the canvas, background and title; the diagram is added as SVG on top
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
)
chart = pygal.XY(
    width=WIDTH,
    height=HEIGHT,
    style=custom_style,
    title="alluvial-basic · python · pygal · anyplot.ai",
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    dots_size=0,
    stroke=False,
    margin=0,
)
chart.add(parties[0], [(0, 0)])
base_svg = chart.render().decode("utf-8")

parts = ['<g id="alluvial-diagram" font-family="sans-serif">']

# Bands: stacked from the top of the source block and the target block
for i, t in enumerate(times[:-1]):
    out_pos = {p: block[(i, p)][0] for p in parties}
    in_pos = {p: block[(i + 1, p)][0] for p in parties}
    seg = edges[edges[FROM_TIME] == t]
    seg = seg.assign(_s=seg[SOURCE].map(parties.index), _t=seg[TARGET].map(parties.index)).sort_values(["_s", "_t"])
    xa, xb = col_x[i] + bar_w / 2, col_x[i + 1] - bar_w / 2
    c0, c1 = xa + 0.4 * (xb - xa), xa + 0.6 * (xb - xa)
    for _, row in seg.iterrows():
        h = row[FLOW] * scale
        ya, yb = out_pos[row[SOURCE]], in_pos[row[TARGET]]
        out_pos[row[SOURCE]] += h
        in_pos[row[TARGET]] += h
        path = (
            f"M {xa:.1f},{ya:.1f} C {c0:.1f},{ya:.1f} {c1:.1f},{yb:.1f} {xb:.1f},{yb:.1f} "
            f"L {xb:.1f},{yb + h:.1f} C {c1:.1f},{yb + h:.1f} {c0:.1f},{ya + h:.1f} {xa:.1f},{ya + h:.1f} Z"
        )
        parts.append(
            f'<path d="{path}" fill="{party_color[row[SOURCE]]}" fill-opacity="0.38" stroke="none">'
            f"<title>{t} {row[SOURCE]} → {times[i + 1]} {row[TARGET]}: {row[FLOW]:g} million</title></path>"
        )

# Blocks, party labels at every column, column headers
for i, t in enumerate(times):
    x = col_x[i]
    parts.append(
        f'<text x="{x:.1f}" y="{top - 60}" text-anchor="middle" font-size="58" font-weight="bold" fill="{INK}">{t}</text>'
    )
    for party in parties:
        y, h = block[(i, party)]
        parts.append(
            f'<rect x="{x - bar_w / 2:.1f}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{party_color[party]}">'
            f"<title>{t} {party}: {size[(i, party)]:.1f} million</title></rect>"
        )
        if i == 0:
            lx, anchor = x - bar_w / 2 - 24, "end"
        else:
            lx, anchor = x + bar_w / 2 + 24, "start"
        parts.append(
            f'<text x="{lx:.1f}" y="{y + h / 2:.1f}" text-anchor="{anchor}" dominant-baseline="middle" font-size="40" '
            f'font-weight="bold" fill="{INK}" stroke="{PAGE_BG}" stroke-width="10" stroke-linejoin="round" '
            f'paint-order="stroke">{party}</text>'
        )

parts.append(
    f'<text x="{WIDTH / 2:.0f}" y="{HEIGHT - 70}" text-anchor="middle" font-size="40" font-style="italic" '
    f'fill="{INK_SOFT}">Band width shows voters moving between parties ({FLOW.lower()})</text>'
)
parts.append("</g>")

svg = base_svg.replace("</svg>", "".join(parts) + "</svg>")

# Save
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.svg", "w", encoding="utf-8") as f:
    f.write(svg)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>alluvial-basic · python · pygal · anyplot.ai</title>'
        f"<style>body{{margin:0;background:{PAGE_BG}}}svg{{width:100%;height:auto;display:block}}</style></head>"
        f"<body>{svg}</body></html>"
    )
