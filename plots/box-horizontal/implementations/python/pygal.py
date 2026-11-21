"""anyplot.ai
box-horizontal: Horizontal Box Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
JOB_TITLE = "Job title"  # role: categories
SALARY = "Salary (USD)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("salaries.csv")
rng = np.random.default_rng(42)
groups = {
    "Software Engineer": (125000, 20000),
    "Data Scientist": (130000, 22000),
    "Product Manager": (140000, 25000),
    "Designer": (105000, 18000),
    "DevOps Engineer": (135000, 21000),
}
df = pd.DataFrame(
    {
        JOB_TITLE: [name for name in groups for _ in range(100)],
        SALARY: np.concatenate([rng.normal(mean, sd, 100) for mean, sd in groups.values()]),
    }
)

# Plot: reads only df and the constants above
table = {str(name): sub[SALARY].dropna().tolist() for name, sub in df.groupby(JOB_TITLE, sort=False)}

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=4,
)


# pygal has no native horizontal box chart: horizontal layout + box series. The horizontal
# mixin transposes pygal's lines but not its rect and circle nodes, so they are swapped here.
def draw_box_horizontal(self, parent_node, quartiles, outliers, box_index, metadata):
    center = pygal.graph.box.Box._draw_box(self, parent_node, quartiles, outliers, box_index, metadata)
    for node in parent_node:
        if node.tag == "rect":
            x, y = float(node.get("x")), float(node.get("y"))
            w, h = float(node.get("width")), float(node.get("height"))
            node.set("x", str(min(y, y + h)))
            node.set("y", str(x))
            node.set("width", str(abs(h)))
            node.set("height", str(w))
        elif node.tag == "circle":
            cx, cy = node.get("cx"), node.get("cy")
            node.set("cx", cy)
            node.set("cy", cx)
    return center


HorizontalBox = type(
    "HorizontalBox", (pygal.graph.horizontal.HorizontalGraph, pygal.graph.box.Box), {"_draw_box": draw_box_horizontal}
)

chart = HorizontalBox(
    width=3200,
    height=1800,
    style=custom_style,
    title="box-horizontal · python · pygal · anyplot.ai",
    x_title=SALARY,
    show_legend=True,
    legend_at_bottom=True,
    show_y_guides=True,
    show_x_guides=False,
    box_mode="tukey",
    value_formatter=lambda v: f"{v / 1000:.0f}k",
)
lo = np.floor(df[SALARY].min() / 20000) * 20000
hi = np.ceil(df[SALARY].max() / 20000) * 20000
ticks = [int(t) for t in np.arange(lo, hi + 1, 20000)]
chart.range = (lo, hi)
chart.zero = lo  # the box chart otherwise stretches the value axis down to zero
chart.y_labels = ticks
chart.y_labels_major = ticks
chart.x_labels = list(table)
for name, values in table.items():
    chart.add(name, values)

# Output
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
