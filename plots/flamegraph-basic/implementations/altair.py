""" pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-14
"""

import altair as alt
import pandas as pd


# Data - simulated CPU profiling stacks with realistic function names

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

# Identify the hottest code path (widest bar at each depth following the dominant branch)
max_depth = df["depth"].max()
hot_path_stacks = set()
current_stack = "main"
hot_path_stacks.add(current_stack)
for d in range(1, max_depth + 1):
    children = df[(df["depth"] == d) & (df["stack"].str.startswith(current_stack + ";"))]
    if not children.empty:
        hottest = children.loc[children["samples"].idxmax()]
        current_stack = hottest["stack"]
        hot_path_stacks.add(current_stack)

df["is_hot"] = df["stack"].isin(hot_path_stacks)
df["opacity_val"] = df["is_hot"].map({True: 1.0, False: 0.6})

# Plot
alt.data_transformers.disable_max_rows()

bars = (
    alt.Chart(df)
    .mark_rect(stroke="#FFFFFF", strokeWidth=0.5, cornerRadius=2)
    .encode(
        x=alt.X("x:Q", title="Samples (count)", axis=alt.Axis(titleFontSize=22, labelFontSize=18)),
        x2="x2:Q",
        y=alt.Y(
            "depth:O", title="Stack Depth (level)", sort="descending", axis=alt.Axis(titleFontSize=22, labelFontSize=18)
        ),
        color=alt.Color(
            "depth:Q",
            scale=alt.Scale(
                domain=[0, max_depth], range=["#FEEDDE", "#FDBE85", "#FD8D3C", "#E6550D", "#BD0026", "#7F0000"]
            ),
            legend=None,
        ),
        opacity=alt.Opacity("opacity_val:Q", legend=None, scale=alt.Scale(domain=[0.5, 1.0], range=[0.5, 1.0])),
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
    .mark_text(fontSize=16, color="#1a1a1a", fontWeight="bold", align="center", baseline="middle")
    .encode(x=alt.X("mid:Q"), y=alt.Y("depth:O", sort="descending"), text="label:N")
    .transform_calculate(mid="(datum.x + datum.x2) / 2")
)

# Highlight selection for interactive exploration (distinctive Altair feature)
highlight = alt.selection_point(on="pointerover", fields=["stack"], empty=False)

highlight_bars = (
    alt.Chart(df)
    .mark_rect(stroke="#333333", strokeWidth=2, cornerRadius=2)
    .encode(
        x="x:Q",
        x2="x2:Q",
        y=alt.Y("depth:O", sort="descending"),
        opacity=alt.condition(highlight, alt.value(1.0), alt.value(0)),
        color=alt.value("transparent"),
    )
    .add_params(highlight)
)

chart = (
    (bars + highlight_bars + labels)
    .interactive()
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "flamegraph-basic · altair · pyplots.ai",
            subtitle=[
                "CPU profiling: 500 samples | Hot path: main → request_handler → process_request → db_query → execute_sql",
                "Hover over bars to highlight | Scroll to zoom | Drag to pan",
            ],
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#666666",
            anchor="start",
            offset=16,
        ),
        padding={"left": 20, "right": 20, "top": 20, "bottom": 20},
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False, domainColor="#cccccc", labelColor="#444444", titleColor="#333333")
    .configure_title(subtitlePadding=6)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
