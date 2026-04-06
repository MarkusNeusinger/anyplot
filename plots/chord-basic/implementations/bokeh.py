""" pyplots.ai
chord-basic: Basic Chord Diagram
Library: bokeh 3.8.2 | Python 3.14
Quality: 85/100 | Updated: 2026-04-06
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure


output_file("plot.html", title="chord-basic · bokeh · pyplots.ai")

# Data - Migration flows between continents (in millions)
entities = ["Africa", "Asia", "Europe", "N. America", "S. America", "Oceania"]
n = len(entities)

# Flow matrix (rows = source, cols = target)
flow_matrix = np.array(
    [
        [0, 8, 12, 3, 2, 1],  # Africa to others
        [5, 0, 15, 10, 2, 4],  # Asia to others
        [3, 10, 0, 8, 4, 2],  # Europe to others
        [2, 6, 12, 0, 8, 1],  # N. America to others
        [4, 3, 7, 12, 0, 1],  # S. America to others
        [1, 5, 3, 2, 1, 0],  # Oceania to others
    ]
)

# Colorblind-safe palette — distinct hues, no yellow/orange confusion
colors = ["#306998", "#D55E00", "#0072B2", "#56B4E9", "#009E73", "#CC79A7"]

# Calculate total flows for each entity (sum of outgoing and incoming)
total_flows = flow_matrix.sum(axis=1) + flow_matrix.sum(axis=0)
total_all = total_flows.sum()

# Calculate arc angles for each entity
gap = 0.03 * 2 * np.pi
total_gap = gap * n
available = 2 * np.pi - total_gap
arc_angles = (total_flows / total_all) * available

# Calculate start and end angles for each entity's arc (start from top)
arc_starts = np.zeros(n)
arc_ends = np.zeros(n)
current_angle = np.pi / 2
for i in range(n):
    arc_starts[i] = current_angle
    arc_ends[i] = current_angle + arc_angles[i]
    current_angle = arc_ends[i] + gap

arc_mids = (arc_starts + arc_ends) / 2

# Figure
p = figure(
    width=3600,
    height=3600,
    title="chord-basic · bokeh · pyplots.ai",
    x_range=(-1.45, 1.85),
    y_range=(-1.45, 1.45),
    tools="hover,pan,wheel_zoom,reset",
)

p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None
p.background_fill_color = "#F5F5F0"
p.border_fill_color = "#FFFFFF"
p.title.text_font_size = "36pt"
p.title.text_color = "#2D2D2D"
p.title.align = "center"

# Determine top flows for storytelling emphasis
all_flows = []
for i in range(n):
    for j in range(n):
        if i != j and flow_matrix[i, j] > 0:
            all_flows.append(flow_matrix[i, j])
flow_75th = np.percentile(all_flows, 75)
flow_max = max(all_flows)

# Outer arcs — gradient-style with thicker ring for high-flow entities
outer_radius = 0.95
inner_radius = 0.87
arc_resolution = 60

for i in range(n):
    theta = np.linspace(arc_starts[i], arc_ends[i], arc_resolution)
    x_outer = outer_radius * np.cos(theta)
    y_outer = outer_radius * np.sin(theta)
    x_inner = inner_radius * np.cos(theta[::-1])
    y_inner = inner_radius * np.sin(theta[::-1])

    source = ColumnDataSource(
        data={
            "x": [list(np.concatenate([x_outer, x_inner]))],
            "y": [list(np.concatenate([y_outer, y_inner]))],
            "entity": [entities[i]],
            "total": [f"{int(total_flows[i])}M total flow"],
        }
    )
    p.patches("x", "y", source=source, fill_color=colors[i], fill_alpha=0.92, line_color="#FFFFFF", line_width=2.5)

# Inner ring — subtle decorative detail
inner_ring_r = inner_radius - 0.005
theta_full = np.linspace(0, 2 * np.pi, 360)
p.line(
    inner_ring_r * np.cos(theta_full),
    inner_ring_r * np.sin(theta_full),
    line_color="#CCCCCC",
    line_width=0.8,
    line_alpha=0.5,
)

# Entity labels with flow totals
label_radius = 1.12
for i in range(n):
    angle = arc_mids[i]
    x = label_radius * np.cos(angle)
    y = label_radius * np.sin(angle)

    angle_deg = np.degrees(angle) % 360
    if 80 < angle_deg < 100 or 260 < angle_deg < 280:
        anchor = "center"
    elif 90 < angle_deg < 270:
        anchor = "right"
    else:
        anchor = "left"

    p.text(
        x=[x],
        y=[y],
        text=[entities[i]],
        text_font_size="26pt",
        text_align=anchor,
        text_baseline="middle",
        text_color=colors[i],
        text_font_style="bold",
    )

    # Flow total underneath label — guides viewer to high-flow entities
    sub_y = y - 0.08
    p.text(
        x=[x],
        y=[sub_y],
        text=[f"{int(total_flows[i])}M"],
        text_font_size="16pt",
        text_align=anchor,
        text_baseline="middle",
        text_color="#888888",
    )

# Track position within each entity's arc for chord placement
chord_pos = arc_starts.copy()
chord_radius = inner_radius - 0.02
n_bezier = 40

# Draw bidirectional chords — visual hierarchy via alpha scaling
chord_data = {
    "x": [],
    "y": [],
    "source_name": [],
    "target_name": [],
    "value": [],
    "color": [],
    "alpha": [],
    "line_width": [],
}

for i in range(n):
    for j in range(n):
        if i == j or flow_matrix[i, j] == 0:
            continue

        val = flow_matrix[i, j]

        # Visual hierarchy: dominant flows get more emphasis
        if val >= flow_75th:
            alpha = 0.55 + 0.2 * (val / flow_max)
            lw = 2.0
        else:
            alpha = 0.2 + 0.15 * (val / flow_max)
            lw = 1.0

        # Chord width at source/target proportional to flow
        width_i = (val / total_flows[i]) * arc_angles[i]
        width_j = (val / total_flows[j]) * arc_angles[j]

        start_i = chord_pos[i]
        end_i = start_i + width_i
        chord_pos[i] = end_i

        start_j = chord_pos[j]
        end_j = start_j + width_j
        chord_pos[j] = end_j

        # Build chord shape: arc at i, bezier to j, arc at j, bezier back
        theta_i = np.linspace(start_i, end_i, 15)
        arc_i_x = chord_radius * np.cos(theta_i)
        arc_i_y = chord_radius * np.sin(theta_i)

        t = np.linspace(0, 1, n_bezier)
        x1, y1 = chord_radius * np.cos(end_i), chord_radius * np.sin(end_i)
        x2, y2 = chord_radius * np.cos(start_j), chord_radius * np.sin(start_j)
        bez1_x = (1 - t) ** 2 * x1 + t**2 * x2
        bez1_y = (1 - t) ** 2 * y1 + t**2 * y2

        theta_j = np.linspace(start_j, end_j, 15)
        arc_j_x = chord_radius * np.cos(theta_j)
        arc_j_y = chord_radius * np.sin(theta_j)

        x3, y3 = chord_radius * np.cos(end_j), chord_radius * np.sin(end_j)
        x4, y4 = chord_radius * np.cos(start_i), chord_radius * np.sin(start_i)
        bez2_x = (1 - t) ** 2 * x3 + t**2 * x4
        bez2_y = (1 - t) ** 2 * y3 + t**2 * y4

        cx = np.concatenate([arc_i_x, bez1_x, arc_j_x, bez2_x])
        cy = np.concatenate([arc_i_y, bez1_y, arc_j_y, bez2_y])

        chord_data["x"].append(list(cx))
        chord_data["y"].append(list(cy))
        chord_data["source_name"].append(entities[i])
        chord_data["target_name"].append(entities[j])
        chord_data["value"].append(int(val))
        chord_data["color"].append(colors[i])
        chord_data["alpha"].append(round(alpha, 3))
        chord_data["line_width"].append(lw)

# Render chords with per-element alpha for visual hierarchy
chord_source = ColumnDataSource(data=chord_data)
chords = p.patches(
    "x",
    "y",
    source=chord_source,
    fill_color="color",
    fill_alpha="alpha",
    line_color="color",
    line_alpha="alpha",
    line_width="line_width",
)

# Hover tool for chords — distinctive Bokeh interactive feature
hover = p.select(type=HoverTool)
hover.tooltips = """
<div style="font-size:16px;padding:8px;background:#FFFFFF;border:1px solid #CCC;border-radius:4px;">
<b>@source_name → @target_name</b><br/>
Flow: <b>@value</b> million
</div>
"""
hover.renderers = [chords]

# Legend with visual hierarchy indicator
legend_x = 1.3
legend_y = 0.65

p.add_layout(
    Label(
        x=legend_x - 0.02,
        y=legend_y + 0.15,
        text="Migration Flows",
        text_font_size="22pt",
        text_font_style="bold",
        text_color="#2D2D2D",
    )
)

# Sort legend entries by total flow (descending) to reinforce hierarchy
sorted_indices = np.argsort(-total_flows)
for rank, i in enumerate(sorted_indices):
    y_pos = legend_y - rank * 0.14
    p.rect(x=[legend_x], y=[y_pos], width=0.1, height=0.08, fill_color=colors[i], line_color="#FFFFFF", line_width=2)
    p.text(
        x=[legend_x + 0.1],
        y=[y_pos],
        text=[f"{entities[i]}  ({int(total_flows[i])}M)"],
        text_font_size="20pt",
        text_baseline="middle",
        text_color="#444444",
    )

# Annotation for top flow — focal point for data storytelling
top_flow_idx = np.unravel_index(flow_matrix.argmax(), flow_matrix.shape)
top_src, top_tgt = entities[top_flow_idx[0]], entities[top_flow_idx[1]]
top_val = flow_matrix[top_flow_idx[0], top_flow_idx[1]]

p.add_layout(
    Label(
        x=0,
        y=-1.3,
        text=f"Largest flow: {top_src} → {top_tgt} ({top_val}M)",
        text_font_size="18pt",
        text_color="#666666",
        text_align="center",
        text_font_style="italic",
    )
)

# Save
export_png(p, filename="plot.png")
save(p)
