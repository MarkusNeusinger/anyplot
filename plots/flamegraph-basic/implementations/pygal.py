"""pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-14
"""

import importlib
import sys

import numpy as np


# Import pygal avoiding name collision
_cwd = sys.path[0]
sys.path[:] = [p for p in sys.path if p != _cwd]
_pygal = importlib.import_module("pygal")
_Style = importlib.import_module("pygal.style").Style
_cairosvg = importlib.import_module("cairosvg")
sys.path.insert(0, _cwd)

# Data: Simulated CPU profiling stacks with sample counts
np.random.seed(42)

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

# Build flame graph structure: for each depth level, compute the x-offset and width
# of each frame based on its position among siblings under the same parent
total_samples = max(s[1] for s in stacks if ";" not in s[0])

# Parse stacks into a tree structure using nested dicts
tree = {}
for stack_path, samples in stacks:
    parts = stack_path.split(";")
    node = tree
    for part in parts:
        if part not in node:
            node[part] = {"_samples": 0, "_children": {}}
        node = node[part]
    node["_samples"] = samples
    if "_children" not in node:
        node["_children"] = {}

# Flatten tree into rectangles: (depth, x_start, width, label, samples)
# x_start and width are in fraction of total_samples
rectangles = []
stack_queue = [(tree, 0, 0.0)]
while stack_queue:
    current_node, depth, x_offset = stack_queue.pop(0)
    for name in sorted(current_node.keys()):
        if name.startswith("_"):
            continue
        child = current_node[name]
        samples = child.get("_samples", 0)
        if samples == 0:
            continue
        w = samples / total_samples
        rectangles.append((depth, x_offset, w, name, samples))
        # Queue children
        child_x = x_offset
        for child_name in sorted(child.keys()):
            if child_name.startswith("_"):
                continue
            grandchild = child[child_name]
            gs = grandchild.get("_samples", 0)
            if gs > 0:
                stack_queue.append(({child_name: grandchild}, depth + 1, child_x))
                child_x += gs / total_samples
        x_offset += w

# Chart dimensions
W, H = 4800, 2700
margin_top = 180
margin_bottom = 120
margin_left = 180
margin_right = 120

plot_w = W - margin_left - margin_right
plot_h = H - margin_top - margin_bottom

max_depth = max(r[0] for r in rectangles)
num_levels = max_depth + 1
bar_gap = 6
bar_height = (plot_h - bar_gap * num_levels) / num_levels

# Warm color palette (yellows, oranges, reds) for flame graph aesthetic
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

# Build SVG
svg_parts = []
svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
svg_parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="white"/>')

# Title
svg_parts.append(
    f'<text x="{W / 2}" y="{70}" text-anchor="middle" fill="#333333" '
    f'style="font-size:48px;font-weight:600;font-family:sans-serif">'
    f"flamegraph-basic \u00b7 pygal \u00b7 pyplots.ai</text>"
)

# Subtitle
svg_parts.append(
    f'<text x="{W / 2}" y="{120}" text-anchor="middle" fill="#666666" '
    f'style="font-size:28px;font-weight:400;font-family:sans-serif">'
    f"CPU profiling \u2014 {total_samples} samples \u2014 HTTP request processing</text>"
)

# Draw flame graph rectangles (bottom-to-top: root at bottom)
for depth, x_frac, w_frac, label, samples in rectangles:
    x = margin_left + x_frac * plot_w
    bar_w = w_frac * plot_w - 2
    y = H - margin_bottom - (depth + 1) * (bar_height + bar_gap)

    if bar_w < 1:
        continue

    # Assign color based on hash of function name for consistency
    color_idx = hash(label) % len(flame_colors)
    color = flame_colors[color_idx]

    # Rectangle
    svg_parts.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_height:.1f}" '
        f'fill="{color}" stroke="#ffffff" stroke-width="1" rx="3" ry="3"/>'
    )

    # Label inside bar if wide enough
    font_size = 28
    char_width = font_size * 0.62
    text_width_estimate = len(label) * char_width
    if bar_w > text_width_estimate + 30:
        text_x = x + bar_w / 2
        text_y = y + bar_height / 2 + font_size * 0.35
        display_text = f"{label} ({samples})"
        display_width = len(display_text) * char_width
        if bar_w > display_width + 30:
            text_label = display_text
        else:
            text_label = label
        svg_parts.append(
            f'<text x="{text_x:.1f}" y="{text_y:.1f}" text-anchor="middle" fill="#1a1a1a" '
            f'style="font-size:{font_size}px;font-weight:500;font-family:monospace">'
            f"{text_label}</text>"
        )

# Depth axis label
mid_y = (margin_top + H - margin_bottom) / 2
svg_parts.append(
    f'<text x="{margin_left - 80}" y="{mid_y:.0f}" text-anchor="middle" fill="#666666" '
    f'style="font-size:34px;font-weight:500;font-family:sans-serif" '
    f'transform="rotate(-90, {margin_left - 80}, {mid_y:.0f})">Call Stack Depth</text>'
)

svg_parts.append("</svg>")
svg_content = "\n".join(svg_parts)

# Save PNG
_cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to="plot.png", output_width=W, output_height=H)

# Save interactive HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>flamegraph-basic - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
        rect:hover {{ opacity: 0.8; cursor: pointer; }}
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
