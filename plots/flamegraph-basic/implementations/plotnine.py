""" pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-14
"""

import pandas as pd
from plotnine import (
    aes,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


# Data - simulated CPU profiling stacks (web server request handling)
stacks = {
    "main": 1000,
    "main;request_handler": 800,
    "main;request_handler;parse_headers": 150,
    "main;request_handler;parse_body": 120,
    "main;request_handler;parse_body;decode_json": 90,
    "main;request_handler;parse_body;validate_schema": 25,
    "main;request_handler;route_dispatch": 480,
    "main;request_handler;route_dispatch;auth_middleware": 100,
    "main;request_handler;route_dispatch;auth_middleware;verify_token": 70,
    "main;request_handler;route_dispatch;auth_middleware;check_permissions": 25,
    "main;request_handler;route_dispatch;query_database": 250,
    "main;request_handler;route_dispatch;query_database;build_query": 40,
    "main;request_handler;route_dispatch;query_database;execute_sql": 160,
    "main;request_handler;route_dispatch;query_database;execute_sql;fetch_rows": 100,
    "main;request_handler;route_dispatch;query_database;execute_sql;deserialize": 45,
    "main;request_handler;route_dispatch;query_database;cache_result": 35,
    "main;request_handler;route_dispatch;render_template": 110,
    "main;request_handler;route_dispatch;render_template;compile_template": 40,
    "main;request_handler;route_dispatch;render_template;apply_filters": 55,
    "main;request_handler;send_response": 40,
    "main;request_handler;send_response;compress_gzip": 30,
    "main;gc_collect": 80,
    "main;gc_collect;mark_sweep": 60,
    "main;gc_collect;compact_heap": 15,
    "main;logging": 100,
    "main;logging;format_message": 40,
    "main;logging;write_file": 50,
}

# Build flame graph rectangles from stack data
total_samples = stacks["main"]

# Group stacks by depth and compute positions
depth_children: dict[tuple[int, str | None], list[tuple[str, str, int]]] = {}
for stack_path, samples in stacks.items():
    parts = stack_path.split(";")
    depth = len(parts) - 1
    parent = ";".join(parts[:-1]) if depth > 0 else None
    func_name = parts[-1]
    depth_children.setdefault((depth, parent), []).append((func_name, stack_path, samples))

# Compute x positions level by level
positions: dict[str, tuple[int, int]] = {"main": (0, total_samples)}
for depth in range(1, 8):
    for (d, parent), children in sorted(depth_children.items()):
        if d != depth or parent not in positions:
            continue
        x_cursor = positions[parent][0]
        for _func_name, stack_path, samples in children:
            positions[stack_path] = (x_cursor, x_cursor + samples)
            x_cursor += samples

# Build dataframe — map sample count to color for data storytelling
records = []
for stack_path, (xmin, xmax) in positions.items():
    parts = stack_path.split(";")
    depth = len(parts) - 1
    func_name = parts[-1]
    samples = xmax - xmin
    width_frac = samples / total_samples

    records.append(
        {
            "xmin": xmin,
            "xmax": xmax,
            "ymin": depth - 0.45,
            "ymax": depth + 0.45,
            "depth": depth,
            "func": func_name,
            "samples": samples,
            "label": func_name if width_frac > 0.06 else "",
            "label_x": (xmin + xmax) / 2,
            "label_y": depth,
        }
    )

df = pd.DataFrame(records)

# Plot — use scale_fill_gradientn to map sample count to warm flame colors
# Higher sample counts = hotter (redder), lower = cooler (yellower)
plot = (
    ggplot(df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="samples"), color="white", size=0.3)
    + geom_text(aes(x="label_x", y="label_y", label="label"), size=7, color="#1a1a1a", fontweight="bold")
    + scale_fill_gradientn(
        colors=["#FFEB3B", "#FFC107", "#FF9800", "#FF5722", "#D32F2F"], name="Samples", breaks=[100, 500, 1000]
    )
    + scale_x_continuous(expand=(0, 0))
    + scale_y_continuous(expand=(0.02, 0.02))
    + labs(title="flamegraph-basic · plotnine · pyplots.ai")
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold", margin={"b": 15}),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="#1a1a1a", color="#1a1a1a"),
        legend_position="bottom",
        legend_direction="horizontal",
        legend_title=element_text(size=14, weight="bold"),
        legend_text=element_text(size=12),
        legend_key_width=120,
        legend_key_height=12,
        legend_margin={"t": 10},
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
