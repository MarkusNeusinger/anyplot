"""pyplots.ai
arc-basic: Basic Arc Diagram
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 85/100 | Updated: 2026-02-23
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem
from bokeh.plotting import figure


# Data - Character interactions in a story chapter
nodes = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry"]
edges = [
    (0, 1, 3),  # Alice-Bob: frequent
    (0, 2, 2),  # Alice-Carol: moderate
    (1, 3, 1),  # Bob-David: brief
    (2, 4, 2),  # Carol-Eve: moderate
    (0, 5, 1),  # Alice-Frank: brief
    (3, 6, 2),  # David-Grace: moderate
    (4, 7, 1),  # Eve-Henry: brief
    (0, 7, 3),  # Alice-Henry: frequent (long-range)
    (1, 4, 2),  # Bob-Eve: moderate
    (2, 6, 1),  # Carol-Grace: brief
    (5, 7, 2),  # Frank-Henry: moderate
    (1, 2, 1),  # Bob-Carol: brief (short-range)
]

# Node positions along horizontal axis
n_nodes = len(nodes)
x_positions = np.linspace(0.5, 10.5, n_nodes)
y_baseline = 0

# Compute weighted degree per node for data storytelling (hub visibility)
weighted_degrees = np.zeros(n_nodes)
for src, tgt, w in edges:
    weighted_degrees[src] += w
    weighted_degrees[tgt] += w

# Node sizes scaled by weighted degree — hub characters appear larger
min_wd, max_wd = weighted_degrees.min(), weighted_degrees.max()
node_sizes = 28 + (weighted_degrees - min_wd) / (max_wd - min_wd) * 28

# Node colors: darker fill for higher connectivity
light_rgb = np.array([0x93, 0xB5, 0xCF])
dark_rgb = np.array([0x1A, 0x3F, 0x5C])
node_colors = []
for wd in weighted_degrees:
    t = (wd - min_wd) / (max_wd - min_wd)
    rgb = (light_rgb + t * (dark_rgb - light_rgb)).astype(int)
    node_colors.append(f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")

# Weight-based styling: darker and thicker for stronger connections
weight_colors = {1: "#93B5CF", 2: "#306998", 3: "#1A3F5C"}
weight_labels = {1: "Brief", 2: "Moderate", 3: "Frequent"}

# Create figure with tighter vertical framing
p = figure(
    width=4800,
    height=2700,
    title="arc-basic \u00b7 bokeh \u00b7 pyplots.ai",
    x_range=(-0.2, 11.2),
    y_range=(-0.65, 3.15),
    toolbar_location=None,
)

# Style — subtle background tint complements blue palette
p.background_fill_color = "#F7F9FB"
p.border_fill_color = "#F7F9FB"
p.title.text_font_size = "32pt"
p.title.text_color = "#1A3F5C"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Subtitle providing narrative context
subtitle = Label(
    x=-0.1,
    y=2.95,
    text="Character Interaction Frequency in Chapter 1",
    text_font_size="22pt",
    text_font_style="italic",
    text_color="#666666",
    text_align="left",
)
p.add_layout(subtitle)

# Draw arcs using Bokeh's native bezier glyph
arc_renderers_by_weight = {1: [], 2: [], 3: []}

for src_idx, tgt_idx, weight in edges:
    x_src = x_positions[src_idx]
    x_tgt = x_positions[tgt_idx]

    distance = abs(x_tgt - x_src)
    arc_height = distance * 0.35

    # Control points at 1/3 and 2/3 for smooth, rounded arcs
    cx0 = x_src + (x_tgt - x_src) / 3
    cx1 = x_src + 2 * (x_tgt - x_src) / 3
    cy = arc_height

    line_width = 1.0 + weight * 2.5
    color = weight_colors[weight]
    alpha = 0.45 + weight * 0.13

    arc_source = ColumnDataSource(
        data={
            "x0": [x_src],
            "y0": [y_baseline],
            "x1": [x_tgt],
            "y1": [y_baseline],
            "cx0": [cx0],
            "cy0": [cy],
            "cx1": [cx1],
            "cy1": [cy],
            "source_name": [nodes[src_idx]],
            "target_name": [nodes[tgt_idx]],
            "weight_label": [weight_labels[weight]],
        }
    )
    renderer = p.bezier(
        x0="x0",
        y0="y0",
        x1="x1",
        y1="y1",
        cx0="cx0",
        cy0="cy0",
        cx1="cx1",
        cy1="cy1",
        source=arc_source,
        line_width=line_width,
        line_color=color,
        line_alpha=alpha,
    )
    arc_renderers_by_weight[weight].append(renderer)

# HoverTool for edge details (Bokeh-distinctive interactivity)
hover = HoverTool(
    tooltips=[("Connection", "@source_name \u2194 @target_name"), ("Frequency", "@weight_label")], line_policy="interp"
)
p.add_tools(hover)

# Draw nodes with degree-based sizing and coloring
node_source = ColumnDataSource(
    data={
        "x": x_positions,
        "y": [y_baseline] * n_nodes,
        "name": nodes,
        "size": node_sizes,
        "color": node_colors,
        "connections": [int(wd) for wd in weighted_degrees],
    }
)
node_renderer = p.scatter(
    x="x", y="y", source=node_source, size="size", fill_color="color", line_color="white", line_width=3
)

# Node hover with connection strength
node_hover = HoverTool(
    tooltips=[("Character", "@name"), ("Connection Strength", "@connections")], renderers=[node_renderer]
)
p.add_tools(node_hover)

# Node labels
for i, name in enumerate(nodes):
    label = Label(
        x=x_positions[i],
        y=-0.22,
        text=name,
        text_font_size="20pt",
        text_align="center",
        text_baseline="top",
        text_color="#333333",
    )
    p.add_layout(label)

# Legend by interaction frequency
legend_items = []
for weight, label_text in [(3, "Frequent"), (2, "Moderate"), (1, "Brief")]:
    if arc_renderers_by_weight[weight]:
        legend_items.append(LegendItem(label=label_text, renderers=[arc_renderers_by_weight[weight][0]]))

legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="20pt",
    label_text_color="#444444",
    border_line_color=None,
    background_fill_color="#F7F9FB",
    background_fill_alpha=0.9,
    glyph_width=40,
    glyph_height=8,
    spacing=12,
    padding=18,
)
p.add_layout(legend)

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="arc-basic")
