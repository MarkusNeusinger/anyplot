"""anyplot.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per tier in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
NODE = "Position"  # role: nodes
PARENT = "Reports to"  # role: edges
TIER = "Tier"  # role: level

# Data: replace this block with your own edge list, for example df = pd.read_csv("org.csv")
# (one row per node; the root has an empty parent)
df = pd.DataFrame(
    {
        NODE: [
            "CEO",
            "VP Engineering",
            "VP Sales",
            "VP Operations",
            "Dir Frontend",
            "Dir Backend",
            "Dir DevOps",
            "Dir Americas",
            "Dir EMEA",
            "Dir Logistics",
            "Dir HR",
            "Mgr React",
            "Mgr Vue",
            "Mgr API",
            "Mgr DB",
            "Mgr Cloud",
            "Mgr NA",
            "Mgr LATAM",
            "Mgr UK",
            "Mgr Germany",
            "Mgr Supply",
            "Mgr Talent",
        ],
        PARENT: [
            None,
            "CEO",
            "CEO",
            "CEO",
            "VP Engineering",
            "VP Engineering",
            "VP Engineering",
            "VP Sales",
            "VP Sales",
            "VP Operations",
            "VP Operations",
            "Dir Frontend",
            "Dir Frontend",
            "Dir Backend",
            "Dir Backend",
            "Dir DevOps",
            "Dir Americas",
            "Dir Americas",
            "Dir EMEA",
            "Dir EMEA",
            "Dir Logistics",
            "Dir HR",
        ],
        TIER: ["Executive"] + ["Vice presidents"] * 3 + ["Directors"] * 7 + ["Managers"] * 11,
    }
)

# Plot: tree layout derived from df only
children = {node: [] for node in df[NODE]}
root = None
for node, parent in zip(df[NODE], df[PARENT], strict=True):
    if pd.isna(parent):
        root = node
    else:
        children[parent].append(node)

depth = {root: 0}
x_pos = {}
next_leaf = [0]


def place(node, level):
    """Leaves take consecutive slots; a parent sits centered above its children."""
    depth[node] = level
    kids = children[node]
    if not kids:
        x_pos[node] = float(next_leaf[0])
        next_leaf[0] += 1
    else:
        for kid in kids:
            place(kid, level + 1)
        x_pos[node] = (x_pos[kids[0]] + x_pos[kids[-1]]) / 2


place(root, 0)
max_depth = max(depth.values())
pos = {node: (x_pos[node], max_depth - depth[node]) for node in df[NODE]}

style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(INK_MUTED, *IMPRINT_PALETTE),  # first series is the edge layer
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=36,
    legend_font_size=44,
    value_font_size=34,
    value_colors=(INK,) * 9,
    stroke_width=3,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=style,
    title="network-hierarchical · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=28,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    xrange=(-0.8, next_leaf[0] - 0.2),
    range=(-0.45, max_depth + 0.45),
    print_values=False,
    print_labels=True,
    explicit_size=True,
    # pygal fixes the point-label size at 10px; enlarge it and center it under its node
    css=(
        "file://style.css",
        "file://graph.css",
        "inline:.text-overlay text.label{font-size:30px !important;text-anchor:middle !important;font-style:normal}",
    ),
    truncate_legend=-1,
    margin=60,
    margin_top=40,
)

# Reporting lines: one continuous walk down and back up the tree, so every
# parent-child pair is traced and no stray segment joins unrelated nodes
walk = [pos[root]]


def trace(node):
    for kid in children[node]:
        walk.extend([pos[kid]])
        trace(kid)
        walk.append(pos[node])


trace(root)
chart.add("Reporting line", walk, show_dots=False, stroke=True, stroke_style={"width": 3})

# Nodes, one series per tier, each point labelled with its own name
for tier in df[TIER].unique():
    members = df.loc[df[TIER] == tier, NODE]
    chart.add(tier, [{"value": pos[node], "label": node} for node in members], stroke=False, dots_size=24)

chart.render_to_file(f"plot-{THEME}.svg")
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
