""" pyplots.ai
alluvial-basic: Basic Alluvial Diagram
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import Label, Legend, LegendItem
from bokeh.plotting import figure


# Data: Voter migration between political parties across 4 election years
np.random.seed(42)

time_points = ["2012", "2016", "2020", "2024"]
categories = ["Democratic", "Republican", "Independent", "Other"]
colors = {"Democratic": "#306998", "Republican": "#D62728", "Independent": "#FFD43B", "Other": "#7F7F7F"}

# Define flows between consecutive time points (from_cat, to_cat, value in millions)
flows_data = [
    # 2012 -> 2016
    [
        ("Democratic", "Democratic", 35),
        ("Democratic", "Independent", 5),
        ("Democratic", "Republican", 2),
        ("Republican", "Republican", 30),
        ("Republican", "Independent", 4),
        ("Republican", "Democratic", 3),
        ("Independent", "Democratic", 4),
        ("Independent", "Republican", 3),
        ("Independent", "Independent", 8),
        ("Other", "Other", 3),
        ("Other", "Independent", 2),
        ("Other", "Democratic", 1),
    ],
    # 2016 -> 2020
    [
        ("Democratic", "Democratic", 38),
        ("Democratic", "Independent", 3),
        ("Democratic", "Republican", 2),
        ("Republican", "Republican", 32),
        ("Republican", "Independent", 3),
        ("Republican", "Democratic", 2),
        ("Independent", "Democratic", 5),
        ("Independent", "Republican", 4),
        ("Independent", "Independent", 8),
        ("Other", "Other", 2),
        ("Other", "Independent", 2),
        ("Other", "Republican", 1),
    ],
    # 2020 -> 2024
    [
        ("Democratic", "Democratic", 40),
        ("Democratic", "Independent", 4),
        ("Democratic", "Republican", 1),
        ("Republican", "Republican", 34),
        ("Republican", "Independent", 2),
        ("Republican", "Democratic", 3),
        ("Independent", "Democratic", 4),
        ("Independent", "Republican", 5),
        ("Independent", "Independent", 6),
        ("Other", "Other", 2),
        ("Other", "Democratic", 1),
        ("Other", "Independent", 1),
    ],
]

# Calculate node heights at each time point
node_heights = []
for t_idx, _t in enumerate(time_points):
    heights = {}
    if t_idx == 0:
        for cat in categories:
            heights[cat] = sum(f[2] for f in flows_data[0] if f[0] == cat)
    elif t_idx == len(time_points) - 1:
        for cat in categories:
            heights[cat] = sum(f[2] for f in flows_data[-1] if f[1] == cat)
    else:
        for cat in categories:
            heights[cat] = sum(f[2] for f in flows_data[t_idx - 1] if f[1] == cat)
    node_heights.append(heights)

# Plot dimensions
x_positions = [0, 1, 2, 3]
node_width = 0.12
gap = 2

# Calculate node positions (y_start, y_end for each category at each time point)
node_positions = []
for t_idx in range(len(time_points)):
    positions = {}
    y_cursor = 0
    for cat in categories:
        height = node_heights[t_idx][cat]
        positions[cat] = {"y_start": y_cursor, "y_end": y_cursor + height}
        y_cursor += height + gap
    node_positions.append(positions)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="alluvial-basic · bokeh · pyplots.ai",
    x_range=(-0.9, 4.3),
    y_range=(-8, max(sum(node_heights[0].values()) + gap * len(categories), 120)),
    tools="",
    toolbar_location=None,
)

# Style the figure
p.title.text_font_size = "32pt"
p.title.align = "center"
p.xgrid.visible = False
p.ygrid.visible = False
p.xaxis.visible = False
p.yaxis.visible = False
p.outline_line_color = None
p.background_fill_color = "#FAFAFA"

# Add subtitle explaining units
subtitle = Label(
    x=1.5,
    y=115,
    text="Voter Migration Between Parties (values in millions)",
    text_font_size="20pt",
    text_align="center",
    text_baseline="top",
    text_color="#666666",
)
p.add_layout(subtitle)

# Draw flows (bands connecting nodes) - inline bezier calculation for KISS structure
n_points = 50
t_param = np.linspace(0, 1, n_points)

for t_idx, flows in enumerate(flows_data):
    x_start = x_positions[t_idx] + node_width / 2
    x_end = x_positions[t_idx + 1] - node_width / 2

    # Track current position for each category on source and target sides
    source_cursors = {cat: node_positions[t_idx][cat]["y_start"] for cat in categories}
    target_cursors = {cat: node_positions[t_idx + 1][cat]["y_start"] for cat in categories}

    for from_cat, to_cat, value in flows:
        if value == 0:
            continue

        # Source coordinates
        y_src_bottom = source_cursors[from_cat]
        y_src_top = y_src_bottom + value
        source_cursors[from_cat] = y_src_top

        # Target coordinates
        y_tgt_bottom = target_cursors[to_cat]
        y_tgt_top = y_tgt_bottom + value
        target_cursors[to_cat] = y_tgt_top

        # Inline bezier curve calculation for top and bottom edges
        cx0 = x_start + (x_end - x_start) / 3
        cx1 = x_start + 2 * (x_end - x_start) / 3

        # Top edge bezier
        x_top = (
            (1 - t_param) ** 3 * x_start
            + 3 * (1 - t_param) ** 2 * t_param * cx0
            + 3 * (1 - t_param) * t_param**2 * cx1
            + t_param**3 * x_end
        )
        y_top = (
            (1 - t_param) ** 3 * y_src_top
            + 3 * (1 - t_param) ** 2 * t_param * y_src_top
            + 3 * (1 - t_param) * t_param**2 * y_tgt_top
            + t_param**3 * y_tgt_top
        )

        # Bottom edge bezier
        x_bottom = (
            (1 - t_param) ** 3 * x_start
            + 3 * (1 - t_param) ** 2 * t_param * cx0
            + 3 * (1 - t_param) * t_param**2 * cx1
            + t_param**3 * x_end
        )
        y_bottom = (
            (1 - t_param) ** 3 * y_src_bottom
            + 3 * (1 - t_param) ** 2 * t_param * y_src_bottom
            + 3 * (1 - t_param) * t_param**2 * y_tgt_bottom
            + t_param**3 * y_tgt_bottom
        )

        # Create patch coordinates (top path + reversed bottom path)
        xs = list(x_top) + list(x_bottom[::-1])
        ys = list(y_top) + list(y_bottom[::-1])

        # Use source category color with transparency
        color = colors[from_cat]
        p.patch(xs, ys, fill_color=color, fill_alpha=0.5, line_color=color, line_alpha=0.7, line_width=1)

# Draw nodes (rectangles for each category at each time point) and collect legend items
legend_renderers = {}
for t_idx, _t in enumerate(time_points):
    x = x_positions[t_idx]
    for cat in categories:
        y_start = node_positions[t_idx][cat]["y_start"]
        y_end = node_positions[t_idx][cat]["y_end"]
        height = y_end - y_start

        if height > 0:
            # Draw node rectangle
            renderer = p.quad(
                left=x - node_width / 2,
                right=x + node_width / 2,
                top=y_end,
                bottom=y_start,
                fill_color=colors[cat],
                line_color="white",
                line_width=2,
            )

            # Store first renderer for each category for legend
            if cat not in legend_renderers:
                legend_renderers[cat] = renderer

            # Add category label with increased font size (20pt)
            if t_idx == 0:
                label = Label(
                    x=x - node_width / 2 - 0.03,
                    y=(y_start + y_end) / 2,
                    text=f"{cat} ({int(height)}M)",
                    text_font_size="20pt",
                    text_baseline="middle",
                    text_align="right",
                    text_color="#333333",
                )
                p.add_layout(label)
            elif t_idx == len(time_points) - 1:
                label = Label(
                    x=x + node_width / 2 + 0.03,
                    y=(y_start + y_end) / 2,
                    text=f"{cat} ({int(height)}M)",
                    text_font_size="20pt",
                    text_baseline="middle",
                    text_color="#333333",
                )
                p.add_layout(label)

# Create legend
legend_items = [LegendItem(label=cat, renderers=[legend_renderers[cat]]) for cat in categories]
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="18pt",
    glyph_width=30,
    glyph_height=30,
    spacing=10,
    padding=15,
    background_fill_alpha=0.8,
    background_fill_color="white",
    border_line_color="#cccccc",
)
p.add_layout(legend, "right")

# Add time point labels at the bottom
for t_idx, t in enumerate(time_points):
    label = Label(
        x=x_positions[t_idx],
        y=-4,
        text=t,
        text_font_size="24pt",
        text_align="center",
        text_baseline="top",
        text_color="#333333",
        text_font_style="bold",
    )
    p.add_layout(label)

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactive version
output_file("plot.html")
save(p)
