"""pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: plotly 6.6.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-14
"""

import numpy as np
import plotly.graph_objects as go


np.random.seed(42)

# Data - Simulated CPU profiling data with hierarchical call stacks
# Format: (stack_path, self_samples)
raw_stacks = [
    ("main", 0),
    ("main;process_request", 0),
    ("main;process_request;parse_headers", 120),
    ("main;process_request;parse_headers;validate_encoding", 45),
    ("main;process_request;parse_body", 80),
    ("main;process_request;parse_body;decode_json", 60),
    ("main;process_request;parse_body;decode_json;alloc_buffer", 25),
    ("main;process_request;route_handler", 0),
    ("main;process_request;route_handler;auth_check", 90),
    ("main;process_request;route_handler;auth_check;verify_token", 70),
    ("main;process_request;route_handler;auth_check;verify_token;decrypt", 55),
    ("main;process_request;route_handler;auth_check;load_session", 40),
    ("main;process_request;route_handler;query_db", 0),
    ("main;process_request;route_handler;query_db;connect", 30),
    ("main;process_request;route_handler;query_db;execute_sql", 150),
    ("main;process_request;route_handler;query_db;execute_sql;optimize_plan", 85),
    ("main;process_request;route_handler;query_db;execute_sql;fetch_rows", 110),
    ("main;process_request;route_handler;query_db;execute_sql;fetch_rows;deserialize", 65),
    ("main;process_request;route_handler;render_template", 95),
    ("main;process_request;route_handler;render_template;compile", 50),
    ("main;process_request;route_handler;render_template;escape_html", 35),
    ("main;process_request;send_response", 0),
    ("main;process_request;send_response;compress", 75),
    ("main;process_request;send_response;write_socket", 55),
    ("main;gc_collect", 40),
    ("main;gc_collect;mark_sweep", 30),
    ("main;gc_collect;compact_heap", 20),
    ("main;log_metrics", 25),
    ("main;log_metrics;serialize", 15),
]

# Build lookup of self samples
stack_self = dict(raw_stacks)

# Collect all unique stacks including intermediates
all_stacks = set()
for stack, _ in raw_stacks:
    parts = stack.split(";")
    for i in range(len(parts)):
        all_stacks.add(";".join(parts[: i + 1]))

# Calculate inclusive values (self + all descendants)
inclusive = {}
for stack in all_stacks:
    total = stack_self.get(stack, 0)
    prefix = stack + ";"
    for other, samples in stack_self.items():
        if other.startswith(prefix) and samples > 0:
            total += samples
    inclusive[stack] = total

total_samples = inclusive["main"]

# Build children map and sort alphabetically
children_map = {}
for stack in all_stacks:
    parts = stack.split(";")
    if len(parts) > 1:
        parent = ";".join(parts[:-1])
        children_map.setdefault(parent, []).append(stack)

for parent in children_map:
    children_map[parent].sort(key=lambda s: s.split(";")[-1])

# Assign x positions iteratively using a stack (no recursion)
bars = []
work_stack = [("main", 0.0)]
while work_stack:
    stack, x_start = work_stack.pop()
    width = inclusive[stack] / total_samples
    depth = stack.count(";")
    func_name = stack.split(";")[-1]
    bars.append((x_start, width, depth, func_name, inclusive[stack], stack))
    if stack in children_map:
        child_x = x_start
        for child in reversed(children_map[stack]):
            child_width = inclusive[child] / total_samples
            work_stack.append((child, child_x))
            child_x += child_width

# Identify the hot path (widest bar at each depth)
hot_path_stacks = set()
depth_bars = {}
for _, _, depth, _, samples, stack in bars:
    if depth not in depth_bars or samples > depth_bars[depth][1]:
        depth_bars[depth] = (stack, samples)
for stack, _ in depth_bars.values():
    hot_path_stacks.add(stack)

