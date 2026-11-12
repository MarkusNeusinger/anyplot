"""anyplot.ai
hive-basic: Basic Hive Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-07
"""

import math
import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per axis group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your tables' column names
MODULE = "Module"  # role: nodes
GROUP = "Module type"  # role: axis_attribute
DEGREE = "Degree (dependencies)"  # role: extra
SOURCE = "Source module"  # role: edges
TARGET = "Target module"  # role: extra

# Data: replace this block with your own tables, for example df = pd.read_csv("edges.csv")
# Software module dependency network: nodes sit on one axis per module type
nodes = pd.DataFrame(
    [
        ("kernel", "Core", 8),
        ("config", "Core", 6),
        ("database", "Core", 7),
        ("auth", "Core", 5),
        ("cache", "Core", 4),
        ("logger", "Core", 6),
        ("events", "Core", 5),
        ("helpers", "Utility", 5),
        ("validators", "Utility", 4),
        ("formatters", "Utility", 3),
        ("parsers", "Utility", 4),
        ("converters", "Utility", 3),
        ("crypto", "Utility", 4),
        ("compress", "Utility", 2),
        ("rest_api", "Interface", 6),
        ("graphql", "Interface", 5),
        ("websocket", "Interface", 4),
        ("cli", "Interface", 3),
        ("admin_ui", "Interface", 4),
        ("public_ui", "Interface", 5),
    ],
    columns=[MODULE, GROUP, DEGREE],
)
df = pd.DataFrame(
    [
        ("kernel", "config"),
        ("kernel", "database"),
        ("kernel", "auth"),
        ("config", "cache"),
        ("config", "logger"),
        ("database", "cache"),
        ("database", "logger"),
        ("auth", "events"),
        ("kernel", "helpers"),
        ("config", "validators"),
        ("database", "parsers"),
        ("auth", "crypto"),
        ("cache", "formatters"),
        ("logger", "formatters"),
        ("events", "helpers"),
        ("kernel", "rest_api"),
        ("kernel", "graphql"),
        ("database", "rest_api"),
        ("database", "graphql"),
        ("auth", "rest_api"),
        ("auth", "websocket"),
        ("logger", "cli"),
        ("helpers", "validators"),
        ("validators", "parsers"),
        ("formatters", "converters"),
        ("parsers", "converters"),
        ("crypto", "compress"),
        ("helpers", "rest_api"),
        ("helpers", "public_ui"),
        ("validators", "rest_api"),
        ("validators", "graphql"),
        ("formatters", "cli"),
        ("parsers", "graphql"),
        ("crypto", "websocket"),
        ("rest_api", "admin_ui"),
        ("rest_api", "public_ui"),
        ("graphql", "public_ui"),
        ("websocket", "admin_ui"),
    ],
    columns=[SOURCE, TARGET],
)

# Plot: reads only df, nodes and the constants above
groups = nodes[GROUP].unique().tolist()
n_axes = len(groups)
axis_angles = [2 * math.pi * i / n_axes - math.pi / 2 for i in range(n_axes)]
center = 5.0
inner_radius = 1.2
outer_radius = 4.0

# Position along each axis follows degree: highest degree nearest the center
ranked = nodes.sort_values(DEGREE, ascending=False, kind="stable")
rank = ranked.groupby(GROUP, sort=False).cumcount()
span = ranked.groupby(GROUP, sort=False)[MODULE].transform("size").clip(lower=2) - 1
ranked = ranked.assign(radius=inner_radius + rank / span * (outer_radius - inner_radius))
angle_of = dict(zip(groups, axis_angles, strict=False))
positions = {
    name: (center + radius * math.cos(angle_of[group]), center + radius * math.sin(angle_of[group]))
    for name, group, radius in zip(ranked[MODULE], ranked[GROUP], ranked["radius"], strict=False)
}
group_of = dict(zip(nodes[MODULE], nodes[GROUP], strict=False))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(
        [INK_SOFT] * n_axes
        + [IMPRINT_PALETTE[i] + "55" for i in range(n_axes)]
        + [IMPRINT_PALETTE[i] for i in range(n_axes)]
        + [IMPRINT_PALETTE[i] for i in range(n_axes)]
    ),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=40,
    value_label_font_size=34,
    value_colors=tuple([INK] * (4 * n_axes)),
    stroke_width=3,
)

chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title="hive-basic · python · pygal · anyplot.ai",
    x_title=f"Distance from center = {DEGREE.split(' (')[0].lower()}, highest nearest",
    show_legend=True,
    legend_at_bottom=True,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    stroke=True,
    dots_size=14,
    range=(0.1, 7.9),
    xrange=(0, 10),
    print_labels=True,
    print_values=False,
)

# Straight radial axes from a common center
for angle in axis_angles:
    chart.add(
        None,
        [
            (center + (inner_radius - 0.3) * math.cos(angle), center + (inner_radius - 0.3) * math.sin(angle)),
            (center + (outer_radius + 0.3) * math.cos(angle), center + (outer_radius + 0.3) * math.sin(angle)),
        ],
        show_dots=False,
        fill=False,
        stroke_style={"width": 6, "linecap": "round"},
    )

# Edges as Bezier curves pulled toward the center, grouped by source axis
edge_points = {group: [] for group in groups}
for src, tgt in zip(df[SOURCE], df[TARGET], strict=False):
    src_x, src_y = positions[src]
    tgt_x, tgt_y = positions[tgt]
    pull = 0.75 if group_of[src] == group_of[tgt] else 0.35
    ctrl_x = center + pull * ((src_x + tgt_x) / 2 - center)
    ctrl_y = center + pull * ((src_y + tgt_y) / 2 - center)
    for step in range(26):
        t = step / 25
        edge_points[group_of[src]].append(
            (
                (1 - t) ** 2 * src_x + 2 * (1 - t) * t * ctrl_x + t**2 * tgt_x,
                (1 - t) ** 2 * src_y + 2 * (1 - t) * t * ctrl_y + t**2 * tgt_y,
            )
        )
    edge_points[group_of[src]].append(None)

for group in groups:
    chart.add(None, edge_points[group], show_dots=False, fill=False, stroke_style={"width": 2, "linecap": "round"})

# Nodes per axis, labelled with the first four letters of the module name
for group in groups:
    members = nodes.loc[nodes[GROUP] == group, MODULE]
    chart.add(group, [{"value": positions[name], "label": name[:4].upper()} for name in members], stroke=False)

# Axis names at the outer end of each axis, in the axis color
label_radius = outer_radius + 0.8
for group, angle in zip(groups, axis_angles, strict=False):
    chart.add(
        None,
        [{"value": (center + label_radius * math.cos(angle), center + label_radius * math.sin(angle)), "label": group}],
        stroke=False,
        dots_size=1,
    )

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
