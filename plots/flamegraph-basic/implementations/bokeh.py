""" pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-14
"""

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure


# Data - Simulated CPU profiling data for a web server application
# 55 unique stack traces covering realistic call hierarchies
stack_data = [
    ("main", 10000),
    ("main;handle_request", 8500),
    ("main;handle_request;parse_headers", 1200),
    ("main;handle_request;parse_headers;read_line", 700),
    ("main;handle_request;parse_headers;read_line;decode_utf8", 350),
    ("main;handle_request;parse_headers;read_line;strip_whitespace", 200),
    ("main;handle_request;parse_headers;validate_content_type", 300),
    ("main;handle_request;parse_headers;parse_cookies", 150),
    ("main;handle_request;authenticate", 2000),
    ("main;handle_request;authenticate;verify_token", 1400),
    ("main;handle_request;authenticate;verify_token;decode_jwt", 900),
    ("main;handle_request;authenticate;verify_token;decode_jwt;base64_decode", 500),
    ("main;handle_request;authenticate;verify_token;decode_jwt;verify_signature", 350),
    ("main;handle_request;authenticate;verify_token;check_expiry", 400),
    ("main;handle_request;authenticate;load_user", 500),
    ("main;handle_request;authenticate;load_user;query_cache", 300),
    ("main;handle_request;authenticate;load_user;query_db", 180),
    ("main;handle_request;process_query", 4000),
    ("main;handle_request;process_query;parse_sql", 600),
    ("main;handle_request;process_query;parse_sql;tokenize", 350),
    ("main;handle_request;process_query;parse_sql;build_ast", 200),
    ("main;handle_request;process_query;optimize", 500),
    ("main;handle_request;process_query;optimize;rewrite_joins", 280),
    ("main;handle_request;process_query;optimize;estimate_cost", 180),
    ("main;handle_request;process_query;execute", 2400),
    ("main;handle_request;process_query;execute;fetch_rows", 1500),
    ("main;handle_request;process_query;execute;fetch_rows;read_index", 800),
    ("main;handle_request;process_query;execute;fetch_rows;read_index;btree_search", 500),
    ("main;handle_request;process_query;execute;fetch_rows;read_index;page_read", 250),
    ("main;handle_request;process_query;execute;fetch_rows;deserialize", 600),
    ("main;handle_request;process_query;execute;fetch_rows;deserialize;decode_row", 400),
    ("main;handle_request;process_query;execute;apply_filter", 700),
    ("main;handle_request;process_query;execute;apply_filter;compare_values", 450),
    ("main;handle_request;process_query;execute;apply_filter;check_null", 200),
    ("main;handle_request;process_query;format_result", 400),
    ("main;handle_request;process_query;format_result;build_json", 250),
    ("main;handle_request;process_query;format_result;paginate", 120),
    ("main;handle_request;send_response", 1000),
    ("main;handle_request;send_response;serialize_json", 500),
    ("main;handle_request;send_response;serialize_json;encode_utf8", 300),
    ("main;handle_request;send_response;compress", 300),
    ("main;handle_request;send_response;compress;deflate", 200),
    ("main;handle_request;send_response;write_socket", 150),
    ("main;gc_collect", 1000),
    ("main;gc_collect;mark_phase", 550),
    ("main;gc_collect;mark_phase;trace_refs", 350),
    ("main;gc_collect;mark_phase;check_weak_refs", 150),
    ("main;gc_collect;sweep_phase", 400),
    ("main;gc_collect;sweep_phase;free_objects", 250),
    ("main;gc_collect;sweep_phase;compact_heap", 120),
    ("main;log_metrics", 400),
    ("main;log_metrics;collect_counters", 200),
    ("main;log_metrics;flush_buffer", 150),
    ("main;log_metrics;flush_buffer;write_file", 100),
    ("main;log_metrics;flush_buffer;rotate_log", 40),
]

# Build hierarchy from stack traces
total_samples = 10000
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

# Perceptually uniform warm palette using Inferno colormap stops
# Mapped from cool (pale yellow, low heat) to hot (deep red-black, high heat)
INFERNO_STOPS = [
    (0.0, (252, 255, 164)),  # pale yellow (coolest)
    (0.15, (249, 228, 76)),  # yellow
    (0.30, (243, 177, 31)),  # amber
    (0.45, (226, 123, 25)),  # orange
    (0.60, (194, 74, 36)),  # red-orange
    (0.75, (148, 33, 61)),  # deep red
    (0.90, (101, 12, 81)),  # dark magenta
    (1.0, (60, 9, 76)),  # deep purple-black (hottest)
]


def heat_to_color(heat):
    """Interpolate in perceptually uniform Inferno colormap."""
    heat = max(0.0, min(1.0, heat))
    for i in range(len(INFERNO_STOPS) - 1):
        t0, c0 = INFERNO_STOPS[i]
        t1, c1 = INFERNO_STOPS[i + 1]
        if heat <= t1:
            frac = (heat - t0) / (t1 - t0) if t1 > t0 else 0
            r = int(c0[0] + frac * (c1[0] - c0[0]))
            g = int(c0[1] + frac * (c1[1] - c0[1]))
            b = int(c0[2] + frac * (c1[2] - c0[2]))
            return f"#{r:02x}{g:02x}{b:02x}"
    return f"#{INFERNO_STOPS[-1][1][0]:02x}{INFERNO_STOPS[-1][1][1]:02x}{INFERNO_STOPS[-1][1][2]:02x}"


# Layout flames iteratively using a stack (avoids recursive function for KISS)
rects = []
work_stack = [("main", 0.0, 100.0)]
while work_stack:
    stack_key, x_start, x_end = work_stack.pop()
    node = nodes[stack_key]
    depth = node["depth"]
    width_fraction = x_end - x_start

    # Color: perceptually uniform warm palette based on sample proportion
    heat = node["samples"] / total_samples
    color = heat_to_color(heat)
    text_color = "#f0f0f0" if heat > 0.55 else "#1a1a1a"

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
            "text_color": text_color,
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

# Plot - tighter y_range to minimize wasted vertical space
p = figure(
    width=4800,
    height=2700,
    title="flamegraph-basic \u00b7 bokeh \u00b7 pyplots.ai",
    x_range=(-1, 101),
    y_range=(-0.2, max_depth + 1.0),
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
            text_color=r["text_color"],
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
output_file("plot.html", title="flamegraph-basic \u00b7 bokeh \u00b7 pyplots.ai")
save(p)