# Color palette: warm tones with varied saturation for differentiation
# Hot path bars get deeper, more saturated reds; others get lighter warm tones
hot_colors = ["#D32F2F", "#C62828", "#B71C1C", "#E53935", "#EF5350", "#F44336", "#D50000", "#FF1744"]
warm_colors = [
    "#FFCC80",
    "#FFE0B2",
    "#FFD180",
    "#FFE57F",
    "#FFF176",
    "#FFD54F",
    "#FFAB40",
    "#FFB74D",
    "#FFCC02",
    "#FFE082",
    "#F0E68C",
    "#FAFAD2",
    "#FFD700",
    "#F5DEB3",
    "#FFDAB9",
]

color_map = {}
for bar in bars:
    func = bar[3]
    stack = bar[5]
    if func not in color_map:
        if stack in hot_path_stacks:
            idx = hash(func) % len(hot_colors)
            color_map[func] = hot_colors[idx]
        else:
            idx = hash(func) % len(warm_colors)
            color_map[func] = warm_colors[idx]

max_depth = max(b[2] for b in bars)

# Group bars by depth to reduce trace count
depth_groups = {}
for x_start, width, depth, func_name, samples, stack in bars:
    depth_groups.setdefault(depth, []).append((x_start, width, func_name, samples, stack))

# Plot
fig = go.Figure()

bar_height = 0.82

for depth in sorted(depth_groups.keys()):
    group = depth_groups[depth]
    for x_start, width, func_name, samples, stack in group:
        color = color_map[func_name]
        is_hot = stack in hot_path_stacks
        border_color = "#B71C1C" if is_hot else "rgba(255,255,255,0.8)"
        border_width = 1.5 if is_hot else 0.5

        fig.add_trace(
            go.Bar(
                x=[width],
                y=[depth],
                base=[x_start],
                orientation="h",
                marker={"color": color, "line": {"color": border_color, "width": border_width}},
                width=bar_height,
                showlegend=False,
                hovertemplate=(
                    f"<b>{func_name}</b><br>Stack: {stack}<br>Samples: {samples} ({width * 100:.1f}%)<extra></extra>"
                ),
            )
        )

# Add function name labels
for x_start, width, depth, func_name, _samples, stack in bars:
    is_hot = stack in hot_path_stacks
    if width > 0.05:
        display_text = func_name
        if width < 0.10:
            max_chars = max(3, int(width * 120))
            display_text = func_name[:max_chars] + "…" if len(func_name) > max_chars else func_name

        font_color = "#FFFFFF" if is_hot else "#2E2E2E"

        fig.add_annotation(
            x=x_start + width / 2,
            y=depth,
            text=f"<b>{display_text}</b>" if is_hot else display_text,
            showarrow=False,
            font={"size": 16, "color": font_color, "family": "Consolas, Monaco, monospace"},
            xanchor="center",
            yanchor="middle",
        )

# Add hot path indicator annotation
fig.add_annotation(
    x=0.99,
    y=max_depth + 0.35,
    text="<b>■</b> Hot path (most samples)",
    showarrow=False,
    font={"size": 14, "color": "#B71C1C", "family": "Consolas, Monaco, monospace"},
    xanchor="right",
    yanchor="bottom",
)

# Style
fig.update_layout(
    title={
        "text": "flamegraph-basic · plotly · pyplots.ai",
        "font": {"size": 28, "family": "Consolas, Monaco, monospace", "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    template="plotly_white",
    barmode="overlay",
    xaxis={
        "title": {"text": "Proportion of Total Samples", "font": {"size": 22}},
        "tickfont": {"size": 16},
        "range": [0, 1],
        "tickformat": ".0%",
        "showgrid": False,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Stack Depth", "font": {"size": 22}},
        "tickfont": {"size": 16},
        "dtick": 1,
        "range": [-0.5, max_depth + 0.7],
        "showgrid": False,
        "zeroline": False,
    },
    margin={"t": 100, "l": 80, "r": 50, "b": 80},
    plot_bgcolor="#FAFAFA",
    paper_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
