""" pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-14
"""

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Data - simulated CPU profiling stacks with sample counts
stacks = {
    "main": 950,
    "main;process_request": 800,
    "main;process_request;parse_input": 180,
    "main;process_request;parse_input;tokenize": 120,
    "main;process_request;parse_input;validate": 50,
    "main;process_request;compute": 450,
    "main;process_request;compute;matrix_multiply": 280,
    "main;process_request;compute;matrix_multiply;dot_product": 200,
    "main;process_request;compute;matrix_multiply;allocate_buffer": 60,
    "main;process_request;compute;transform": 130,
    "main;process_request;compute;transform;normalize": 80,
    "main;process_request;compute;transform;scale": 40,
    "main;process_request;send_response": 120,
    "main;process_request;send_response;serialize": 70,
    "main;process_request;send_response;write_socket": 40,
    "main;initialize": 100,
    "main;initialize;load_config": 55,
    "main;initialize;setup_logging": 35,
    "main;gc_collect": 40,
}

total_samples = stacks["main"]

# Build flame graph rectangles with parent offset tracking
positions = {"main": (0.0, total_samples)}
rects = []
parent_offsets = {}  # tracks current x offset for children of each parent

for stack_path, samples in stacks.items():
    parts = stack_path.split(";")
    depth = len(parts) - 1
    func_name = parts[-1]

    if depth == 0:
        rects.append((depth, func_name, 0.0, samples))
        continue

    parent = ";".join(parts[:-1])
    if parent not in positions:
        continue

    parent_x, _ = positions[parent]
    x_start = parent_offsets.get(parent, parent_x)
    positions[stack_path] = (x_start, samples)
    parent_offsets[parent] = x_start + samples
    rects.append((depth, func_name, x_start, samples))

# Warm color palette - color by proportion of total samples (hot path = hotter colors)
warm_colors = ["#FFF3B0", "#FFDD57", "#FFB627", "#FF9505", "#FF6700", "#E8430A", "#D62828"]
cmap = mcolors.LinearSegmentedColormap.from_list("flame", warm_colors, N=256)

# Plot using matplotlib Rectangle patches
fig, ax = plt.subplots(figsize=(16, 9))
fig.set_facecolor("#FAFAFA")
ax.set_facecolor("#FAFAFA")

bar_height = 0.88
max_depth = max(r[0] for r in rects)

for depth, func_name, x_start, width in rects:
    # Color mapped to proportion of total samples - wider bars get hotter colors
    proportion = width / total_samples
    color_val = np.clip(proportion * 2.5, 0.05, 1.0)
    color = cmap(color_val)

    # Use matplotlib FancyBboxPatch for rounded corners on wide bars
    rect = mpatches.FancyBboxPatch(
        (x_start, depth - bar_height / 2),
        width,
        bar_height,
        boxstyle=mpatches.BoxStyle.Round(pad=0, rounding_size=3),
        facecolor=color,
        edgecolor="white",
        linewidth=0.8,
    )
    ax.add_patch(rect)

    # Add function name label if bar is wide enough
    bar_fraction = width / total_samples
    if bar_fraction > 0.05:
        label = func_name
        # Add percentage on major bars for data storytelling
        if bar_fraction > 0.12:
            label = f"{func_name} ({bar_fraction:.0%})"
            fontsize = 14
            fontweight = "semibold"
        else:
            fontsize = 12
            fontweight = "medium"

        text_color = "#1a1a1a" if color_val < 0.7 else "#FFFFFF"
        ax.text(
            x_start + width / 2,
            depth,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight=fontweight,
            color=text_color,
            clip_on=True,
        )

# Style
ax.set_xlim(-5, total_samples + 5)
ax.set_ylim(-0.6, max_depth + 0.7)
ax.set_xlabel("CPU Samples", fontsize=20, labelpad=10)
ax.set_ylabel("Stack Depth", fontsize=20, labelpad=10)
ax.set_title("flamegraph-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)
ax.set_yticks(range(max_depth + 1))
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.6)
ax.spines["bottom"].set_linewidth(0.6)
ax.spines["left"].set_color("#888888")
ax.spines["bottom"].set_color("#888888")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
