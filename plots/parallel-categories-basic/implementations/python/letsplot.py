""" anyplot.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_label,
    geom_polygon,
    geom_rect,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DIMENSIONS = ["Channel", "Product", "Size", "Outcome"]  # role: dimension_
COUNT = "Count"  # role: count

# Data: replace this block with your own table, for example df = pd.read_csv("journeys.csv")
# Customer journeys: acquisition channel, product category, purchase size, outcome
df = pd.DataFrame(
    [
        # Online channel journeys
        ("Online", "Electronics", "Large", "Completed", 45),
        ("Online", "Electronics", "Small", "Completed", 32),
        ("Online", "Electronics", "Large", "Abandoned", 18),
        ("Online", "Electronics", "Small", "Abandoned", 12),
        ("Online", "Clothing", "Large", "Completed", 28),
        ("Online", "Clothing", "Small", "Completed", 55),
        ("Online", "Clothing", "Large", "Abandoned", 8),
        ("Online", "Clothing", "Small", "Abandoned", 15),
        ("Online", "Home", "Large", "Completed", 22),
        ("Online", "Home", "Small", "Completed", 18),
        ("Online", "Home", "Large", "Abandoned", 10),
        ("Online", "Home", "Small", "Abandoned", 7),
        # Store channel journeys
        ("Store", "Electronics", "Large", "Completed", 35),
        ("Store", "Electronics", "Small", "Completed", 20),
        ("Store", "Electronics", "Large", "Abandoned", 5),
        ("Store", "Electronics", "Small", "Abandoned", 3),
        ("Store", "Clothing", "Large", "Completed", 40),
        ("Store", "Clothing", "Small", "Completed", 65),
        ("Store", "Clothing", "Large", "Abandoned", 4),
        ("Store", "Clothing", "Small", "Abandoned", 6),
        ("Store", "Home", "Large", "Completed", 30),
        ("Store", "Home", "Small", "Completed", 25),
        ("Store", "Home", "Large", "Abandoned", 3),
        ("Store", "Home", "Small", "Abandoned", 2),
        # Mobile channel journeys
        ("Mobile", "Electronics", "Large", "Completed", 25),
        ("Mobile", "Electronics", "Small", "Completed", 42),
        ("Mobile", "Electronics", "Large", "Abandoned", 22),
        ("Mobile", "Electronics", "Small", "Abandoned", 18),
        ("Mobile", "Clothing", "Large", "Completed", 15),
        ("Mobile", "Clothing", "Small", "Completed", 48),
        ("Mobile", "Clothing", "Large", "Abandoned", 10),
        ("Mobile", "Clothing", "Small", "Abandoned", 20),
        ("Mobile", "Home", "Large", "Completed", 12),
        ("Mobile", "Home", "Small", "Completed", 22),
        ("Mobile", "Home", "Large", "Abandoned", 8),
        ("Mobile", "Home", "Small", "Abandoned", 12),
    ],
    columns=[*DIMENSIONS, COUNT],
)

# Plot: reads only df and the constants above
n_dims = len(DIMENSIONS)
first_dim = DIMENSIONS[0]
total_flow = df[COUNT].sum()

# Categories per dimension keep the data's order; ribbons are colored by the first dimension
categories = {dim: list(df[dim].dropna().unique()) for dim in DIMENSIONS}
channel_colors = dict(zip(categories[first_dim], IMPRINT_PALETTE, strict=False))
dimension_totals = {dim: df.groupby(dim, sort=False)[COUNT].sum().to_dict() for dim in DIMENSIONS}

# Layout parameters in the panel's unit square
x_positions = [0.13 + 0.62 * i / (n_dims - 1) for i in range(n_dims)]
node_width = 0.030
node_gap = 0.035
flow_scale = 0.72

# Node positions for all dimensions
node_positions = []
for dim_idx, dim in enumerate(DIMENSIONS):
    positions = {}
    y_offset = 0.10
    for cat in categories[dim]:
        height = dimension_totals[dim][cat] / total_flow * flow_scale
        positions[cat] = {"y0": y_offset, "y1": y_offset + height, "x": x_positions[dim_idx]}
        y_offset += height + node_gap
    node_positions.append(positions)

# Flow polygons between adjacent dimensions
flow_data = []
for dim_from_idx in range(n_dims - 1):
    dim_from = DIMENSIONS[dim_from_idx]
    dim_to = DIMENSIONS[dim_from_idx + 1]

    # Aggregate flows between categories, split by the coloring dimension
    flow_counts = df.groupby([dim_from, dim_to, first_dim], sort=False)[COUNT].sum()

    # Offsets for stacking ribbons within each node
    from_offsets = dict.fromkeys(categories[dim_from], 0)
    to_offsets = dict.fromkeys(categories[dim_to], 0)

    from_positions = node_positions[dim_from_idx]
    to_positions = node_positions[dim_from_idx + 1]

    x_left = x_positions[dim_from_idx] + node_width / 2
    x_right = x_positions[dim_from_idx + 1] - node_width / 2

    sorted_flows = sorted(
        flow_counts.items(),
        key=lambda item: (
            categories[dim_from].index(item[0][0]),
            categories[dim_to].index(item[0][1]),
            categories[first_dim].index(item[0][2]),
        ),
    )

    for (from_cat, to_cat, source_channel), count in sorted_flows:
        flow_height = count / total_flow * flow_scale

        src_y0 = from_positions[from_cat]["y0"] + from_offsets[from_cat]
        src_y1 = src_y0 + flow_height
        from_offsets[from_cat] += flow_height

        tgt_y0 = to_positions[to_cat]["y0"] + to_offsets[to_cat]
        tgt_y1 = tgt_y0 + flow_height
        to_offsets[to_cat] += flow_height

        # Smooth ribbon edges with a smoothstep easing curve
        n_points = 30
        ts = [i / n_points for i in range(n_points + 1)]
        xs = [x_left + t * (x_right - x_left) for t in ts]
        eases = [t * t * (3 - 2 * t) for t in ts]
        y_top = [src_y1 + e * (tgt_y1 - src_y1) for e in eases]
        y_bottom = [src_y0 + e * (tgt_y0 - src_y0) for e in eases]

        # Close the polygon: top edge forward, bottom edge back
        flow_id = f"d{dim_from_idx}_{from_cat}_{to_cat}_{source_channel}"
        for x, y in zip(xs + xs[::-1], y_top + y_bottom[::-1], strict=True):
            flow_data.append({"x": x, "y": y, "flow_id": flow_id, "channel": source_channel})

df_flows = pd.DataFrame(flow_data)

# Node rectangles
node_rects = [
    {
        "xmin": node_positions[dim_idx][cat]["x"] - node_width / 2,
        "xmax": node_positions[dim_idx][cat]["x"] + node_width / 2,
        "ymin": node_positions[dim_idx][cat]["y0"],
        "ymax": node_positions[dim_idx][cat]["y1"],
    }
    for dim_idx, dim in enumerate(DIMENSIONS)
    for cat in categories[dim]
]
df_nodes = pd.DataFrame(node_rects)

# Dimension headers at the top
df_headers = pd.DataFrame({"x": x_positions, "y": 0.96, "label": DIMENSIONS})

# Category labels with counts: left of the first axis, right of every other axis
left_labels = []
right_labels = []
for dim_idx, dim in enumerate(DIMENSIONS):
    for cat in categories[dim]:
        pos = node_positions[dim_idx][cat]
        on_left = dim_idx == 0
        offset = -(node_width / 2 + 0.02) if on_left else node_width / 2 + 0.02
        row = {
            "x": pos["x"] + offset,
            "y": (pos["y0"] + pos["y1"]) / 2,
            "label": f"{cat} ({dimension_totals[dim][cat]})",
        }
        (left_labels if on_left else right_labels).append(row)
df_left = pd.DataFrame(left_labels)
df_right = pd.DataFrame(right_labels)

plot = (
    ggplot()
    + geom_polygon(
        aes(x="x", y="y", group="flow_id", fill="channel"), data=df_flows, alpha=0.5, color="white", size=0.04
    )
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), data=df_nodes, fill=INK_SOFT, color=INK, size=0.5
    )
    + geom_text(aes(x="x", y="y", label="label"), data=df_headers, size=9, hjust=0.5, fontface="bold", color=INK)
    + geom_label(
        aes(x="x", y="y", label="label"),
        data=df_left,
        size=6,
        hjust=1,
        color=INK_SOFT,
        fill=PAGE_BG,
        alpha=0.85,
        label_size=0,
    )
    + geom_label(
        aes(x="x", y="y", label="label"),
        data=df_right,
        size=6,
        hjust=0,
        color=INK_SOFT,
        fill=PAGE_BG,
        alpha=0.85,
        label_size=0,
    )
    + scale_fill_manual(values=channel_colors, name=f"Acquisition {first_dim.lower()}")
    + labs(title="parallel-categories-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=11, face="bold", color=INK),
        legend_position="bottom",
        legend_background=element_blank(),
    )
    + scale_x_continuous(limits=[-0.02, 1.02])
    + scale_y_continuous(limits=[-0.02, 1.02])
    + ggsize(800, 450)
)

# Save as PNG (scale 4x for 3200 × 1800 px) and HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
