"""pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-14
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Configure seaborn style
sns.set_context("talk", font_scale=1.2)
sns.set_style("white")

# Data - simulated CPU profiling stacks with sample counts
np.random.seed(42)

stacks = {
    "main": 950,
    "main;init_config": 50,
    "main;process_request": 600,
    "main;process_request;parse_headers": 80,
    "main;process_request;authenticate": 120,
    "main;process_request;authenticate;verify_token": 70,
    "main;process_request;authenticate;check_permissions": 40,
    "main;process_request;handle_route": 350,
    "main;process_request;handle_route;query_database": 200,
    "main;process_request;handle_route;query_database;build_sql": 50,
    "main;process_request;handle_route;query_database;execute": 120,
    "main;process_request;handle_route;query_database;fetch_rows": 25,
    "main;process_request;handle_route;serialize_response": 90,
    "main;process_request;handle_route;serialize_response;to_json": 70,
    "main;process_request;handle_route;compress": 40,
    "main;process_request;send_response": 30,
    "main;cleanup": 80,
    "main;cleanup;close_connections": 45,
    "main;cleanup;flush_logs": 30,
    "main;log_metrics": 180,
    "main;log_metrics;collect_stats": 90,
    "main;log_metrics;collect_stats;cpu_usage": 40,
    "main;log_metrics;collect_stats;mem_usage": 35,
    "main;log_metrics;write_to_disk": 60,
    "main;log_metrics;write_to_disk;buffer_flush": 35,
}

# Build flame graph structure
# For each depth level, compute the x-position and width of each frame
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
# Sort children alphabetically within each parent for consistent layout
positions = {}
positions["main"] = (0, total_samples)

for depth in sorted(frames.keys()):
    if depth == 0:
        continue
    # Group frames by parent
    parent_children = {}
    for stack_path, func_name, samples in frames[depth]:
        parent_path = ";".join(stack_path.split(";")[:-1])
        if parent_path not in parent_children:
            parent_children[parent_path] = []
        parent_children[parent_path].append((stack_path, func_name, samples))

    for parent_path, children in parent_children.items():
        if parent_path not in positions:
            continue
        parent_x, parent_w = positions[parent_path]
        # Sort children alphabetically for consistent layout
        children.sort(key=lambda c: c[1])
        current_x = parent_x
        for stack_path, _func_name, samples in children:
            positions[stack_path] = (current_x, samples)
            current_x += samples

# Warm color palette for flame graph aesthetic
flame_cmap = LinearSegmentedColormap.from_list("flame", ["#FFE066", "#FFB347", "#FF6B35", "#E8352B", "#C41E3A"])

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

bar_height = 0.85
max_depth = max(frames.keys())

for stack_path, (x_pos, width) in positions.items():
    depth = stack_path.count(";")
    func_name = stack_path.split(";")[-1]

    # Color based on a hash of function name for consistency
    color_val = (hash(func_name) % 1000) / 1000.0
    color = flame_cmap(0.15 + color_val * 0.7)

    # Draw rectangle
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
    bar_fraction = width / total_samples
    if bar_fraction > 0.04:
        label = func_name
        if bar_fraction > 0.08:
            pct = width / total_samples * 100
            label = f"{func_name} ({pct:.0f}%)"
        ax.text(
            x_pos + width / 2,
            depth + bar_height / 2,
            label,
            ha="center",
            va="center",
            fontsize=11 if bar_fraction > 0.1 else 9,
            fontweight="medium",
            color="#1a1a1a",
        )

# Style
ax.set_xlim(-5, total_samples + 5)
ax.set_ylim(-0.3, max_depth + 1.2)
ax.set_xlabel("Samples", fontsize=20)
ax.set_ylabel("Stack Depth", fontsize=20)
ax.set_title("flamegraph-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)

# Set y-ticks to integer depths
ax.set_yticks(range(max_depth + 1))
ax.set_yticklabels([f"Depth {i}" for i in range(max_depth + 1)])

# Remove spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Subtle x-axis grid only
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.yaxis.grid(False)

plt.tight_layout()

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
