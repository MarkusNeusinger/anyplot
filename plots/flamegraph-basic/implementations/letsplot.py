""" pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-14
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_identity,
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
# Each stack frame gets: xmin, xmax, ymin, ymax, label, samples
total_samples = stacks["main"]

# Parse stacks into a tree structure to compute positions
# For each depth level, children are placed left-to-right within their parent's x-span
records = []

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

# Position children within each parent's x-span
stack_queue = ["main"]
while stack_queue:
    current = stack_queue.pop(0)
    parent_xmin, parent_xmax = positions[current]
    if current in children_map:
        # Sort children alphabetically for consistent layout
        kids = sorted(children_map[current], key=lambda x: x[0])
        # Calculate self-time for implicit gap
        child_total = sum(s for _, s in kids)
        parent_samples = stacks[current]
        self_time = parent_samples - child_total
        # Start children from left edge of parent
        x_cursor = parent_xmin
        # Distribute proportionally within parent's span
        parent_width = parent_xmax - parent_xmin
        scale = parent_width / parent_samples
        if self_time > 0:
            x_cursor += self_time * scale * 0.5  # Center children, self-time split
        for child_path, child_samples in kids:
            child_width = child_samples * scale
            positions[child_path] = (x_cursor, x_cursor + child_width)
            x_cursor += child_width
            stack_queue.append(child_path)

# Build rectangles
for stack_path, samples in stacks.items():
    parts = stack_path.split(";")
    depth = len(parts) - 1
    func_name = parts[-1]
    xmin, xmax = positions[stack_path]
    records.append(
        {
            "xmin": xmin,
            "xmax": xmax,
            "ymin": depth,
            "ymax": depth + 0.88,
            "func": func_name,
            "depth": depth,
            "samples": samples,
            "pct": round(samples / total_samples * 100, 1),
            "stack": stack_path,
        }
    )

df = pd.DataFrame(records)

# Warm color palette: map depth to flame colors (yellow -> orange -> red)
flame_colors = ["#FFF176", "#FFCA28", "#FFA726", "#FF7043", "#EF5350", "#E53935", "#C62828"]
df["color"] = df["depth"].apply(lambda d: flame_colors[min(d, len(flame_colors) - 1)])

# Label: show function name only if bar is wide enough
min_label_width = total_samples * 0.065
df["label"] = df.apply(lambda r: r["func"] if (r["xmax"] - r["xmin"]) >= min_label_width else "", axis=1)
df["label_x"] = (df["xmin"] + df["xmax"]) / 2
df["label_y"] = (df["ymin"] + df["ymax"]) / 2

# Plot
plot = (
    ggplot(df)
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="color"),
        color="#ffffff",
        size=0.4,
        tooltips=layer_tooltips()
        .title("@func")
        .line("Samples: @samples")
        .line("Percentage: @pct%")
        .line("Stack: @stack"),
    )
    + geom_text(aes(x="label_x", y="label_y", label="label"), size=11, color="#1a1a1a", fontface="bold")
    + scale_fill_identity()
    + labs(title="flamegraph-basic · letsplot · pyplots.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=26, face="bold", color="#1a1a2e", hjust=0.5),
        plot_background=element_rect(fill="#fafafa", color="#fafafa"),
        plot_margin=[40, 30, 30, 30],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
