""" pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-14
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure


# Data - Simulated CPU profiling data for a web server application
np.random.seed(42)

stack_data = [
    ("main", 1000),
    ("main;handle_request", 850),
    ("main;handle_request;parse_headers", 120),
    ("main;handle_request;authenticate", 200),
    ("main;handle_request;authenticate;verify_token", 140),
    ("main;handle_request;authenticate;verify_token;decode_jwt", 90),
    ("main;handle_request;authenticate;verify_token;check_expiry", 40),
    ("main;handle_request;authenticate;load_user", 50),
    ("main;handle_request;process_query", 400),
    ("main;handle_request;process_query;parse_sql", 60),
    ("main;handle_request;process_query;execute", 280),
    ("main;handle_request;process_query;execute;fetch_rows", 180),
    ("main;handle_request;process_query;execute;fetch_rows;read_index", 100),
    ("main;handle_request;process_query;execute;fetch_rows;deserialize", 70),
    ("main;handle_request;process_query;execute;apply_filter", 80),
    ("main;handle_request;process_query;format_result", 50),
    ("main;handle_request;send_response", 100),
    ("main;handle_request;send_response;serialize_json", 60),
    ("main;handle_request;send_response;compress", 30),
    ("main;gc_collect", 100),
    ("main;gc_collect;mark_phase", 55),
    ("main;gc_collect;sweep_phase", 40),
    ("main;log_metrics", 40),
]

# Build hierarchy from stack traces
nodes = {}
for stack_str, samples in stack_data:
    parts = stack_str.split(";")
    func_name = parts[-1]
    depth = len(parts) - 1
    nodes[stack_str] = {
        "name": func_name,
        "stack": stack_str,
        "samples": samples,
        "depth": depth,
        "parent": ";".join(parts[:-1]) if depth > 0 else None,
    }

# Find children for each node
children_map = {}
for key, node in nodes.items():
    parent = node["parent"]
    if parent not in children_map:
        children_map[parent] = []
    children_map[parent].append(key)

max_depth = max(n["depth"] for n in nodes.values())
total_samples = nodes["main"]["samples"]

# Warm color palette for flame graph (yellows -> oranges -> reds)
flame_colors = [
    "#E25822",
    "#E8692D",
    "#ED7A38",
    "#F28C43",
    "#F5A623",
    "#F7B733",
    "#F9C846",
    "#FBDA61",
    "#FCE77D",
    "#FEF3A2",
]


# Layout: bottom-to-top, width proportional to samples
def layout_flames(stack_key, x_start, x_end, rects):
    node = nodes[stack_key]
    depth = node["depth"]
    width_fraction = x_end - x_start

    color_idx = min(depth, len(flame_colors) - 1)
    rects.append(
        {
            "name": node["name"],
            "depth": depth,
            "x_start": x_start,
            "x_end": x_end,
            "samples": node["samples"],
            "color": flame_colors[color_idx],
        }
    )

    # Layout children sorted alphabetically (flame graph convention)
    child_keys = sorted(children_map.get(stack_key, []))
    if child_keys:
        current_x = x_start
        for ck in child_keys:
            child_samples = nodes[ck]["samples"]
            child_width = width_fraction * (child_samples / node["samples"])
            layout_flames(ck, current_x, current_x + child_width, rects)
            current_x += child_width


rects = []
layout_flames("main", 0, 100, rects)

# Prepare data for Bokeh
x_centers = [(r["x_start"] + r["x_end"]) / 2 for r in rects]
y_centers = [r["depth"] + 0.5 for r in rects]
widths = [r["x_end"] - r["x_start"] for r in rects]
heights = [0.92 for _ in rects]
colors = [r["color"] for r in rects]
names = [r["name"] for r in rects]
samples = [r["samples"] for r in rects]

source = ColumnDataSource(
    data={
        "x": x_centers,
        "y": y_centers,
        "width": widths,
        "height": heights,
        "color": colors,
        "name": names,
        "samples": samples,
    }
)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="CPU Profile · flamegraph-basic · bokeh · pyplots.ai",
    x_range=(-2, 102),
    y_range=(-0.3, max_depth + 1.5),
    tools="",
    toolbar_location=None,
)

p.rect(
    x="x",
    y="y",
    width="width",
    height="height",
    source=source,
    fill_color="color",
    line_color="white",
    line_width=2,
    fill_alpha=0.92,
)

# Add function name labels inside bars when wide enough
for r in rects:
    rect_width = r["x_end"] - r["x_start"]
    x_center = (r["x_start"] + r["x_end"]) / 2
    y_center = r["depth"] + 0.5

    if rect_width > 3:
        font_size = "22pt" if rect_width > 25 else ("18pt" if rect_width > 10 else "14pt")
        pct = r["samples"] / total_samples * 100
        label_text = r["name"]
        if rect_width > 12:
            label_text = f"{r['name']} ({pct:.1f}%)"

        label = Label(
            x=x_center,
            y=y_center,
            text=label_text,
            text_align="center",
            text_baseline="middle",
            text_font_size=font_size,
            text_color="#1a1a1a",
        )
        p.add_layout(label)

# Style
p.title.text_font_size = "36pt"
p.title.align = "center"

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

p.outline_line_color = None
p.background_fill_color = "#FFFFFF"
p.border_fill_color = "#FFFFFF"

# Save
export_png(p, filename="plot.png")
output_file("plot.html", title="flamegraph-basic · bokeh · pyplots.ai")
save(p)
