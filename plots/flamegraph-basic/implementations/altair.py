""" pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: altair 6.0.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-14
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - simulated CPU profiling stacks with realistic function names
np.random.seed(42)

stacks = {
    "main": 500,
    "main;request_handler": 420,
    "main;request_handler;parse_headers": 80,
    "main;request_handler;parse_headers;decode_utf8": 45,
    "main;request_handler;parse_headers;validate_fields": 30,
    "main;request_handler;route_dispatch": 60,
    "main;request_handler;route_dispatch;regex_match": 40,
    "main;request_handler;process_request": 250,
    "main;request_handler;process_request;db_query": 140,
    "main;request_handler;process_request;db_query;connect_pool": 25,
    "main;request_handler;process_request;db_query;execute_sql": 90,
    "main;request_handler;process_request;db_query;execute_sql;parse_query": 35,
    "main;request_handler;process_request;db_query;execute_sql;fetch_rows": 45,
    "main;request_handler;process_request;db_query;serialize": 20,
    "main;request_handler;process_request;template_render": 80,
    "main;request_handler;process_request;template_render;compile_template": 30,
    "main;request_handler;process_request;template_render;render_html": 45,
    "main;request_handler;process_request;json_encode": 25,
    "main;request_handler;send_response": 25,
    "main;request_handler;send_response;compress_gzip": 18,
    "main;gc_collect": 50,
    "main;gc_collect;mark_sweep": 35,
    "main;gc_collect;compact_heap": 12,
    "main;logger": 25,
    "main;logger;format_message": 15,
    "main;logger;write_file": 8,
}

# Build flamegraph rectangles: compute x-position and width for each frame at each depth
# For each depth level, children are placed left-to-right within their parent's span
total_samples = stacks["main"]

# Parse stacks into a tree structure to compute positions
records = []


# Process stacks by building position map
# For each stack, parent defines the x-range, children fill it left to right
positions = {}
positions["main"] = (0, total_samples)

# Group stacks by depth
stacks_by_depth = {}
for stack_path, value in stacks.items():
    depth = stack_path.count(";")
    if depth not in stacks_by_depth:
        stacks_by_depth[depth] = []
    stacks_by_depth[depth].append((stack_path, value))

# Sort children within each parent by their value (largest first for better layout)
for depth in sorted(stacks_by_depth.keys()):
    if depth == 0:
        for stack_path, value in stacks_by_depth[depth]:
            positions[stack_path] = (0, value)
            func_name = stack_path.split(";")[-1]
            records.append(
                {
                    "x": 0,
                    "x2": value,
                    "depth": depth,
                    "function": func_name,
                    "samples": value,
                    "stack": stack_path,
                    "width": value,
                }
            )
        continue

    # Group by parent
    parent_children = {}
    for stack_path, value in stacks_by_depth[depth]:
        parent = ";".join(stack_path.split(";")[:-1])
        if parent not in parent_children:
            parent_children[parent] = []
        parent_children[parent].append((stack_path, value))

    for parent, children in parent_children.items():
        if parent not in positions:
            continue
        parent_x, parent_x2 = positions[parent]
        # Sort children by value descending for a visually pleasing layout
        children.sort(key=lambda c: c[1], reverse=True)
        current_x = parent_x
        for stack_path, value in children:
            positions[stack_path] = (current_x, current_x + value)
            func_name = stack_path.split(";")[-1]
            records.append(
                {
                    "x": current_x,
                    "x2": current_x + value,
                    "depth": depth,
                    "function": func_name,
                    "samples": value,
                    "stack": stack_path,
                    "width": value,
                }
            )
            current_x += value

df = pd.DataFrame(records)
df["pct"] = (df["samples"] / total_samples * 100).round(1)
df["label"] = df.apply(lambda r: r["function"] if r["width"] / total_samples > 0.06 else "", axis=1)

# Warm flame color palette mapped to depth
max_depth = df["depth"].max()
warm_colors = ["#FFE066", "#FFD033", "#FFAA00", "#FF8800", "#FF6600", "#E64A19", "#D32F2F"]

df["color_val"] = df["depth"] + np.random.uniform(-0.3, 0.3, len(df))

# Plot
alt.data_transformers.disable_max_rows()

bars = (
    alt.Chart(df)
    .mark_rect(stroke="#FFFFFF", strokeWidth=0.5, cornerRadius=2)
    .encode(
        x=alt.X("x:Q", title="Samples", axis=alt.Axis(titleFontSize=22, labelFontSize=18)),
        x2="x2:Q",
        y=alt.Y("depth:O", title="Stack Depth", sort="descending", axis=alt.Axis(titleFontSize=22, labelFontSize=18)),
        color=alt.Color(
            "depth:Q",
            scale=alt.Scale(
                domain=[0, max_depth],
                range=["#FFE066", "#FFD033", "#FFAA00", "#FF8800", "#FF6600", "#E64A19", "#C62828"],
            ),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("function:N", title="Function"),
            alt.Tooltip("samples:Q", title="Samples"),
            alt.Tooltip("pct:Q", title="% Total", format=".1f"),
            alt.Tooltip("stack:N", title="Stack"),
        ],
    )
)

labels = (
    alt.Chart(df[df["label"] != ""])
    .mark_text(fontSize=14, color="#1a1a1a", fontWeight="bold", align="center", baseline="middle")
    .encode(x=alt.X("mid:Q"), y=alt.Y("depth:O", sort="descending"), text="label:N")
    .transform_calculate(mid="(datum.x + datum.x2) / 2")
)

chart = (
    (bars + labels)
    .interactive()
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "flamegraph-basic · altair · pyplots.ai",
            subtitle=["CPU profiling: 500 samples across web request handling stack"],
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#888888",
            anchor="start",
            offset=16,
        ),
        padding={"left": 20, "right": 20, "top": 20, "bottom": 20},
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False, domainColor="#cccccc")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
