""" pyplots.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: altair 6.0.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-03
"""

import altair as alt
import numpy as np
import pandas as pd


np.random.seed(42)

# Data - Political opinion survey: 1000 respondents tracked across 4 quarterly waves
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
waves = ["Wave 1", "Wave 2", "Wave 3", "Wave 4"]
n_cats = len(categories)

initial_counts = [180, 250, 200, 220, 150]

# Transition matrices (rows = source category, cols = target category)
# Row sums match source wave totals, showing gradual polarization
transitions = [
    # Wave 1 -> Wave 2
    np.array(
        [[140, 25, 10, 5, 0], [20, 170, 40, 15, 5], [5, 30, 120, 35, 10], [0, 10, 25, 150, 35], [0, 5, 5, 20, 120]]
    ),
    # Wave 2 -> Wave 3
    np.array([[135, 20, 8, 2, 0], [25, 155, 35, 20, 5], [5, 25, 105, 45, 20], [0, 8, 20, 145, 52], [0, 2, 7, 18, 143]]),
    # Wave 3 -> Wave 4
    np.array([[140, 18, 5, 2, 0], [22, 135, 30, 18, 5], [3, 22, 100, 35, 15], [0, 5, 15, 155, 55], [0, 2, 5, 15, 198]]),
]

# Compute category totals at each wave
wave_totals = [dict(zip(categories, initial_counts, strict=True))]
for trans in transitions:
    wave_totals.append(dict(zip(categories, trans.sum(axis=0).tolist(), strict=True)))

# Layout constants (pixel coordinates)
width = 1600
height = 900
top_margin = 120
bottom_margin = 50
left_margin = 220
right_margin = 220
node_width = 50
node_padding = 18
available_height = height - top_margin - bottom_margin
available_width = width - left_margin - right_margin
n_waves = len(waves)

# X positions for each wave column
x_positions = [left_margin + i * (available_width / (n_waves - 1)) for i in range(n_waves)]

# Compute node positions (y start/height) for each wave and category
node_positions = {}
for w_idx in range(n_waves):
    time_total = sum(wave_totals[w_idx].values())
    usable_height = available_height * 0.88 - node_padding * (n_cats - 1)
    current_y = top_margin + (available_height - usable_height - node_padding * (n_cats - 1)) / 2

    node_positions[w_idx] = {}
    for cat in categories:
        cat_total = wave_totals[w_idx][cat]
        node_height = (cat_total / time_total) * usable_height
        node_positions[w_idx][cat] = {
            "y": current_y,
            "height": node_height,
            "x": x_positions[w_idx] - node_width / 2,
            "total": cat_total,
        }
        current_y += node_height + node_padding

# Colors for opinion categories (diverging blue-gray-red)
category_colors = {
    "Strongly Agree": "#306998",
    "Agree": "#5B9BD5",
    "Neutral": "#888888",
    "Disagree": "#E07B54",
    "Strongly Disagree": "#C0392B",
}

# Build flow polygon data
source_offsets = {}
target_offsets = {}
for w in range(n_waves):
    source_offsets[w] = {cat: node_positions[w][cat]["y"] for cat in categories}
    target_offsets[w] = {cat: node_positions[w][cat]["y"] for cat in categories}

all_flow_data = []
num_curve_points = 40

for t_idx, trans in enumerate(transitions):
    for s_idx, src_cat in enumerate(categories):
        for t_cat_idx, tgt_cat in enumerate(categories):
            val = int(trans[s_idx, t_cat_idx])
            if val == 0:
                continue

            src_pos = node_positions[t_idx][src_cat]
            tgt_pos = node_positions[t_idx + 1][tgt_cat]
            is_stable = s_idx == t_cat_idx

            src_height = (val / wave_totals[t_idx][src_cat]) * src_pos["height"]
            tgt_height = (val / wave_totals[t_idx + 1][tgt_cat]) * tgt_pos["height"]

            src_y_top = source_offsets[t_idx][src_cat]
            src_y_bottom = src_y_top + src_height
            tgt_y_top = target_offsets[t_idx + 1][tgt_cat]
            tgt_y_bottom = tgt_y_top + tgt_height

            source_offsets[t_idx][src_cat] += src_height
            target_offsets[t_idx + 1][tgt_cat] += tgt_height

            x_start = x_positions[t_idx] + node_width / 2
            x_end = x_positions[t_idx + 1] - node_width / 2

            flow_id = f"w{t_idx}_{src_cat}_{tgt_cat}"

            # Top curve (forward)
            top_points = []
            for i in range(num_curve_points):
                t_param = i / (num_curve_points - 1)
                x = x_start + t_param * (x_end - x_start)
                smooth = t_param * t_param * (3 - 2 * t_param)
                y = src_y_top + smooth * (tgt_y_top - src_y_top)
                top_points.append((x, y))

            # Bottom curve (reversed for closed polygon)
            bottom_points = []
            for i in range(num_curve_points - 1, -1, -1):
                t_param = i / (num_curve_points - 1)
                x = x_start + t_param * (x_end - x_start)
                smooth = t_param * t_param * (3 - 2 * t_param)
                y = src_y_bottom + smooth * (tgt_y_bottom - src_y_bottom)
                bottom_points.append((x, y))

            all_points = top_points + bottom_points
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
                        "is_stable": is_stable,
                    }
                )

flows_df = pd.DataFrame(all_flow_data)
stable_df = flows_df[flows_df["is_stable"]].reset_index(drop=True)
change_df = flows_df[~flows_df["is_stable"]].reset_index(drop=True)

