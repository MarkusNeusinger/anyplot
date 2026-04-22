""" pyplots.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-03
"""

import altair as alt
import numpy as np
import pandas as pd


np.random.seed(42)

# Data - Employee engagement survey: 1000 staff tracked across 4 quarterly waves
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
waves = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"]
n_cats = len(categories)

initial_counts = [180, 250, 200, 220, 150]

# Transition matrices showing gradual polarization in employee sentiment
transitions = [
    # Q1 -> Q2
    np.array(
        [[140, 25, 10, 5, 0], [20, 170, 40, 15, 5], [5, 30, 120, 35, 10], [0, 10, 25, 150, 35], [0, 5, 5, 20, 120]]
    ),
    # Q2 -> Q3
    np.array([[135, 20, 8, 2, 0], [25, 155, 35, 20, 5], [5, 25, 105, 45, 20], [0, 8, 20, 145, 52], [0, 2, 7, 18, 143]]),
    # Q3 -> Q4
    np.array([[140, 18, 5, 2, 0], [22, 135, 30, 18, 5], [3, 22, 100, 35, 15], [0, 5, 15, 155, 55], [0, 2, 5, 15, 198]]),
]

# Compute category totals at each wave
wave_totals = [dict(zip(categories, initial_counts, strict=True))]
for trans in transitions:
    wave_totals.append(dict(zip(categories, trans.sum(axis=0).tolist(), strict=True)))

# Layout constants
width = 1600
height = 900
top_margin = 130
bottom_margin = 60
left_margin = 240
right_margin = 350
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
    usable_height = available_height * 0.85 - node_padding * (n_cats - 1)
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

# Colors for sentiment categories (diverging blue-gray-red)
category_colors = {
    "Strongly Agree": "#306998",
    "Agree": "#79B8DE",
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

            top_points = []
            for i in range(num_curve_points):
                t_param = i / (num_curve_points - 1)
                x = x_start + t_param * (x_end - x_start)
                smooth = t_param * t_param * (3 - 2 * t_param)
                y = src_y_top + smooth * (tgt_y_top - src_y_top)
                top_points.append((x, y))

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
                        "name": src_cat,
                        "value": val,
                        "x": x,
                        "y": y,
                        "order": pt_idx,
                        "is_stable": is_stable,
                    }
                )

flows_df = pd.DataFrame(all_flow_data)

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

# Interactive hover selection for category highlighting
node_hover = alt.selection_point(fields=["name"], on="pointerover")

# Stable flows (higher opacity to emphasize persistence)
stable_chart = (
    alt.Chart(flows_df)
    .transform_filter("datum.is_stable")
    .mark_line(filled=True, opacity=0.65, strokeWidth=0)
    .encode(
        x=alt.X("x:Q", scale=x_domain, axis=None),
        y=alt.Y("y:Q", scale=y_domain, axis=None),
        color=alt.Color("source_cat:N", scale=alt.Scale(domain=color_domain, range=color_range), legend=None),
        detail="flow_id:N",
        order="order:Q",
        opacity=alt.condition(node_hover, alt.value(0.7), alt.value(0.5)),
        tooltip=[alt.Tooltip("source_cat:N", title="Category"), alt.Tooltip("value:Q", title="Respondents (stable)")],
    )
)

# Changing flows (increased opacity for better visibility)
change_chart = (
    alt.Chart(flows_df)
    .transform_filter("!datum.is_stable")
    .mark_line(filled=True, opacity=0.45, strokeWidth=0)
    .encode(
        x=alt.X("x:Q", scale=x_domain, axis=None),
        y=alt.Y("y:Q", scale=y_domain, axis=None),
        color=alt.Color("source_cat:N", scale=alt.Scale(domain=color_domain, range=color_range), legend=None),
        detail="flow_id:N",
        order="order:Q",
        opacity=alt.condition(node_hover, alt.value(0.5), alt.value(0.35)),
        tooltip=[
            alt.Tooltip("source_cat:N", title="From"),
            alt.Tooltip("target_cat:N", title="To"),
            alt.Tooltip("value:Q", title="Respondents"),
        ],
    )
)

# Node rectangles with color legend
nodes_chart = (
    alt.Chart(nodes_df)
    .mark_rect(stroke="#2A2A2A", strokeWidth=1.5, cornerRadius=5)
    .encode(
        x=alt.X("x:Q", scale=x_domain),
        y=alt.Y("y:Q", scale=y_domain),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color(
            "name:N",
            scale=alt.Scale(domain=color_domain, range=color_range),
            legend=alt.Legend(
                title="Sentiment",
                orient="bottom",
                direction="horizontal",
                titleFontSize=18,
                labelFontSize=18,
                titlePadding=10,
                symbolSize=220,
                padding=5,
            ),
        ),
        tooltip=[
            alt.Tooltip("wave:N", title="Quarter"),
            alt.Tooltip("name:N", title="Sentiment"),
            alt.Tooltip("total:Q", title="Respondents"),
        ],
    )
    .add_params(node_hover)
)

