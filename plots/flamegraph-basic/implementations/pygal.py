"""pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: pygal 3.1.0 | Python 3.14.3
"""

import importlib
import sys
from collections import defaultdict


# Import pygal avoiding name collision with this file
_cwd = sys.path[0]
sys.path[:] = [p for p in sys.path if p != _cwd]
_pygal = importlib.import_module("pygal")
_Style = importlib.import_module("pygal.style").Style
sys.path.insert(0, _cwd)

# Data: Simulated CPU profiling stacks with sample counts
stacks = [
    ("main", 800),
    ("main;process_request", 600),
    ("main;process_request;parse_headers", 120),
    ("main;process_request;parse_headers;validate_utf8", 45),
    ("main;process_request;parse_headers;decode_base64", 55),
    ("main;process_request;route_dispatch", 180),
    ("main;process_request;route_dispatch;regex_match", 90),
    ("main;process_request;route_dispatch;lookup_handler", 70),
    ("main;process_request;execute_handler", 250),
    ("main;process_request;execute_handler;db_query", 140),
    ("main;process_request;execute_handler;db_query;connect_pool", 35),
    ("main;process_request;execute_handler;db_query;execute_sql", 80),
    ("main;process_request;execute_handler;db_query;fetch_rows", 20),
    ("main;process_request;execute_handler;serialize_json", 70),
    ("main;process_request;execute_handler;serialize_json;encode_utf8", 30),
    ("main;process_request;execute_handler;template_render", 30),
    ("main;process_request;send_response", 40),
    ("main;process_request;send_response;compress_gzip", 25),
    ("main;gc_collect", 80),
    ("main;gc_collect;mark_sweep", 55),
    ("main;gc_collect;compact_heap", 20),
    ("main;log_metrics", 60),
    ("main;log_metrics;format_json", 30),
    ("main;log_metrics;write_buffer", 25),
    ("main;idle_wait", 50),
]

total_samples = 800

# Build tree structure from stack traces
tree = {}
for stack_path, samples in stacks:
    parts = stack_path.split(";")
    node = tree
    for part in parts:
        if part not in node:
            node[part] = {"_samples": 0}
        node = node[part]
    node["_samples"] = samples

# BFS to compute rectangles: (depth, x_start_frac, width_frac, label, samples)
rectangles = []
queue = [(tree, 0, 0.0)]
while queue:
    current_node, depth, x_offset = queue.pop(0)
    for name in sorted(current_node.keys()):
        if name.startswith("_"):
            continue
        child = current_node[name]
        samples = child.get("_samples", 0)
        if samples == 0:
            continue
        w = samples / total_samples
        rectangles.append((depth, x_offset, w, name, samples))
        child_x = x_offset
        for child_name in sorted(child.keys()):
            if child_name.startswith("_"):
                continue
            grandchild = child[child_name]
            gs = grandchild.get("_samples", 0)
            if gs > 0:
                queue.append(({child_name: grandchild}, depth + 1, child_x))
                child_x += gs / total_samples
        x_offset += w

# Group rectangles by depth level
depth_rects = defaultdict(list)
for depth, x_frac, w_frac, label, samples in rectangles:
    depth_rects[depth].append((x_frac, w_frac, label, samples))

for d in depth_rects:
    depth_rects[d].sort()

max_depth = max(depth_rects.keys())
num_levels = max_depth + 1

# Build ordered segments per depth with spacers for alignment
all_segments = []
for d in range(num_levels):
    segments = []
    rects = depth_rects.get(d, [])
    current_x = 0.0
    for x_frac, w_frac, label, samples in rects:
        gap = x_frac - current_x
        if gap > 0.001:
            segments.append((gap * total_samples, "", True))
        segments.append((samples, label, False))
        current_x = x_frac + w_frac
    all_segments.append(segments)

max_segs = max(len(s) for s in all_segments)

# Warm flame color palette
flame_colors = [
    "#fee090",
    "#fdae61",
    "#f46d43",
    "#d73027",
    "#e8853a",
    "#fb9a29",
    "#fdd49e",
    "#fc8d59",
    "#ef6548",
    "#d7301f",
    "#f7cb4d",
    "#e67e22",
    "#f4a460",
    "#e06c47",
]

# pygal style with warm flame aesthetic
custom_style = _Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#cccccc",
    colors=tuple(flame_colors),
    title_font_size=48,
    label_font_size=24,
    major_label_font_size=22,
    legend_font_size=16,
    value_font_size=20,
    value_label_font_size=18,
    font_family="monospace",
    tooltip_font_size=20,
)

# Create flame graph using pygal HorizontalStackedBar
chart = _pygal.HorizontalStackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="flamegraph-basic · pygal · pyplots.ai",
    x_title="Samples",
    y_title="Call Stack Depth",
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    print_values=False,
    print_labels=True,
    spacing=2,
    rounded_bars=3,
    tooltip_border_radius=5,
    margin_top=40,
    margin_bottom=60,
    margin_right=80,
)

# Row labels: depth levels (pygal renders last label at top, so natural order
# places root/depth 0 at bottom)
chart.x_labels = [f"Depth {d}" for d in range(num_levels)]

# Add series — one per column position across depth levels
for col in range(max_segs):
    values = []
    for d in range(num_levels):
        segs = all_segments[d]
        if col < len(segs):
            value, label, is_spacer = segs[col]
            if is_spacer:
                values.append({"value": value, "color": "white", "style": "stroke: white; stroke-width: 0"})
            else:
                color_idx = hash(label) % len(flame_colors)
                display = f"{label} ({value})" if value >= 50 else label
                values.append(
                    {
                        "value": value,
                        "color": flame_colors[color_idx],
                        "label": display,
                        "style": f"stroke: white; stroke-width: 1.5; fill: {flame_colors[color_idx]}",
                    }
                )
        else:
            values.append(None)
    chart.add("", values)

# Render to PNG and interactive HTML
chart.render_to_png("plot.png")

svg_content = chart.render(is_unicode=True)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>flamegraph-basic - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {svg_content}
    </figure>
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as fout:
    fout.write(html_content)