# Node rectangles data
nodes_data = []
for w_idx in range(n_waves):
    for cat in categories:
        pos = node_positions[w_idx][cat]
        nodes_data.append(
            {
                "name": cat,
                "wave": waves[w_idx],
                "x": pos["x"],
                "y": pos["y"],
                "x2": pos["x"] + node_width,
                "y2": pos["y"] + pos["height"],
                "color": category_colors[cat],
                "total": pos["total"],
                "label_x": pos["x"] + node_width / 2,
                "label_y": pos["y"] + pos["height"] / 2,
                "wave_idx": w_idx,
            }
        )
nodes_df = pd.DataFrame(nodes_data)

# Shared scales
x_domain = alt.Scale(domain=[0, width])
y_domain = alt.Scale(domain=[0, height])
color_domain = list(category_colors.keys())
color_range = list(category_colors.values())

# Stable flows (higher opacity to emphasize persistence)
stable_chart = (
    alt.Chart(stable_df)
    .mark_line(filled=True, opacity=0.55, strokeWidth=0)
    .encode(
        x=alt.X("x:Q", scale=x_domain, axis=None),
        y=alt.Y("y:Q", scale=y_domain, axis=None),
        color=alt.Color("source_cat:N", scale=alt.Scale(domain=color_domain, range=color_range), legend=None),
        detail="flow_id:N",
        order="order:Q",
        tooltip=[alt.Tooltip("source_cat:N", title="Category"), alt.Tooltip("value:Q", title="Respondents (stable)")],
    )
)

# Changing flows (lower opacity to distinguish from stable)
change_chart = (
    alt.Chart(change_df)
    .mark_line(filled=True, opacity=0.22, strokeWidth=0)
    .encode(
        x=alt.X("x:Q", scale=x_domain, axis=None),
        y=alt.Y("y:Q", scale=y_domain, axis=None),
        color=alt.Color("source_cat:N", scale=alt.Scale(domain=color_domain, range=color_range), legend=None),
        detail="flow_id:N",
        order="order:Q",
        tooltip=[
            alt.Tooltip("source_cat:N", title="From"),
            alt.Tooltip("target_cat:N", title="To"),
            alt.Tooltip("value:Q", title="Respondents"),
        ],
    )
)

# Node rectangles
nodes_chart = (
    alt.Chart(nodes_df)
    .mark_rect(stroke="#333333", strokeWidth=1.5, cornerRadius=3)
    .encode(
        x=alt.X("x:Q", scale=x_domain),
        y=alt.Y("y:Q", scale=y_domain),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color("color:N", scale=None),
        tooltip=[
            alt.Tooltip("wave:N", title="Wave"),
            alt.Tooltip("name:N", title="Opinion"),
            alt.Tooltip("total:Q", title="Respondents"),
        ],
    )
)

# Count labels on nodes
nodes_df["count_label"] = nodes_df["total"].astype(str)
count_labels = (
    alt.Chart(nodes_df[nodes_df["y2"] - nodes_df["y"] >= 25].reset_index(drop=True))
    .mark_text(fontSize=13, fontWeight="bold", color="#FFFFFF", baseline="middle", align="center")
    .encode(x=alt.X("label_x:Q", scale=x_domain), y=alt.Y("label_y:Q", scale=y_domain), text="count_label:N")
)

# Side labels: left (Wave 1) and right (Wave 4)
label_data = []
for _, row in nodes_df.iterrows():
    y_mid = (row["y"] + row["y2"]) / 2
    if row["wave_idx"] == 0:
        label_data.append(
            {"x": row["x"] - 10, "y": y_mid, "text": f"{row['name']} ({int(row['total'])})", "align": "right"}
        )
    elif row["wave_idx"] == n_waves - 1:
        label_data.append(
            {"x": row["x2"] + 10, "y": y_mid, "text": f"{row['name']} ({int(row['total'])})", "align": "left"}
        )

labels_df = pd.DataFrame(label_data)

left_labels = (
    alt.Chart(labels_df[labels_df["align"] == "right"].reset_index(drop=True))
    .mark_text(fontSize=15, fontWeight="bold", color="#444444", align="right", baseline="middle")
    .encode(x=alt.X("x:Q", scale=x_domain), y=alt.Y("y:Q", scale=y_domain), text="text:N")
)

right_labels = (
    alt.Chart(labels_df[labels_df["align"] == "left"].reset_index(drop=True))
    .mark_text(fontSize=15, fontWeight="bold", color="#444444", align="left", baseline="middle")
    .encode(x=alt.X("x:Q", scale=x_domain), y=alt.Y("y:Q", scale=y_domain), text="text:N")
)

# Wave column headers
wave_header_data = [{"x": x_positions[i], "y": top_margin - 45, "text": waves[i]} for i in range(n_waves)]
wave_headers = (
    alt.Chart(pd.DataFrame(wave_header_data))
    .mark_text(fontSize=22, fontWeight="bold", color="#333333", baseline="bottom")
    .encode(x=alt.X("x:Q", scale=x_domain), y=alt.Y("y:Q", scale=y_domain), text="text:N")
)

# Combine all layers
chart = (
    alt.layer(change_chart, stable_chart, nodes_chart, count_labels, left_labels, right_labels, wave_headers)
    .properties(
        width=width,
        height=height,
        title=alt.Title(
            text="alluvial-opinion-flow · altair · pyplots.ai", fontSize=28, anchor="middle", color="#333333", offset=20
        ),
    )
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
