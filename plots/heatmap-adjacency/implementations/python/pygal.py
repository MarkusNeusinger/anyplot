"""anyplot.ai
heatmap-adjacency: Network Adjacency Matrix Heatmap
Library: pygal 3.1.3 | Python 3.13
Quality: pending | Updated: 2026-11-16
"""

import os
import re

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
ABSENT = "#DEDBD4" if THEME == "light" else "#2E2E2A"

# Imprint palette (canonical order); imprint_seq runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEQ_LOW, SEQ_HIGH = IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]

# Columns: set these to your table's column names
SOURCE = "Source"  # role: source
TARGET = "Target"  # role: target
WEIGHT = "Collaboration strength"  # role: weight
DEPARTMENT = "Source department"  # role: extra

# Data: replace this block with your own edge list, for example df = pd.read_csv("edges.csv");
# list every undirected edge in both directions, nodes ordered by group
rng = np.random.default_rng(42)
nodes = [f"{'ABC'[g]}{k + 1}" for g in range(3) for k in range(8)]
group_of = np.repeat(np.arange(3), 8)
same_group = group_of[:, None] == group_of[None, :]
present = np.triu(rng.random(same_group.shape) < np.where(same_group, 0.78, 0.07), k=1)
weights = np.where(same_group, rng.uniform(0.55, 1.0, same_group.shape), rng.uniform(0.1, 0.45, same_group.shape))
src, dst = np.nonzero(present)
w_edge = np.round(weights[src, dst], 2)
rows, cols = np.r_[src, dst], np.r_[dst, src]
by_node = np.lexsort((cols, rows))
df = pd.DataFrame(
    {
        SOURCE: [nodes[i] for i in rows[by_node]],
        TARGET: [nodes[j] for j in cols[by_node]],
        WEIGHT: np.r_[w_edge, w_edge][by_node],
        DEPARTMENT: [f"Department {'ABC'[group_of[i]]}" for i in rows[by_node]],
    }
)

# Plot
SIZE = 2400
# node order = order of first appearance as a source, then any target-only nodes
order = list(dict.fromkeys([*df[SOURCE], *df[TARGET]]))
n = len(order)
matrix = df.pivot_table(index=SOURCE, columns=TARGET, values=WEIGHT, aggfunc="max", sort=False).reindex(
    index=order, columns=order
)
# a boundary wherever the source department changes along the node order
dept_of = df.drop_duplicates(SOURCE).set_index(SOURCE)[DEPARTMENT].reindex(order)
boundaries = [i for i in range(1, n) if dept_of.iloc[i] != dept_of.iloc[i - 1]]
w_max = float(df[WEIGHT].max())
w_min = float(df[WEIGHT].min())


def lerp_hex(c0, c1, t):
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b, strict=True))


def cell_color(w):
    if not w > 0:
        return ABSENT
    return lerp_hex(SEQ_LOW, SEQ_HIGH, (w - w_min) / (w_max - w_min))


style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=58,
    label_font_size=38,
    major_label_font_size=38,
    legend_font_size=36,
    value_font_size=30,
    tooltip_font_size=30,
    stroke_width=0,
    opacity=1,
    opacity_hover=0.85,
)

chart = pygal.StackedBar(
    width=SIZE,
    height=SIZE,
    style=style,
    title="heatmap-adjacency · python · pygal · anyplot.ai",
    show_legend=False,
    show_y_guides=False,
    show_x_guides=False,
    x_label_rotation=0,
    margin_top=40,
    margin_bottom=40,
    margin_left=40,
    margin_right=330,
    spacing=0,
    print_values=False,
    range=(0, n),
    include_x_axis=True,
    truncate_label=-1,
)
chart.x_labels = order
# one label per row, centred on that row's band; the top row is the last stacked series
chart.y_labels = [{"label": node, "value": i + 0.5} for i, node in enumerate(reversed(order))]
chart.value_formatter = lambda v: f"{v:g}"
for node in reversed(order):
    chart.add(
        node,
        [
            {
                "value": 1,
                "color": cell_color(w),
                "label": f"{node} ↔ {col}: {w:.2f}" if w > 0 else f"{node} ↔ {col}: none",
            }
            for col, w in matrix.loc[node].items()
        ],
    )

