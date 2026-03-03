""" pyplots.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-03
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem
from bokeh.plotting import figure


# Data: Remote work policy opinion survey — 1,000 employees across 4 quarterly waves
# Story: Opinions gradually polarize as the debate matures
waves = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
opinions = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
colors = {
    "Strongly Agree": "#306998",
    "Agree": "#6BAED6",
    "Neutral": "#A0A0A0",
    "Disagree": "#E8915A",
    "Strongly Disagree": "#8B2252",
}

# Flow transitions between consecutive waves (source, target, respondent_count)
flows_data = [
    # Q1 → Q2
    [
        ("Strongly Agree", "Strongly Agree", 105),
        ("Strongly Agree", "Agree", 15),
        ("Agree", "Strongly Agree", 25),
        ("Agree", "Agree", 230),
        ("Agree", "Neutral", 20),
        ("Agree", "Disagree", 5),
        ("Neutral", "Agree", 35),
        ("Neutral", "Neutral", 190),
        ("Neutral", "Disagree", 20),
        ("Neutral", "Strongly Disagree", 5),
        ("Disagree", "Agree", 5),
        ("Disagree", "Neutral", 30),
        ("Disagree", "Disagree", 175),
        ("Disagree", "Strongly Disagree", 20),
        ("Strongly Disagree", "Neutral", 10),
        ("Strongly Disagree", "Disagree", 15),
        ("Strongly Disagree", "Strongly Disagree", 95),
    ],
    # Q2 → Q3 (polarization intensifies)
    [
        ("Strongly Agree", "Strongly Agree", 120),
        ("Strongly Agree", "Agree", 10),
        ("Agree", "Strongly Agree", 40),
        ("Agree", "Agree", 215),
        ("Agree", "Neutral", 25),
        ("Agree", "Disagree", 5),
        ("Neutral", "Agree", 30),
        ("Neutral", "Neutral", 180),
        ("Neutral", "Disagree", 30),
        ("Neutral", "Strongly Disagree", 10),
        ("Disagree", "Agree", 5),
        ("Disagree", "Neutral", 25),
        ("Disagree", "Disagree", 160),
        ("Disagree", "Strongly Disagree", 25),
        ("Strongly Disagree", "Neutral", 10),
        ("Strongly Disagree", "Disagree", 10),
        ("Strongly Disagree", "Strongly Disagree", 100),
    ],
    # Q3 → Q4 (further polarization)
    [
        ("Strongly Agree", "Strongly Agree", 148),
        ("Strongly Agree", "Agree", 12),
        ("Agree", "Strongly Agree", 35),
        ("Agree", "Agree", 195),
        ("Agree", "Neutral", 25),
        ("Agree", "Disagree", 5),
        ("Neutral", "Agree", 25),
        ("Neutral", "Neutral", 175),
        ("Neutral", "Disagree", 30),
        ("Neutral", "Strongly Disagree", 10),
        ("Disagree", "Agree", 5),
        ("Disagree", "Neutral", 20),
        ("Disagree", "Disagree", 150),
        ("Disagree", "Strongly Disagree", 30),
        ("Strongly Disagree", "Neutral", 10),
        ("Strongly Disagree", "Disagree", 10),
        ("Strongly Disagree", "Strongly Disagree", 115),
    ],
]

# Compute node totals at each wave
node_totals = []
for w_idx in range(len(waves)):
    totals = {}
    if w_idx == 0:
        for op in opinions:
            totals[op] = sum(f[2] for f in flows_data[0] if f[0] == op)
    elif w_idx == len(waves) - 1:
        for op in opinions:
            totals[op] = sum(f[2] for f in flows_data[-1] if f[1] == op)
    else:
        for op in opinions:
            totals[op] = sum(f[2] for f in flows_data[w_idx - 1] if f[1] == op)
    node_totals.append(totals)

# Compute net flows per transition to identify largest shifts for highlighting
net_flows = []
for _w_idx, flows in enumerate(flows_data):
    transition_nets = {}
    for from_op, to_op, count in flows:
        if from_op != to_op:
            key = tuple(sorted([from_op, to_op]))
            if key not in transition_nets:
                transition_nets[key] = 0
            if from_op < to_op:
                transition_nets[key] += count
            else:
                transition_nets[key] -= count
    net_flows.append(transition_nets)

# Find the top net flow magnitude across all transitions for highlighting threshold
all_net_magnitudes = []
for nets in net_flows:
    all_net_magnitudes.extend(abs(v) for v in nets.values())
net_highlight_threshold = sorted(all_net_magnitudes, reverse=True)[2] if len(all_net_magnitudes) > 2 else 0

# Layout
x_positions = [0, 1.5, 3.0, 4.5]
node_width = 0.14
gap = 18

# Calculate node vertical positions
node_positions = []
for w_idx in range(len(waves)):
    positions = {}
    y_cursor = 0
    for op in opinions:
        height = node_totals[w_idx][op]
        positions[op] = {"y_start": y_cursor, "y_end": y_cursor + height}
        y_cursor += height + gap
    node_positions.append(positions)

max_y = max(node_positions[w][opinions[-1]]["y_end"] for w in range(len(waves)))

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="alluvial-opinion-flow · bokeh · pyplots.ai",
    x_range=(-1.8, 6.8),
    y_range=(-70, max_y + 80),
    tools="",
    toolbar_location=None,
)

# Style
p.title.text_font_size = "32pt"
p.title.align = "center"
p.xgrid.visible = False
p.ygrid.visible = False
p.xaxis.visible = False
p.yaxis.visible = False
p.outline_line_color = None
p.background_fill_color = "#FFFFFF"

# Subtitle
subtitle = Label(
    x=2.25,
    y=max_y + 55,
    text="Remote Work Policy Survey — 1,000 Employees Across 4 Quarters",
    text_font_size="22pt",
    text_align="center",
    text_baseline="top",
    text_color="#555555",
)
p.add_layout(subtitle)

# Precompute all flow ribbon data for ColumnDataSource-based rendering
n_points = 50
t_param = np.linspace(0, 1, n_points)

flow_xs_list = []
flow_ys_list = []
flow_colors = []
flow_alphas = []
flow_line_widths = []
flow_from_labels = []
flow_to_labels = []
flow_counts = []
flow_wave_labels = []
flow_types = []

for w_idx, flows in enumerate(flows_data):
    x_start = x_positions[w_idx] + node_width / 2
    x_end = x_positions[w_idx + 1] - node_width / 2

    source_cursors = {op: node_positions[w_idx][op]["y_start"] for op in opinions}
    target_cursors = {op: node_positions[w_idx + 1][op]["y_start"] for op in opinions}

    for from_op, to_op, count in flows:
        if count == 0:
            continue

        y_src_bottom = source_cursors[from_op]
        y_src_top = y_src_bottom + count
        source_cursors[from_op] = y_src_top

        y_tgt_bottom = target_cursors[to_op]
        y_tgt_top = y_tgt_bottom + count
        target_cursors[to_op] = y_tgt_top

        is_stable = from_op == to_op

        # Check if this flow is part of a large net shift
        is_net_highlight = False
        if not is_stable:
            key = tuple(sorted([from_op, to_op]))
            net_mag = abs(net_flows[w_idx].get(key, 0))
            is_net_highlight = net_mag >= net_highlight_threshold

        # Cubic bezier control points
        cx0 = x_start + (x_end - x_start) / 3
        cx1 = x_start + 2 * (x_end - x_start) / 3

        # Top edge bezier
        x_curve = (
            (1 - t_param) ** 3 * x_start
            + 3 * (1 - t_param) ** 2 * t_param * cx0
            + 3 * (1 - t_param) * t_param**2 * cx1
            + t_param**3 * x_end
        )
        y_top = (
            (1 - t_param) ** 3 * y_src_top
            + 3 * (1 - t_param) ** 2 * t_param * y_src_top
            + 3 * (1 - t_param) * t_param**2 * y_tgt_top
            + t_param**3 * y_tgt_top
        )
        y_bottom = (
            (1 - t_param) ** 3 * y_src_bottom
            + 3 * (1 - t_param) ** 2 * t_param * y_src_bottom
            + 3 * (1 - t_param) * t_param**2 * y_tgt_bottom
            + t_param**3 * y_tgt_bottom
        )

        xs = list(x_curve) + list(x_curve[::-1])
        ys = list(y_top) + list(y_bottom[::-1])

        if is_stable:
            fill_alpha = 0.6
            line_w = 0.5
        elif is_net_highlight:
            fill_alpha = 0.45
            line_w = 2.0
        else:
            fill_alpha = 0.2
            line_w = 0.5

        flow_xs_list.append(xs)
        flow_ys_list.append(ys)
        flow_colors.append(colors[from_op])
        flow_alphas.append(fill_alpha)
        flow_line_widths.append(line_w)
        flow_from_labels.append(from_op)
        flow_to_labels.append(to_op)
        flow_counts.append(count)
        flow_wave_labels.append(f"{waves[w_idx]} → {waves[w_idx + 1]}")
        flow_types.append("Stable" if is_stable else "Changed")

# Sort: render changers first (behind), then stable on top
sort_order = sorted(range(len(flow_types)), key=lambda i: flow_types[i] == "Stable")

flow_source = ColumnDataSource(
    data={
        "xs": [flow_xs_list[i] for i in sort_order],
        "ys": [flow_ys_list[i] for i in sort_order],
        "color": [flow_colors[i] for i in sort_order],
        "alpha": [flow_alphas[i] for i in sort_order],
        "line_width": [flow_line_widths[i] for i in sort_order],
        "from_op": [flow_from_labels[i] for i in sort_order],
        "to_op": [flow_to_labels[i] for i in sort_order],
        "count": [flow_counts[i] for i in sort_order],
        "wave": [flow_wave_labels[i] for i in sort_order],
        "flow_type": [flow_types[i] for i in sort_order],
    }
)

flow_renderer = p.patches(
    xs="xs",
    ys="ys",
    fill_color="color",
    fill_alpha="alpha",
    line_color="color",
    line_alpha=0.3,
    line_width="line_width",
    source=flow_source,
)

# Add HoverTool for flow ribbons
hover = HoverTool(
    renderers=[flow_renderer],
    tooltips=[
        ("Transition", "@wave"),
        ("From", "@from_op"),
        ("To", "@to_op"),
        ("Respondents", "@count"),
        ("Type", "@flow_type"),
    ],
    point_policy="follow_mouse",
)
p.add_tools(hover)

# Draw nodes using ColumnDataSource
node_left = []
node_right = []
node_top = []
node_bottom = []
node_colors_list = []
node_op_labels = []
node_wave_labels = []
node_count_labels = []

for w_idx in range(len(waves)):
    x = x_positions[w_idx]
    for op in opinions:
        y_start = node_positions[w_idx][op]["y_start"]
        y_end = node_positions[w_idx][op]["y_end"]
        height = y_end - y_start
        if height > 0:
            node_left.append(x - node_width / 2)
            node_right.append(x + node_width / 2)
            node_top.append(y_end)
            node_bottom.append(y_start)
            node_colors_list.append(colors[op])
            node_op_labels.append(op)
            node_wave_labels.append(waves[w_idx])
            node_count_labels.append(str(int(height)))

node_source = ColumnDataSource(
    data={
        "left": node_left,
        "right": node_right,
        "top": node_top,
        "bottom": node_bottom,
        "color": node_colors_list,
        "opinion": node_op_labels,
        "wave": node_wave_labels,
        "count": node_count_labels,
    }
)

p.quad(
    left="left",
    right="right",
    top="top",
    bottom="bottom",
    fill_color="color",
    line_color="white",
    line_width=2,
    source=node_source,
)

# Node text labels and legend renderers
legend_renderers = {}
for w_idx in range(len(waves)):
    x = x_positions[w_idx]
    for op in opinions:
        y_start = node_positions[w_idx][op]["y_start"]
        y_end = node_positions[w_idx][op]["y_end"]
        height = y_end - y_start

        if height > 0:
            if op not in legend_renderers:
                r = p.quad(
                    left=x - node_width / 2,
                    right=x + node_width / 2,
                    top=y_end,
                    bottom=y_start,
                    fill_color=colors[op],
                    line_color=colors[op],
                    fill_alpha=0,
                    line_alpha=0,
                )
                legend_renderers[op] = r

            y_mid = (y_start + y_end) / 2
            if w_idx == 0:
                label = Label(
                    x=x - node_width / 2 - 0.05,
                    y=y_mid,
                    text=f"{op} ({int(height)})",
                    text_font_size="18pt",
                    text_baseline="middle",
                    text_align="right",
                    text_color="#333333",
                )
                p.add_layout(label)
            elif w_idx == len(waves) - 1:
                label = Label(
                    x=x + node_width / 2 + 0.05,
                    y=y_mid,
                    text=f"{op} ({int(height)})",
                    text_font_size="18pt",
                    text_baseline="middle",
                    text_color="#333333",
                )
                p.add_layout(label)
            else:
                label = Label(
                    x=x + node_width / 2 + 0.05,
                    y=y_mid,
                    text=str(int(height)),
                    text_font_size="16pt",
                    text_baseline="middle",
                    text_color="#555555",
                )
                p.add_layout(label)

# Wave column headers
for w_idx, wave in enumerate(waves):
    label = Label(
        x=x_positions[w_idx],
        y=-20,
        text=wave,
        text_font_size="24pt",
        text_align="center",
        text_baseline="top",
        text_color="#333333",
        text_font_style="bold",
    )
    p.add_layout(label)

# Legend — positioned inside the plot, larger text
legend_items = [LegendItem(label=op, renderers=[legend_renderers[op]]) for op in opinions]
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="18pt",
    glyph_width=32,
    glyph_height=32,
    spacing=10,
    padding=18,
    background_fill_alpha=0.85,
    background_fill_color="white",
    border_line_color="#bbbbbb",
    border_line_width=2,
)
p.add_layout(legend, "right")

# Opacity legend note
opacity_note = Label(
    x=2.25,
    y=-50,
    text="Solid flows = stable opinion  ·  Faded flows = opinion changed  ·  Bold flows = largest net shifts",
    text_font_size="18pt",
    text_align="center",
    text_color="#777777",
)
p.add_layout(opacity_note)

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
