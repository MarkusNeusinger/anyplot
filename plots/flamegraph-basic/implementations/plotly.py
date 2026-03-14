""" pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: plotly 6.6.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-14
"""

import numpy as np
import plotly.graph_objects as go


np.random.seed(42)

# Data - Simulated CPU profiling data with hierarchical call stacks
# Format: (stack_path, samples) where stack_path is semicolon-delimited
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

# Build hierarchical structure: compute inclusive sample counts (self + children)
stack_self_samples = {}
for stack, samples in raw_stacks:
    stack_self_samples[stack] = samples

# Collect all unique stacks including intermediates
all_stacks = set()
for stack, _ in raw_stacks:
    parts = stack.split(";")
    for i in range(len(parts)):
        all_stacks.add(";".join(parts[: i + 1]))

# Calculate inclusive values (self + all descendants)
inclusive = {}
for stack in all_stacks:
    total = stack_self_samples.get(stack, 0)
    for other_stack, samples in stack_self_samples.items():
        if other_stack.startswith(stack + ";") and samples > 0:
            total += samples
    inclusive[stack] = total

# Build flame graph rectangles
# Each bar: x_start, width, depth, function_name, inclusive_samples
bars = []

# Sort children alphabetically at each level (flame graph convention)
children_map = {}
for stack in all_stacks:
    parts = stack.split(";")
    if len(parts) > 1:
        parent = ";".join(parts[:-1])
        if parent not in children_map:
            children_map[parent] = []
        children_map[parent].append(stack)

for parent in children_map:
    children_map[parent].sort(key=lambda s: s.split(";")[-1])

# Assign x positions using DFS
total_samples = inclusive["main"]
x_positions = {}


def assign_positions(stack, x_start):
    width = inclusive[stack] / total_samples
    x_positions[stack] = (x_start, width)
    depth = len(stack.split(";")) - 1
    func_name = stack.split(";")[-1]
    bars.append((x_start, width, depth, func_name, inclusive[stack], stack))

    if stack in children_map:
        child_x = x_start
        for child in children_map[stack]:
            assign_positions(child, child_x)
            child_x += inclusive[child] / total_samples


assign_positions("main", 0.0)

# Warm color palette for flame graph aesthetic
warm_colors = [
    "#FFE066",
    "#FFD54F",
    "#FFCA28",
    "#FFC107",
    "#FFB300",
    "#FFA726",
    "#FF9800",
    "#FB8C00",
    "#F57C00",
    "#EF6C00",
    "#FF7043",
    "#F4511E",
    "#E64A19",
    "#D84315",
    "#BF360C",
    "#EF5350",
    "#E53935",
    "#D32F2F",
    "#C62828",
]

# Assign colors based on function name hash for consistency
color_map = {}
for bar in bars:
    func = bar[3]
    if func not in color_map:
        idx = hash(func) % len(warm_colors)
        color_map[func] = warm_colors[idx]

# Plot
fig = go.Figure()

max_depth = max(b[2] for b in bars)
bar_height = 0.85

for x_start, width, depth, func_name, samples, stack in bars:
    color = color_map[func_name]

    fig.add_trace(
        go.Bar(
            x=[width],
            y=[depth],
            base=[x_start],
            orientation="h",
            marker=dict(color=color, line=dict(color="white", width=0.5)),
            width=bar_height,
            showlegend=False,
            hovertemplate=(
                f"<b>{func_name}</b><br>Stack: {stack}<br>Samples: {samples} ({width * 100:.1f}%)<extra></extra>"
            ),
        )
    )

    # Add function name label if bar is wide enough
    if width > 0.06:
        display_text = func_name
        if width < 0.12:
            display_text = func_name[:10] + "..." if len(func_name) > 10 else func_name

        fig.add_annotation(
            x=x_start + width / 2,
            y=depth,
            text=display_text,
            showarrow=False,
            font=dict(size=14, color="#1a1a1a"),
            xanchor="center",
            yanchor="middle",
        )

# Style
fig.update_layout(
    title=dict(text="flamegraph-basic · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    template="plotly_white",
    barmode="overlay",
    xaxis=dict(
        title=dict(text="Proportion of Total Samples", font=dict(size=22)),
        tickfont=dict(size=16),
        range=[0, 1],
        tickformat=".0%",
        showgrid=False,
    ),
    yaxis=dict(
        title=dict(text="Stack Depth", font=dict(size=22)),
        tickfont=dict(size=16),
        dtick=1,
        range=[-0.5, max_depth + 0.5],
        showgrid=False,
    ),
    margin=dict(t=100, l=80, r=40, b=80),
    plot_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