svg = chart.render().decode()

# Locate the plot area pygal laid out, to attach colorbar and group boundaries to it
plot_tag = re.search(
    r'<g transform="translate\(([\d.]+), ([\d.]+)\)" class="plot">\s*<rect x="0" y="0" width="([\d.]+)" height="([\d.]+)"',
    svg,
)
left, top, _, _ = (float(v) for v in plot_tag.groups())
# bounds of the drawn cells (pygal pads the plot area around the bars), cell pitch from neighbouring bars
cells = np.array(
    [
        [float(v) for v in m]
        for m in re.findall(
            r'<rect x="([\d.]+)" y="([\d.]+)" rx="0" ry="0" width="([\d.]+)" height="([\d.]+)" class="rect reactive',
            svg,
        )
    ]
)
pitch_x = np.diff(np.unique(cells[:, 0].round(3))).min()
pw = pitch_x * n
left += cells[:, 0].min() - (pitch_x - cells[0, 2]) / 2
ph = float((cells[:, 1] + cells[:, 3]).max() - cells[:, 1].min())
top += cells[:, 1].min()

extras = []
for b in boundaries:
    gx = left + pw * b / n
    gy = top + ph * b / n
    extras.append(
        f'<line x1="{gx:.1f}" y1="{top:.1f}" x2="{gx:.1f}" y2="{top + ph:.1f}" stroke="{INK}" stroke-width="4" opacity="0.55"/>'
    )
    extras.append(
        f'<line x1="{left:.1f}" y1="{gy:.1f}" x2="{left + pw:.1f}" y2="{gy:.1f}" stroke="{INK}" stroke-width="4" opacity="0.55"/>'
    )

# Colorbar: absent edges as their own swatch, then the weight gradient
cb_x, cb_w = left + pw + 45, 50
cb_h = ph * 0.7
cb_y = top + 60
steps = 120
extras.append(
    f'<text x="{cb_x}" y="{top + 10:.1f}" font-family="sans-serif" font-size="38" fill="{INK}">{WEIGHT.split()[-1].capitalize()}</text>'
)
for k in range(steps):
    t = 1 - k / (steps - 1)
    extras.append(
        f'<rect x="{cb_x}" y="{cb_y + cb_h * k / steps:.1f}" width="{cb_w}" height="{cb_h / steps + 1:.1f}"'
        f' fill="{lerp_hex(SEQ_LOW, SEQ_HIGH, t)}"/>'
    )
extras.append(
    f'<rect x="{cb_x}" y="{cb_y}" width="{cb_w}" height="{cb_h:.1f}" fill="none" stroke="{INK_SOFT}" stroke-width="2" opacity="0.5"/>'
)
for frac in (0, 0.25, 0.5, 0.75, 1):
    value = w_max - frac * (w_max - w_min)
    ty = cb_y + frac * cb_h
    extras.append(
        f'<line x1="{cb_x + cb_w}" y1="{ty:.1f}" x2="{cb_x + cb_w + 12}" y2="{ty:.1f}" stroke="{INK_SOFT}" stroke-width="3"/>'
    )
    extras.append(
        f'<text x="{cb_x + cb_w + 20}" y="{ty + 13:.1f}" font-family="sans-serif" font-size="34" fill="{INK_SOFT}">{value:.2f}</text>'
    )
abs_y = cb_y + cb_h + 60
extras.append(
    f'<rect x="{cb_x}" y="{abs_y:.1f}" width="{cb_w}" height="{cb_w}" fill="{ABSENT}" stroke="{INK_SOFT}" stroke-width="2" opacity="1"/>'
)
extras.append(
    f'<text x="{cb_x + cb_w + 20}" y="{abs_y + 37:.1f}" font-family="sans-serif" font-size="34" fill="{INK_SOFT}">none</text>'
)

svg = svg.replace("</svg>", "".join(extras) + "</svg>")

# Save
import cairosvg  # noqa: E402  (pygal's PNG backend)


cairosvg.svg2png(bytestring=svg.encode(), write_to=f"plot-{THEME}.png", output_width=SIZE, output_height=SIZE)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>body{{margin:0;background:{PAGE_BG}}}</style></head><body>{svg}</body></html>'
    )
