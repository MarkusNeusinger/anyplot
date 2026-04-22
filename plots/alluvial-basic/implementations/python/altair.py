""" pyplots.ai
alluvial-basic: Basic Alluvial Diagram
Library: altair 6.0.0 | Python 3.13.11
Quality: 95/100 | Created: 2025-12-26
"""

import altair as alt
import pandas as pd


# Data: Voter migration between political parties across 4 election cycles
# Time points: 2012, 2016, 2020, 2024
# Categories: Conservative, Liberal, Progressive, Independent

time_points = ["2012", "2016", "2020", "2024"]
categories = ["Conservative", "Liberal", "Progressive", "Independent"]

# Define flows between consecutive time points
# Format: (source_time_idx, source_cat_idx, target_cat_idx, value)
flows_data = [
    # 2012 -> 2016 transitions
    (0, 0, 0, 280),  # Conservative stays Conservative
    (0, 0, 3, 20),  # Conservative to Independent
    (0, 1, 1, 250),  # Liberal stays Liberal
    (0, 1, 2, 30),  # Liberal to Progressive
    (0, 1, 3, 15),  # Liberal to Independent
    (0, 2, 2, 120),  # Progressive stays Progressive
    (0, 2, 1, 25),  # Progressive to Liberal
    (0, 3, 3, 80),  # Independent stays Independent
    (0, 3, 0, 30),  # Independent to Conservative
    (0, 3, 1, 20),  # Independent to Liberal
    # 2016 -> 2020 transitions
    (1, 0, 0, 260),  # Conservative stays Conservative
    (1, 0, 3, 50),  # Conservative to Independent
    (1, 1, 1, 240),  # Liberal stays Liberal
    (1, 1, 2, 45),  # Liberal to Progressive
    (1, 2, 2, 140),  # Progressive stays Progressive
    (1, 2, 1, 35),  # Progressive to Liberal
    (1, 3, 3, 90),  # Independent stays Independent
    (1, 3, 0, 25),  # Independent to Conservative
    (1, 3, 2, 15),  # Independent to Progressive
    # 2020 -> 2024 transitions
    (2, 0, 0, 250),  # Conservative stays Conservative
    (2, 0, 3, 35),  # Conservative to Independent
    (2, 1, 1, 255),  # Liberal stays Liberal
    (2, 1, 2, 40),  # Liberal to Progressive
    (2, 2, 2, 160),  # Progressive stays Progressive
    (2, 2, 1, 40),  # Progressive to Liberal
    (2, 3, 3, 100),  # Independent stays Independent
    (2, 3, 0, 20),  # Independent to Conservative
    (2, 3, 1, 10),  # Independent to Liberal
]

# Canvas dimensions: 1600x900 for 4800x2700 at scale_factor=3.0
width = 1600
height = 900
node_width = 60
node_padding = 20

# Colors for each category (consistent across time points)
category_colors = {
    "Conservative": "#306998",  # Python Blue
    "Liberal": "#FFD43B",  # Python Yellow
    "Progressive": "#2CA02C",  # Green
    "Independent": "#9467BD",  # Purple
}

# Calculate totals at each time point for each category
totals = {}
for t in range(len(time_points)):
    totals[t] = dict.fromkeys(categories, 0)

# Accumulate incoming flows for each node (except first column uses outgoing)
for src_t, src_cat_idx, tgt_cat_idx, val in flows_data:
    tgt_t = src_t + 1
    if src_t == 0:
        totals[0][categories[src_cat_idx]] += val
    totals[tgt_t][categories[tgt_cat_idx]] += val

# Margins for layout
top_margin = 130
bottom_margin = 50
left_margin = 100
right_margin = 100
available_height = height - top_margin - bottom_margin
available_width = width - left_margin - right_margin

# X positions for each time point (evenly spaced)
x_positions = []
for t in range(len(time_points)):
    x_positions.append(left_margin + t * (available_width / (len(time_points) - 1)))

# Calculate node positions for each time point
node_positions = {}
for t in range(len(time_points)):
    time_total = sum(totals[t].values())
    if time_total == 0:
        continue

    # Calculate heights proportionally
    total_height = available_height * 0.85
    padding_total = node_padding * (len(categories) - 1)
    usable_height = total_height - padding_total

    current_y = top_margin + (available_height - total_height) / 2
    node_positions[t] = {}

    for cat in categories:
        cat_total = totals[t][cat]
        if cat_total > 0:
            node_height = (cat_total / time_total) * usable_height
            node_positions[t][cat] = {
                "y": current_y,
                "height": node_height,
                "x": x_positions[t] - node_width / 2,
                "total": cat_total,
            }
            current_y += node_height + node_padding
        else:
            node_positions[t][cat] = {"y": current_y, "height": 0, "x": x_positions[t], "total": 0}

# Create node rectangles data
nodes_data = []
for t in range(len(time_points)):
    for cat in categories:
        pos = node_positions[t][cat]
        if pos["height"] > 0:
            nodes_data.append(
                {
                    "name": cat,
                    "time_point": time_points[t],
                    "x": pos["x"],
                    "y": pos["y"],
                    "x2": pos["x"] + node_width,
                    "y2": pos["y"] + pos["height"],
                    "color": category_colors[cat],
                    "total": pos["total"],
                    "label_x": pos["x"] + node_width / 2,
                    "label_y": pos["y"] + pos["height"] / 2,
                }
            )

nodes_df = pd.DataFrame(nodes_data)

