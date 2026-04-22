""" pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-14
"""

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
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

# Identify the hot path (widest child at each depth)
hot_path_stacks = {"main"}
current = "main"
while True:
    children = {
        k: v for k, v in stacks.items() if k.startswith(current + ";") and k.count(";") == current.count(";") + 1
    }
    if not children:
        break
    hottest = max(children, key=children.get)
    hot_path_stacks.add(hottest)
    current = hottest

# Build flame graph rectangles with parent offset tracking
positions = {"main": (0.0, total_samples)}
rects = []
parent_offsets = {}

for stack_path, samples in stacks.items():
    parts = stack_path.split(";")
    depth = len(parts) - 1
    func_name = parts[-1]
    is_hot = stack_path in hot_path_stacks

    if depth == 0:
        rects.append((depth, func_name, 0.0, samples, is_hot))
        continue

    parent = ";".join(parts[:-1])
    if parent not in positions:
        continue

    parent_x, _ = positions[parent]
    x_start = parent_offsets.get(parent, parent_x)
    positions[stack_path] = (x_start, samples)
    parent_offsets[parent] = x_start + samples
    rects.append((depth, func_name, x_start, samples, is_hot))

# Warm color palette with more dramatic range for hot vs cold distinction
warm_colors = ["#FEF9E7", "#FDE68A", "#FBBF24", "#F59E0B", "#EF6C00", "#D32F2F", "#B71C1C"]
cmap = mcolors.LinearSegmentedColormap.from_list("flame", warm_colors, N=256)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
fig.set_facecolor("#FAFAFA")
ax.set_facecolor("#FAFAFA")

bar_height = 0.88
max_depth = max(r[0] for r in rects)

for depth, func_name, x_start, width, _is_hot in rects:
    proportion = width / total_samples
    # More dramatic color mapping: cubic curve for stronger hot/cold contrast
    color_val = np.clip(proportion**0.6 * 1.8, 0.03, 1.0)
    color = cmap(color_val)

    rect = mpatches.FancyBboxPatch(
        (x_start, depth - bar_height / 2),
        width,
        bar_height,
        boxstyle=mpatches.BoxStyle.Round(pad=0, rounding_size=3),
        facecolor=color,
        edgecolor="white",
        linewidth=0.8,
        zorder=2,
    )
    ax.add_patch(rect)

    # Add function name label if bar is wide enough
    bar_fraction = width / total_samples
    if bar_fraction > 0.05:
        label = func_name
        if bar_fraction > 0.12:
            label = f"{func_name} ({bar_fraction:.0%})"
            fontsize = 15
            fontweight = "bold"
        else:
            fontsize = 14
            fontweight = "medium"

        text_color = "#1a1a1a" if color_val < 0.55 else "#FFFFFF"
        # Path effects for text readability on colored backgrounds
        path_effects = [pe.withStroke(linewidth=2.5, foreground="white" if color_val < 0.55 else "#00000044")]
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
            path_effects=path_effects,
            zorder=5,
        )

# Hot path annotation pointing to the deepest hot path bar
hot_leaf = max((r for r in rects if r[4]), key=lambda r: r[0])
leaf_cx = hot_leaf[2] + hot_leaf[3] / 2
ax.annotate(
    "  Hot path (CPU bottleneck)  ",
    xy=(leaf_cx, hot_leaf[0] + bar_height / 2 + 0.02),
    xytext=(leaf_cx + 250, hot_leaf[0] + 1.15),
    fontsize=13,
    fontweight="semibold",
    color="#B71C1C",
    ha="center",
    arrowprops={"arrowstyle": "-|>", "color": "#C62828", "lw": 1.5, "connectionstyle": "arc3,rad=0.25"},
    bbox={"boxstyle": "round,pad=0.35", "facecolor": "#FFF3E0", "edgecolor": "#E65100", "alpha": 0.92, "linewidth": 1.0},
    zorder=10,
)

# Style
ax.set_xlim(-10, total_samples + 15)
ax.set_ylim(-0.6, max_depth + 1.6)
ax.set_xlabel("CPU Samples", fontsize=20, labelpad=10)
ax.set_ylabel("Stack Depth", fontsize=20, labelpad=10)
ax.set_title("flamegraph-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=16, color="#333333")
ax.tick_params(axis="both", labelsize=16, colors="#555555")
ax.set_yticks(range(max_depth + 1))
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.6)
ax.spines["bottom"].set_linewidth(0.6)
ax.spines["left"].set_color("#888888")
ax.spines["bottom"].set_color("#888888")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
