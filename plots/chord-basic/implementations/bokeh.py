""" pyplots.ai
chord-basic: Basic Chord Diagram
Library: bokeh 3.8.2 | Python 3.14
Quality: 81/100 | Updated: 2026-04-06
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool
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

# Colors for each entity (colorblind-safe palette starting with Python Blue)
colors = ["#306998", "#FFD43B", "#E69F00", "#56B4E9", "#009E73", "#CC79A7"]

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
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FFFFFF"
p.title.text_font_size = "36pt"
p.title.text_color = "#333333"
p.title.align = "center"

# Outer arcs
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
            "total": [int(total_flows[i])],
        }
    )
    p.patches("x", "y", source=source, fill_color=colors[i], fill_alpha=0.9, line_color="white", line_width=2)

# Entity labels
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

# Track position within each entity's arc for chord placement
chord_pos = arc_starts.copy()
chord_radius = inner_radius - 0.02
n_bezier = 40

# Draw bidirectional chords - each direction as a separate chord
chord_data = {"x": [], "y": [], "source_name": [], "target_name": [], "value": [], "color": []}

for i in range(n):
    for j in range(n):
        if i == j or flow_matrix[i, j] == 0:
            continue

        val = flow_matrix[i, j]

        # Chord width at source (i) proportional to flow relative to entity total
        width_i = (val / total_flows[i]) * arc_angles[i]
        # Chord width at target (j) proportional to flow relative to entity total
        width_j = (val / total_flows[j]) * arc_angles[j]

        start_i = chord_pos[i]
        end_i = start_i + width_i
        chord_pos[i] = end_i

        start_j = chord_pos[j]
        end_j = start_j + width_j
        chord_pos[j] = end_j

        # Build chord shape: arc at i, bezier to j, arc at j, bezier back
        # Arc along entity i
        theta_i = np.linspace(start_i, end_i, 15)
        arc_i_x = chord_radius * np.cos(theta_i)
        arc_i_y = chord_radius * np.sin(theta_i)

        # Bezier from end of i to start of j (through center)
        t = np.linspace(0, 1, n_bezier)
        x1 = chord_radius * np.cos(end_i)
        y1 = chord_radius * np.sin(end_i)
        x2 = chord_radius * np.cos(start_j)
        y2 = chord_radius * np.sin(start_j)
        bez1_x = (1 - t) ** 2 * x1 + t**2 * x2
        bez1_y = (1 - t) ** 2 * y1 + t**2 * y2

        # Arc along entity j
        theta_j = np.linspace(start_j, end_j, 15)
        arc_j_x = chord_radius * np.cos(theta_j)
        arc_j_y = chord_radius * np.sin(theta_j)

        # Bezier from end of j back to start of i
        x3 = chord_radius * np.cos(end_j)
        y3 = chord_radius * np.sin(end_j)
        x4 = chord_radius * np.cos(start_i)
        y4 = chord_radius * np.sin(start_i)
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

# Render chords
chord_source = ColumnDataSource(data=chord_data)
chords = p.patches(
    "x",
    "y",
    source=chord_source,
    fill_color="color",
    fill_alpha=0.45,
    line_color="color",
    line_alpha=0.65,
    line_width=1.5,
)

# Hover tool for chords
hover = p.select(type=HoverTool)
hover.tooltips = [("From", "@source_name"), ("To", "@target_name"), ("Flow", "@value million")]
hover.renderers = [chords]

# Legend
legend_x = 1.3
legend_y = 0.6
p.text(
    x=[legend_x - 0.02],
    y=[legend_y + 0.15],
    text=["Migration Flows"],
    text_font_size="22pt",
    text_font_style="bold",
    text_color="#333333",
)

for i, (entity, color) in enumerate(zip(entities, colors, strict=True)):
    y_pos = legend_y - i * 0.14
    p.rect(x=[legend_x], y=[y_pos], width=0.1, height=0.08, fill_color=color, line_color="white", line_width=2)
    p.text(
        x=[legend_x + 0.1],
        y=[y_pos],
        text=[entity],
        text_font_size="20pt",
        text_baseline="middle",
        text_color="#333333",
    )

# Save
export_png(p, filename="plot.png")
save(p)