# Track y offsets for stacking flows within nodes
source_offsets = {}
target_offsets = {}
for t in range(len(time_points)):
    source_offsets[t] = {cat: node_positions[t][cat]["y"] for cat in categories}
    target_offsets[t] = {cat: node_positions[t][cat]["y"] for cat in categories}

# Generate flow polygon data
all_flow_data = []
num_curve_points = 30

for flow_idx, (src_t, src_cat_idx, tgt_cat_idx, val) in enumerate(flows_data):
    tgt_t = src_t + 1
    src_cat = categories[src_cat_idx]
    tgt_cat = categories[tgt_cat_idx]

    src_pos = node_positions[src_t][src_cat]
    tgt_pos = node_positions[tgt_t][tgt_cat]

    if src_pos["height"] == 0 or tgt_pos["height"] == 0:
        continue

    # Calculate flow heights proportional to value
    src_height = (val / totals[src_t][src_cat]) * src_pos["height"]
    tgt_height = (val / totals[tgt_t][tgt_cat]) * tgt_pos["height"]

    # Get current offset positions
    src_y_top = source_offsets[src_t][src_cat]
    src_y_bottom = src_y_top + src_height
    tgt_y_top = target_offsets[tgt_t][tgt_cat]
    tgt_y_bottom = tgt_y_top + tgt_height

    # Update offsets for next flow
    source_offsets[src_t][src_cat] += src_height
    target_offsets[tgt_t][tgt_cat] += tgt_height

    # X coordinates for flow start and end
    x_start = x_positions[src_t] + node_width / 2
    x_end = x_positions[tgt_t] - node_width / 2

    # Generate top curve points using smoothstep
    top_points = []
    for i in range(num_curve_points):
        t_param = i / (num_curve_points - 1)
        x = x_start + t_param * (x_end - x_start)
        bezier_t = t_param * t_param * (3 - 2 * t_param)
        y = src_y_top + bezier_t * (tgt_y_top - src_y_top)
        top_points.append((x, y))

    # Generate bottom curve points (reverse order for closed polygon)
    bottom_points = []
    for i in range(num_curve_points - 1, -1, -1):
        t_param = i / (num_curve_points - 1)
        x = x_start + t_param * (x_end - x_start)
        bezier_t = t_param * t_param * (3 - 2 * t_param)
        y = src_y_bottom + bezier_t * (tgt_y_bottom - src_y_bottom)
        bottom_points.append((x, y))

    # Combine into closed polygon
    all_points = top_points + bottom_points
    flow_id = f"{time_points[src_t]}-{src_cat}-{tgt_cat}-{flow_idx}"

    for pt_idx, (x, y) in enumerate(all_points):
        all_flow_data.append(
            {
                "flow_id": flow_id,
                "source_cat": src_cat,
                "target_cat": tgt_cat,
                "value": val,
                "x": x,
                "y": y,
                "order": pt_idx,
            }
        )

flows_df = pd.DataFrame(all_flow_data)

# Create flow polygons layer
links_chart = (
    alt.Chart(flows_df)
    .mark_line(filled=True, opacity=0.5, strokeWidth=0)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, width]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, height]), axis=None),
        color=alt.Color(
            "source_cat:N",
            scale=alt.Scale(domain=list(category_colors.keys()), range=list(category_colors.values())),
            legend=alt.Legend(
                title="Party",
                titleFontSize=22,
                labelFontSize=20,
                orient="right",
                titleColor="#333333",
                labelColor="#333333",
                symbolSize=300,
            ),
        ),
        detail="flow_id:N",
        order="order:Q",
    )
)

# Create node rectangles layer
nodes_chart = (
    alt.Chart(nodes_df)
    .mark_rect(stroke="#333333", strokeWidth=2)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, width])),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, height])),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color("color:N", scale=None),
        tooltip=[
            alt.Tooltip("name:N", title="Party"),
            alt.Tooltip("time_point:N", title="Year"),
            alt.Tooltip("total:Q", title="Voters (thousands)"),
        ],
    )
)

# Create node labels (directly on nodes) - abbreviate for readability
label_abbrev = {"Conservative": "Con", "Liberal": "Lib", "Progressive": "Prog", "Independent": "Ind"}
nodes_df["label"] = nodes_df["name"].map(label_abbrev)

node_labels = (
    alt.Chart(nodes_df)
    .mark_text(fontSize=14, fontWeight="bold", color="#FFFFFF", baseline="middle", align="center")
    .encode(
        x=alt.X("label_x:Q", scale=alt.Scale(domain=[0, width])),
        y=alt.Y("label_y:Q", scale=alt.Scale(domain=[0, height])),
        text="label:N",
    )
)

# Create time point labels (column headers)
time_labels_data = []
for t, tp in enumerate(time_points):
    time_labels_data.append({"x": x_positions[t], "y": top_margin - 40, "text": tp})
time_labels_df = pd.DataFrame(time_labels_data)

time_labels = (
    alt.Chart(time_labels_df)
    .mark_text(fontSize=24, fontWeight="bold", color="#333333", baseline="bottom")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, width])),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, height])),
        text="text:N",
    )
)

# Combine all layers with interactivity
chart = (
    alt.layer(links_chart, nodes_chart, node_labels, time_labels)
    .properties(
        width=width,
        height=height,
        title=alt.Title(
            text="alluvial-basic · altair · pyplots.ai", fontSize=28, anchor="middle", color="#333333", offset=20
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(padding=15, cornerRadius=5, fillColor="#FFFFFF", strokeColor="#DDDDDD")
    .interactive()
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
