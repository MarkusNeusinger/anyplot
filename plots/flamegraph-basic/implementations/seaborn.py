""" pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-14
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Configure seaborn style
sns.set_context("talk", font_scale=1.2)
sns.set_style("white")

# Warm flame color palette using seaborn's blend_palette
flame_colors = sns.blend_palette(["#FFE066", "#FFB347", "#FF6B35", "#E8352B", "#C41E3A"], n_colors=256, as_cmap=True)

# Data - simulated CPU profiling stacks with sample counts (~65 stack traces)

stacks = {
    "main": 950,
    # Depth 1
    "main;init_config": 50,
    "main;process_request": 600,
    "main;cleanup": 80,
    "main;log_metrics": 180,
    "main;health_check": 40,
    # Depth 2 - init_config
    "main;init_config;load_env": 25,
    "main;init_config;parse_args": 20,
    # Depth 2 - process_request
    "main;process_request;parse_headers": 80,
    "main;process_request;authenticate": 120,
    "main;process_request;handle_route": 350,
    "main;process_request;send_response": 30,
    "main;process_request;log_request": 15,
    # Depth 2 - cleanup
    "main;cleanup;close_connections": 45,
    "main;cleanup;flush_logs": 30,
    # Depth 2 - log_metrics
    "main;log_metrics;collect_stats": 90,
    "main;log_metrics;write_to_disk": 60,
    "main;log_metrics;aggregate": 25,
    # Depth 2 - health_check
    "main;health_check;ping_db": 20,
    "main;health_check;check_memory": 15,
    # Depth 3 - parse_headers
    "main;process_request;parse_headers;decode_utf8": 35,
    "main;process_request;parse_headers;validate_content_type": 30,
    "main;process_request;parse_headers;extract_cookies": 10,
    # Depth 3 - authenticate
    "main;process_request;authenticate;verify_token": 70,
    "main;process_request;authenticate;check_permissions": 40,
    # Depth 3 - handle_route
    "main;process_request;handle_route;query_database": 200,
    "main;process_request;handle_route;serialize_response": 90,
    "main;process_request;handle_route;compress": 40,
    "main;process_request;handle_route;cache_lookup": 15,
    # Depth 3 - send_response
    "main;process_request;send_response;write_headers": 15,
    "main;process_request;send_response;write_body": 10,
    # Depth 3 - collect_stats
    "main;log_metrics;collect_stats;cpu_usage": 40,
    "main;log_metrics;collect_stats;mem_usage": 35,
    "main;log_metrics;collect_stats;disk_io": 10,
    # Depth 3 - write_to_disk
    "main;log_metrics;write_to_disk;buffer_flush": 35,
    "main;log_metrics;write_to_disk;fsync": 20,
    # Depth 3 - aggregate
    "main;log_metrics;aggregate;compute_p99": 15,
    "main;log_metrics;aggregate;compute_mean": 8,
    # Depth 3 - close_connections
    "main;cleanup;close_connections;tcp_shutdown": 25,
    "main;cleanup;close_connections;release_pool": 15,
    # Depth 4 - verify_token
    "main;process_request;authenticate;verify_token;decode_jwt": 35,
    "main;process_request;authenticate;verify_token;check_expiry": 20,
    "main;process_request;authenticate;verify_token;validate_sig": 12,
    # Depth 4 - check_permissions
    "main;process_request;authenticate;check_permissions;load_acl": 22,
    "main;process_request;authenticate;check_permissions;match_role": 14,
    # Depth 4 - query_database
    "main;process_request;handle_route;query_database;build_sql": 50,
    "main;process_request;handle_route;query_database;execute": 120,
    "main;process_request;handle_route;query_database;fetch_rows": 25,
    # Depth 4 - serialize_response
    "main;process_request;handle_route;serialize_response;to_json": 70,
    "main;process_request;handle_route;serialize_response;validate_schema": 15,
    # Depth 4 - compress
    "main;process_request;handle_route;compress;gzip_encode": 30,
    "main;process_request;handle_route;compress;set_headers": 8,
    # Depth 4 - cpu_usage
    "main;log_metrics;collect_stats;cpu_usage;read_proc": 25,
    "main;log_metrics;collect_stats;cpu_usage;calc_percent": 12,
    # Depth 5 - execute
    "main;process_request;handle_route;query_database;execute;prepare_stmt": 40,
    "main;process_request;handle_route;query_database;execute;send_query": 55,
    "main;process_request;handle_route;query_database;execute;parse_result": 20,
    # Depth 5 - to_json
    "main;process_request;handle_route;serialize_response;to_json;encode_fields": 40,
    "main;process_request;handle_route;serialize_response;to_json;format_dates": 20,
    # Depth 5 - decode_jwt
    "main;process_request;authenticate;verify_token;decode_jwt;base64_decode": 18,
    "main;process_request;authenticate;verify_token;decode_jwt;parse_claims": 12,
    # Depth 6 - send_query
    "main;process_request;handle_route;query_database;execute;send_query;tcp_write": 30,
    "main;process_request;handle_route;query_database;execute;send_query;await_ack": 20,
}

# Build flame graph structure
total_samples = stacks["main"]

# Parse stacks into frames at each depth
frames = {}
for stack_path, samples in stacks.items():
    parts = stack_path.split(";")
    depth = len(parts) - 1
    if depth not in frames:
        frames[depth] = []
    frames[depth].append((stack_path, parts[-1], samples))

# Compute x-positions: children must be within parent's span
positions = {}
positions["main"] = (0, total_samples)

for depth in sorted(frames.keys()):
    if depth == 0:
        continue
    parent_children = {}
    for stack_path, func_name, samples in frames[depth]:
        parent_path = ";".join(stack_path.split(";")[:-1])
        if parent_path not in parent_children:
            parent_children[parent_path] = []
        parent_children[parent_path].append((stack_path, func_name, samples))

    for parent_path, children in parent_children.items():
        if parent_path not in positions:
            continue
        parent_x, _parent_w = positions[parent_path]
        children.sort(key=lambda c: c[1])
        current_x = parent_x
        for stack_path, _func_name, samples in children:
            positions[stack_path] = (current_x, samples)
            current_x += samples

# Build DataFrame for seaborn color mapping
records = []
for stack_path, (x_pos, width) in positions.items():
    depth = stack_path.count(";")
    func_name = stack_path.split(";")[-1]
    records.append(
        {
            "stack": stack_path,
            "function": func_name,
            "depth": depth,
            "x": x_pos,
            "width": width,
            "fraction": width / total_samples,
        }
    )
df = pd.DataFrame(records)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

bar_height = 0.85
max_depth = max(frames.keys())

for _, row in df.iterrows():
    func_name = row["function"]
    x_pos = row["x"]
    width = row["width"]
    depth = row["depth"]
    fraction = row["fraction"]

    # Color: use seaborn blend_palette - map by hash for variety within warm tones
    color_val = (hash(func_name) % 1000) / 1000.0
    color = flame_colors(0.15 + color_val * 0.7)

    rect = mpatches.FancyBboxPatch(
        (x_pos, depth),
        width,
        bar_height,
        boxstyle="round,pad=0,rounding_size=0.05",
        facecolor=color,
        edgecolor="white",
        linewidth=1.0,
    )
    ax.add_patch(rect)

    # Add label if bar is wide enough
    if fraction > 0.045:
        label = func_name
        if fraction > 0.08:
            pct = fraction * 100
            label = f"{func_name} ({pct:.0f}%)"

        # Improve text contrast: use white text on dark bars, dark on light
        r, g, b = color[:3]
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        text_color = "#ffffff" if luminance < 0.55 else "#2b2b2b"

        ax.text(
            x_pos + width / 2,
            depth + bar_height / 2,
            label,
            ha="center",
            va="center",
            fontsize=11 if fraction > 0.1 else 9,
            fontweight="bold" if fraction > 0.15 else "medium",
            color=text_color,
            clip_on=True,
        )

# Style
ax.set_xlim(-20, total_samples + 40)
ax.set_ylim(-0.3, max_depth + 1.2)
ax.set_xlabel("Samples", fontsize=20)
ax.set_ylabel("Stack Depth", fontsize=20)
ax.set_title("flamegraph-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)

# Set y-ticks to integer depths
ax.set_yticks(range(max_depth + 1))
ax.set_yticklabels([f"Depth {i}" for i in range(max_depth + 1)])

# Remove spines
sns.despine(ax=ax, top=True, right=True)

# Subtle x-axis grid only
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.yaxis.grid(False)

plt.tight_layout()

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
