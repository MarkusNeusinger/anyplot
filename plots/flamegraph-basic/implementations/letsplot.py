""" pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-14
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_cartesian,
    element_rect,
    element_text,
    geom_rect,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Simulated CPU profiling stacks with sample counts
np.random.seed(42)

stacks = {
    "main": 950,
    "main;process_request": 800,
    "main;process_request;parse_input": 180,
    "main;process_request;parse_input;tokenize": 120,
    "main;process_request;parse_input;validate": 55,
    "main;process_request;compute": 420,
    "main;process_request;compute;matrix_mult": 210,
    "main;process_request;compute;matrix_mult;dot_product": 160,
    "main;process_request;compute;transform": 130,
    "main;process_request;compute;transform;normalize": 80,
    "main;process_request;compute;transform;scale": 45,
    "main;process_request;compute;aggregate": 70,
    "main;process_request;serialize": 190,
    "main;process_request;serialize;to_json": 110,
    "main;process_request;serialize;compress": 72,
    "main;init_config": 90,
    "main;init_config;load_file": 55,
    "main;init_config;parse_yaml": 30,
    "main;cleanup": 50,
    "main;cleanup;flush_cache": 35,
    "main;cleanup;close_conn": 12,
}

# Build flame graph rectangles from stack data
total_samples = stacks["main"]

# Gather children per parent to compute positions
children_map = {}
for stack_path, samples in stacks.items():
    parts = stack_path.split(";")
    if len(parts) > 1:
        parent = ";".join(parts[:-1])
        if parent not in children_map:
            children_map[parent] = []
        children_map[parent].append((stack_path, samples))

# Compute positions top-down from root
positions = {"main": (0.0, total_samples)}

stack_queue = ["main"]
while stack_queue:
    current = stack_queue.pop(0)
    parent_xmin, parent_xmax = positions[current]
    if current in children_map:
        kids = sorted(children_map[current], key=lambda x: x[0])
        child_total = sum(s for _, s in kids)
        parent_samples = stacks[current]
        self_time = parent_samples - child_total
        x_cursor = parent_xmin
        parent_width = parent_xmax - parent_xmin
        scale = parent_width / parent_samples
        if self_time > 0:
            x_cursor += self_time * scale * 0.5
        for child_path, child_samples in kids:
            child_width = child_samples * scale
            positions[child_path] = (x_cursor, x_cursor + child_width)
            x_cursor += child_width
            stack_queue.append(child_path)

# Identify the hottest code path (widest bar at each depth from root)
hot_path = set()
current_path = "main"
hot_path.add(current_path)
while current_path in children_map:
    kids = children_map[current_path]
    hottest = max(kids, key=lambda x: x[1])
    hot_path.add(hottest[0])
    current_path = hottest[0]

# Build rectangles - no vertical gaps between depth levels
records = []
max_depth = 0
for stack_path, samples in stacks.items():
    parts = stack_path.split(";")
    depth = len(parts) - 1
    max_depth = max(max_depth, depth)
    func_name = parts[-1]
    xmin, xmax = positions[stack_path]
    is_hot = stack_path in hot_path
    records.append(
        {
            "xmin": xmin,
            "xmax": xmax,
            "ymin": depth,
            "ymax": depth + 1.0,
            "func": func_name,
            "depth": depth,
            "samples": samples,
            "pct": round(samples / total_samples * 100, 1),
            "stack": stack_path,
            "is_hot": is_hot,
        }
    )

df = pd.DataFrame(records)

# Warm color palette with more distinct steps per depth
# Hot path bars get saturated, intense colors; others get muted tones
flame_hot = ["#FFD54F", "#FFB300", "#FB8C00", "#F4511E", "#E53935"]
flame_cool = ["#FFF9C4", "#FFE082", "#FFCC80", "#FFAB91", "#EF9A9A"]
df["color"] = df.apply(
    lambda r: (
        flame_hot[min(r["depth"], len(flame_hot) - 1)]
        if r["is_hot"]
        else flame_cool[min(r["depth"], len(flame_cool) - 1)]
    ),
    axis=1,
)

# Border color: hot path gets dark border for emphasis, others get subtle white
df["border_color"] = df["is_hot"].apply(lambda h: "#BF360C" if h else "#ffffff")

# Label: show function name only if bar is wide enough, with per-depth overlap check
min_label_width = total_samples * 0.07
df["label"] = df.apply(lambda r: r["func"] if (r["xmax"] - r["xmin"]) >= min_label_width else "", axis=1)

# Per-depth overlap detection: remove labels that would collide
for depth in df["depth"].unique():
    depth_mask = (df["depth"] == depth) & (df["label"] != "")
    depth_bars = df.loc[depth_mask].sort_values("xmin")
    if len(depth_bars) > 1:
        prev_xmax = -float("inf")
        for idx, row in depth_bars.iterrows():
            bar_center = (row["xmin"] + row["xmax"]) / 2
            half_label = len(row["func"]) * 4.5  # approximate char width in data units
            label_left = bar_center - half_label
            if label_left < prev_xmax:
                df.at[idx, "label"] = ""
            else:
                prev_xmax = bar_center + half_label

df["label_x"] = (df["xmin"] + df["xmax"]) / 2
df["label_y"] = (df["ymin"] + df["ymax"]) / 2

# Separate hot-path and non-hot-path for layered rendering
df_cool = df[~df["is_hot"]].copy()
df_hot = df[df["is_hot"]].copy()

# Depth separator lines for visual structure
depth_lines = pd.DataFrame(
    {
        "y": [float(d) for d in range(1, max_depth + 1)],
        "xstart": [0.0] * max_depth,
        "xend": [float(total_samples)] * max_depth,
    }
)

# Plot - layer hot path on top for visual emphasis
plot = (
    ggplot()
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="color"),
        data=df_cool,
        color="#ffffff",
        size=0.3,
        tooltips=layer_tooltips()
        .title("@func")
        .line("Samples: @samples")
        .line("Percentage: @pct%")
        .line("Stack: @stack"),
    )
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="color"),
        data=df_hot,
        color="#BF360C",
        size=1.0,
        tooltips=layer_tooltips()
        .title("@func")
        .line("Samples: @samples")
        .line("Percentage: @pct%")
        .line("Stack: @stack"),
    )
    + geom_segment(
        aes(x="xstart", xend="xend", y="y", yend="y"), data=depth_lines, color="#e0ddd5", size=0.3, alpha=0.5
    )
    + geom_text(
        aes(x="label_x", y="label_y", label="label"),
        data=df,
        size=12,
        color="#1a1a1a",
        fontface="bold",
        label_padding=0.15,
    )
    + scale_fill_identity()
    + scale_x_continuous(expand=[0.005, 0])
    + scale_y_continuous(expand=[0.02, 0])
    + coord_cartesian(ylim=[-0.1, max_depth + 1.15])
    + labs(title="flamegraph-basic · letsplot · pyplots.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=26, face="bold", color="#1a1a2e", hjust=0.5),
        plot_background=element_rect(fill="#f5f5f0", color="#f5f5f0"),
        plot_margin=[40, 30, 15, 30],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
