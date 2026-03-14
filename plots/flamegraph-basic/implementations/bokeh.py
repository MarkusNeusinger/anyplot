""" pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-14
"""

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure


# Data - Simulated CPU profiling data for a web server application
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
total_samples = 1000
nodes = {}
children_map = {}
for stack_str, samples in stack_data:
    parts = stack_str.split(";")
    func_name = parts[-1]
    depth = len(parts) - 1
    parent_key = ";".join(parts[:-1]) if depth > 0 else None
    nodes[stack_str] = {"name": func_name, "samples": samples, "depth": depth, "parent": parent_key}
    if parent_key not in children_map:
        children_map[parent_key] = []
    children_map[parent_key].append(stack_str)

max_depth = max(n["depth"] for n in nodes.values())

# Layout flames iteratively using a stack (avoids recursive function for KISS)
rects = []
work_stack = [("main", 0.0, 100.0)]
while work_stack:
    stack_key, x_start, x_end = work_stack.pop()
    node = nodes[stack_key]
    depth = node["depth"]
    width_fraction = x_end - x_start

    # Color: blend from deep red (hot/wide) to pale yellow (cool/narrow)
    # based on sample proportion — hottest paths glow brightest
    heat = node["samples"] / total_samples
    r_val = int(200 + 55 * (1 - heat))
    g_val = int(70 + 180 * (1 - heat))
    b_val = int(20 + 60 * (1 - heat))
    color = f"#{r_val:02x}{g_val:02x}{b_val:02x}"

    pct = node["samples"] / total_samples * 100
    rects.append(
        {
            "name": node["name"],
            "depth": depth,
            "x_start": x_start,
            "x_end": x_end,
            "samples": node["samples"],
            "pct": f"{pct:.1f}%",
            "stack": stack_key,
            "color": color,
        }
    )

    # Layout children sorted alphabetically (flame graph convention)
    child_keys = sorted(children_map.get(stack_key, []), reverse=True)
    current_x = x_start
    for ck in child_keys:
        child_samples = nodes[ck]["samples"]
        child_width = width_fraction * (child_samples / node["samples"])
        work_stack.append((ck, current_x, current_x + child_width))
        current_x += child_width

# Prepare data for Bokeh
x_centers = [(r["x_start"] + r["x_end"]) / 2 for r in rects]
y_centers = [r["depth"] + 0.5 for r in rects]
widths = [r["x_end"] - r["x_start"] for r in rects]
heights = [0.92] * len(rects)
colors = [r["color"] for r in rects]
names = [r["name"] for r in rects]
samples_list = [r["samples"] for r in rects]
pcts = [r["pct"] for r in rects]
stacks = [r["stack"] for r in rects]

source = ColumnDataSource(
    data={
        "x": x_centers,
        "y": y_centers,
        "width": widths,
        "height": heights,
        "color": colors,
        "name": names,
        "samples": samples_list,
        "pct": pcts,
        "stack": stacks,
    }
)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="flamegraph-basic · bokeh · pyplots.ai",
    x_range=(-2, 102),
    y_range=(-0.3, max_depth + 1.5),
    tools="",
    toolbar_location=None,
)

bars = p.rect(
    x="x",
    y="y",
    width="width",
    height="height",
    source=source,
    fill_color="color",
    line_color="white",
    line_width=2,
    fill_alpha=0.95,
)

# HoverTool - Bokeh distinctive interactive feature
hover = HoverTool(
    renderers=[bars],
    tooltips=[("Function", "@name"), ("Samples", "@samples"), ("CPU %", "@pct"), ("Call Stack", "@stack")],
    point_policy="follow_mouse",
)
p.add_tools(hover)

# Add function name labels inside bars when wide enough
for r in rects:
    rect_width = r["x_end"] - r["x_start"]
    x_center = (r["x_start"] + r["x_end"]) / 2
    y_center = r["depth"] + 0.5

    if rect_width > 3:
        font_size = "22pt" if rect_width > 25 else ("18pt" if rect_width > 10 else "14pt")
        label_text = r["name"]
        if rect_width > 12:
            label_text = f"{r['name']} ({r['pct']})"

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
p.title.text_font_style = "bold"

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
