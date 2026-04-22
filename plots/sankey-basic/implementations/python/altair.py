""" pyplots.ai
sankey-basic: Basic Sankey Diagram
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import pandas as pd


# Data - Energy flow from sources to sectors
flows = [
    {"source": "Coal", "target": "Residential", "value": 20},
    {"source": "Coal", "target": "Commercial", "value": 15},
    {"source": "Coal", "target": "Industrial", "value": 45},
    {"source": "Gas", "target": "Residential", "value": 35},
    {"source": "Gas", "target": "Commercial", "value": 25},
    {"source": "Gas", "target": "Industrial", "value": 30},
    {"source": "Nuclear", "target": "Residential", "value": 15},
    {"source": "Nuclear", "target": "Commercial", "value": 20},
    {"source": "Nuclear", "target": "Industrial", "value": 15},
    {"source": "Renewable", "target": "Residential", "value": 25},
    {"source": "Renewable", "target": "Commercial", "value": 20},
    {"source": "Renewable", "target": "Transport", "value": 10},
]

df = pd.DataFrame(flows)

# Target output: 4800x2700 px (16:9 aspect ratio) with scale_factor=3.0
# Internal canvas: 1600x900 pixels
width = 1600
height = 900
node_width = 80
node_padding = 25

# Compute node positions
sources = df["source"].unique().tolist()
targets = df["target"].unique().tolist()

# Calculate totals for positioning
source_totals = df.groupby("source")["value"].sum().to_dict()
target_totals = df.groupby("target")["value"].sum().to_dict()
total_flow = df["value"].sum()

# Available height for nodes - reserve space for title (top) and margins
top_margin = 100
bottom_margin = 60
available_height = height - top_margin - bottom_margin

# Position source nodes on left, vertically centered
source_total_height = sum(source_totals.values()) / total_flow * available_height * 0.85
source_total_with_padding = source_total_height + node_padding * (len(sources) - 1)
start_y_sources = top_margin + (available_height - source_total_with_padding) / 2

source_positions = {}
current_y = start_y_sources
for src in sources:
    node_height = (source_totals[src] / total_flow) * available_height * 0.85
    source_positions[src] = {"y": current_y, "height": node_height}
    current_y += node_height + node_padding

# Position target nodes on right, vertically centered
target_total_height = sum(target_totals.values()) / total_flow * available_height * 0.85
target_total_with_padding = target_total_height + node_padding * (len(targets) - 1)
start_y_targets = top_margin + (available_height - target_total_with_padding) / 2

target_positions = {}
current_y = start_y_targets
for tgt in targets:
    node_height = (target_totals[tgt] / total_flow) * available_height * 0.85
    target_positions[tgt] = {"y": current_y, "height": node_height}
    current_y += node_height + node_padding

# Color palettes - Python Blue (#306998) as primary, Yellow (#FFD43B) for accent
source_colors = {"Coal": "#306998", "Gas": "#4A8BC6", "Nuclear": "#2D5986", "Renewable": "#FFD43B"}

target_colors = {"Residential": "#4ECDC4", "Commercial": "#95E1D3", "Industrial": "#FF6B6B", "Transport": "#FFA07A"}

# Create node rectangles data
nodes_data = []

for src in sources:
    pos = source_positions[src]
    nodes_data.append(
        {
            "name": src,
            "x": 0,
            "y": pos["y"],
            "x2": node_width,
            "y2": pos["y"] + pos["height"],
            "color": source_colors[src],
            "label_x": node_width + 15,
            "label_y": pos["y"] + pos["height"] / 2,
            "total": source_totals[src],
            "side": "source",
        }
    )

for tgt in targets:
    pos = target_positions[tgt]
    nodes_data.append(
        {
            "name": tgt,
            "x": width - node_width,
            "y": pos["y"],
            "x2": width,
            "y2": pos["y"] + pos["height"],
            "color": target_colors[tgt],
            "label_x": width - node_width - 15,
            "label_y": pos["y"] + pos["height"] / 2,
            "total": target_totals[tgt],
            "side": "target",
        }
    )

nodes_df = pd.DataFrame(nodes_data)

# Create flow paths using polygons
# Track current position within each node for stacking flows
source_y_offsets = {src: source_positions[src]["y"] for src in sources}
target_y_offsets = {tgt: target_positions[tgt]["y"] for tgt in targets}

# Generate polygon points for each flow (closed path)
all_flow_data = []
num_curve_points = 40

for _, row in df.iterrows():
    src = row["source"]
    tgt = row["target"]
    val = row["value"]

    # Flow height proportional to value within each node
    src_height = (val / source_totals[src]) * source_positions[src]["height"]
    tgt_height = (val / target_totals[tgt]) * target_positions[tgt]["height"]

    # Start and end Y positions for this flow band
    src_y_top = source_y_offsets[src]
    src_y_bottom = src_y_top + src_height
    tgt_y_top = target_y_offsets[tgt]
    tgt_y_bottom = tgt_y_top + tgt_height

    # Update offsets for stacking next flow from same source/target
    source_y_offsets[src] += src_height
    target_y_offsets[tgt] += tgt_height

    x_start = node_width
    x_end = width - node_width

    # Generate top curve points (left to right) using smoothstep interpolation
    top_points = []
    for i in range(num_curve_points):
        t = i / (num_curve_points - 1)
        x = x_start + t * (x_end - x_start)
        # Smoothstep creates smooth S-curve for natural flow appearance
        bezier_t = t * t * (3 - 2 * t)
        y = src_y_top + bezier_t * (tgt_y_top - src_y_top)
        top_points.append((x, y))

    # Generate bottom curve points (right to left to close the polygon)
    bottom_points = []
    for i in range(num_curve_points - 1, -1, -1):
        t = i / (num_curve_points - 1)
        x = x_start + t * (x_end - x_start)
        bezier_t = t * t * (3 - 2 * t)
        y = src_y_bottom + bezier_t * (tgt_y_bottom - src_y_bottom)
        bottom_points.append((x, y))

    # Combine top + bottom into closed polygon for filled area rendering
    all_points = top_points + bottom_points
    for pt_idx, (x, y) in enumerate(all_points):
        all_flow_data.append(
            {"flow_id": f"{src}-{tgt}", "source": src, "target": tgt, "value": val, "x": x, "y": y, "order": pt_idx}
        )

flows_df = pd.DataFrame(all_flow_data)

# Create flow polygons using mark_line with filled=True
links_chart = (
    alt.Chart(flows_df)
    .mark_line(filled=True, opacity=0.55, strokeWidth=0)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, width]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, height]), axis=None),
        color=alt.Color(
            "source:N",
            scale=alt.Scale(domain=list(source_colors.keys()), range=list(source_colors.values())),
            legend=alt.Legend(
                title="Energy Source",
                titleFontSize=18,
                labelFontSize=16,
                orient="bottom-right",
                titleColor="#333333",
                labelColor="#333333",
            ),
        ),
        detail="flow_id:N",
        order="order:Q",
    )
)

# Create node rectangles
nodes_chart = (
    alt.Chart(nodes_df)
    .mark_rect(stroke="#333333", strokeWidth=2)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, width])),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, height])),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color("color:N", scale=None),
        tooltip=[alt.Tooltip("name:N", title="Node"), alt.Tooltip("total:Q", title="Total Flow (units)")],
    )
)

# Create source labels (right-aligned to the left of nodes)
source_labels_df = nodes_df[nodes_df["side"] == "source"]
source_labels = (
    alt.Chart(source_labels_df)
    .mark_text(fontSize=20, fontWeight="bold", color="#333333", align="left", baseline="middle")
    .encode(
        x=alt.X("label_x:Q", scale=alt.Scale(domain=[0, width])),
        y=alt.Y("label_y:Q", scale=alt.Scale(domain=[0, height])),
        text="name:N",
    )
)

# Create target labels (left-aligned to the right of nodes)
target_labels_df = nodes_df[nodes_df["side"] == "target"]
target_labels = (
    alt.Chart(target_labels_df)
    .mark_text(fontSize=20, fontWeight="bold", color="#333333", align="right", baseline="middle")
    .encode(
        x=alt.X("label_x:Q", scale=alt.Scale(domain=[0, width])),
        y=alt.Y("label_y:Q", scale=alt.Scale(domain=[0, height])),
        text="name:N",
    )
)

# Combine all layers
chart = (
    alt.layer(links_chart, nodes_chart, source_labels, target_labels)
    .properties(
        width=width,
        height=height,
        title=alt.Title(
            text="sankey-basic · altair · pyplots.ai",
            subtitle="Energy Flow from Sources to Sectors",
            fontSize=28,
            subtitleFontSize=20,
            anchor="middle",
            color="#333333",
            subtitleColor="#666666",
        ),
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(padding=15, cornerRadius=5, fillColor="#FFFFFF", strokeColor="#DDDDDD")
)

# Save as PNG (4800x2700 px with scale_factor=3.0) and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