# Count labels on nodes (filtered by minimum node height for readability)
count_labels = (
    alt.Chart(nodes_df)
    .transform_filter(alt.datum.y2 - alt.datum.y >= 25)
    .transform_calculate(count_label="'' + datum.total")
    .mark_text(fontSize=18, fontWeight="bold", color="#FFFFFF", baseline="middle", align="center")
    .encode(x=alt.X("label_x:Q", scale=x_domain), y=alt.Y("label_y:Q", scale=y_domain), text="count_label:N")
)

# Side labels with net change indicators on the right (Wave 4)
label_data = []
for _, row in nodes_df.iterrows():
    y_mid = (row["y"] + row["y2"]) / 2
    if row["wave_idx"] == 0:
        label_data.append(
            {"x": row["x"] - 12, "y": y_mid, "text": f"{row['name']} ({int(row['total'])})", "align": "right"}
        )
    elif row["wave_idx"] == n_waves - 1:
        cat = row["name"]
        delta = wave_totals[n_waves - 1][cat] - wave_totals[0][cat]
        sign = "+" if delta > 0 else ""
        label_data.append(
            {
                "x": row["x2"] + 12,
                "y": y_mid,
                "text": f"{row['name']} ({int(row['total'])}) {sign}{delta}",
                "align": "left",
            }
        )

labels_df = pd.DataFrame(label_data)

left_labels = (
    alt.Chart(labels_df)
    .transform_filter(alt.datum.align == "right")
    .mark_text(fontSize=18, fontWeight="bold", color="#444444", align="right", baseline="middle")
    .encode(x=alt.X("x:Q", scale=x_domain), y=alt.Y("y:Q", scale=y_domain), text="text:N")
)

right_labels = (
    alt.Chart(labels_df)
    .transform_filter(alt.datum.align == "left")
    .mark_text(fontSize=18, fontWeight="bold", color="#444444", align="left", baseline="middle")
    .encode(x=alt.X("x:Q", scale=x_domain), y=alt.Y("y:Q", scale=y_domain), text="text:N")
)

# Wave column headers (positioned above the diagram)
max_node_y = max(
    node_positions[w][cat]["y"] + node_positions[w][cat]["height"] for w in range(n_waves) for cat in categories
)
header_y = max_node_y + 35
wave_header_data = [{"x": x_positions[i], "y": header_y, "text": waves[i]} for i in range(n_waves)]
wave_headers = (
    alt.Chart(pd.DataFrame(wave_header_data))
    .mark_text(fontSize=22, fontWeight="bold", color="#333333", baseline="bottom")
    .encode(x=alt.X("x:Q", scale=x_domain), y=alt.Y("y:Q", scale=y_domain), text="text:N")
)

# Trend annotation (positioned near bottom, close to legend)
trend_data = [
    {"x": width / 2, "y": 18, "text": "Polarization trend: extreme sentiments grow while moderate opinions decline"}
]
trend_annotation = (
    alt.Chart(pd.DataFrame(trend_data))
    .mark_text(fontSize=18, fontStyle="italic", color="#666666", baseline="top", align="center")
    .encode(x=alt.X("x:Q", scale=x_domain), y=alt.Y("y:Q", scale=y_domain), text="text:N")
)

# Light background bands behind each wave column for visual depth
band_width = 60
band_data = []
for i in range(n_waves):
    band_data.append(
        {
            "x": x_positions[i] - band_width,
            "x2": x_positions[i] + band_width,
            "y": top_margin - 20,
            "y2": max_node_y + 10,
        }
    )
wave_bands = (
    alt.Chart(pd.DataFrame(band_data))
    .mark_rect(color="#EAEEF2", opacity=0.5, cornerRadius=8)
    .encode(x=alt.X("x:Q", scale=x_domain, axis=None), x2="x2:Q", y=alt.Y("y:Q", scale=y_domain, axis=None), y2="y2:Q")
)

# Combine all layers
chart = (
    alt.layer(
        wave_bands,
        change_chart,
        stable_chart,
        nodes_chart,
        count_labels,
        left_labels,
        right_labels,
        wave_headers,
        trend_annotation,
    )
    .properties(
        width=width,
        height=height,
        title=alt.Title(
            text="alluvial-opinion-flow · altair · pyplots.ai",
            subtitle="Employee Engagement Survey — 1,000 Staff Quarterly Sentiment Tracking",
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#888888",
            anchor="middle",
            color="#333333",
            offset=20,
        ),
    )
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
