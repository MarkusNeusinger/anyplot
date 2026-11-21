"""anyplot.ai
icicle-basic: Basic Icicle Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_size_identity,
    theme,
    xlim,
    ylim,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per hierarchy level in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
NAME = "name"  # role: name
PARENT = "parent"  # role: parent
VALUE = "value"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("hierarchy.csv")
df = pd.DataFrame(
    [
        ("root", "", 1000),
        ("Documents", "root", 350),
        ("Media", "root", 400),
        ("Projects", "root", 250),
        ("Work", "Documents", 200),
        ("Personal", "Documents", 150),
        ("Photos", "Media", 220),
        ("Videos", "Media", 180),
        ("Python", "Projects", 120),
        ("Web", "Projects", 130),
        ("Reports", "Work", 120),
        ("Contracts", "Work", 80),
        ("Letters", "Personal", 90),
        ("Receipts", "Personal", 60),
        ("2024", "Photos", 130),
        ("2023", "Photos", 90),
        ("Movies", "Videos", 100),
        ("Clips", "Videos", 80),
        ("DataViz", "Python", 70),
        ("ML", "Python", 50),
        ("Frontend", "Web", 75),
        ("Backend", "Web", 55),
    ],
    columns=[NAME, PARENT, VALUE],
)

# Plot: reads only df and the constants above
parent_of = dict(zip(df[NAME], df[PARENT].fillna("")))
# A parent that names no row (or is empty) marks a root
parent_of = {node: (parent if parent in parent_of else "") for node, parent in parent_of.items()}
value_of = dict(zip(df[NAME], df[VALUE]))
children = {}
for node, parent in parent_of.items():
    if parent:
        children.setdefault(parent, []).append(node)

# Level of each node = number of ancestors
levels = {}
for node in parent_of:
    level, current = 0, node
    while parent_of[current]:
        level += 1
        current = parent_of[current]
    levels[node] = level
max_level = max(levels.values())

# Rectangle positions (root at the top, children directly below their parent)
roots = [node for node, parent in parent_of.items() if not parent]
rects = []
stack = [(root, 0.0, 1.0) for root in roots]
while stack:
    node, x_start, x_end = stack.pop()
    rects.append(
        {
            NAME: node,
            "xmin": x_start,
            "xmax": x_end,
            "ymin": max_level - levels[node],
            "ymax": max_level - levels[node] + 1,
            "level": levels[node],
        }
    )
    kids = children.get(node, [])
    total = sum(value_of[k] for k in kids)
    cursor = x_start
    for kid in kids:
        width = (x_end - x_start) * value_of[kid] / total
        stack.append((kid, cursor, cursor + width))
        cursor += width

rect_df = pd.DataFrame(rects)
rect_df["level_str"] = rect_df["level"].astype(str)
rect_df["x_center"] = (rect_df["xmin"] + rect_df["xmax"]) / 2
rect_df["y_center"] = (rect_df["ymin"] + rect_df["ymax"]) / 2

# Label only rectangles wide enough for their text
rect_df["width"] = rect_df["xmax"] - rect_df["xmin"]
rect_df["show_label"] = rect_df["width"] > (rect_df[NAME].str.len() * 0.007 + 0.01)
label_df = rect_df[rect_df["show_label"]].copy()

# Label size (mm) shrinks with depth
label_df["font_size"] = (7.0 - 1.0 * label_df["level"]).clip(lower=4.0)

level_colors = {str(i): IMPRINT_PALETTE[i] for i in range(max_level + 1)}

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(size=16, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_title=element_text(size=12, color=INK),
)

plot = (
    ggplot()
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="level_str"),
        data=rect_df,
        color=INK_SOFT,
        size=0.75,
        alpha=0.9,
    )
    + geom_text(aes(x="x_center", y="y_center", label=NAME, size="font_size"), data=label_df, color=INK)
    + scale_fill_manual(values=level_colors, name="Hierarchy Level")
    + scale_size_identity()
    + xlim(-0.02, 1.02)
    + ylim(-0.1, max_level + 1.1)
    + labs(title="icicle-basic · python · letsplot · anyplot.ai")
    + anyplot_theme
    + ggsize(800, 450)
)

# Save outputs
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
