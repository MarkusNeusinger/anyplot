""" pyplots.ai
chord-basic: Basic Chord Diagram
Library: bokeh 3.8.2 | Python 3.14
Quality: 90/100 | Updated: 2026-04-06
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

# Figure — centered symmetric layout, no toolbar clutter
p = figure(
    width=3600,
    height=3600,
    title="chord-basic · bokeh · pyplots.ai",
    x_range=(-1.55, 1.55),
    y_range=(-1.75, 1.45),
    toolbar_location=None,
    tools="",
)

p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None
p.background_fill_color = "#F5F5F0"
p.border_fill_color = "#F5F5F0"
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
        text_font_size="28pt",
        text_align=anchor,
        text_baseline="middle",
        text_color=colors[i],
        text_font_style="bold",
    )

    # Flow total underneath label
    sub_y = y - 0.08
    p.text(
        x=[x],
        y=[sub_y],
        text=[f"{int(total_flows[i])}M"],
        text_font_size="20pt",
        text_align=anchor,
        text_baseline="middle",
        text_color="#777777",
    )

# Track position within each entity's arc for chord placement
chord_pos = arc_starts.copy()
chord_radius = inner_radius - 0.02
n_bezier = 40

# Build all chord shapes — visual hierarchy via alpha scaling
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
        alpha = (0.55 + 0.2 * (val / flow_max)) if val >= flow_75th else (0.2 + 0.15 * (val / flow_max))
        lw = 2.0 if val >= flow_75th else 1.0

        # Chord width proportional to flow
        w_i = (val / total_flows[i]) * arc_angles[i]
        w_j = (val / total_flows[j]) * arc_angles[j]
        s_i, chord_pos[i] = chord_pos[i], chord_pos[i] + w_i
        e_i = chord_pos[i]
        s_j, chord_pos[j] = chord_pos[j], chord_pos[j] + w_j
        e_j = chord_pos[j]

        # Build chord: arc at i → bezier → arc at j → bezier back
        th_i = np.linspace(s_i, e_i, 15)
        th_j = np.linspace(s_j, e_j, 15)
        t = np.linspace(0, 1, n_bezier)

        pts_i = chord_radius * np.exp(1j * th_i)
        pts_j = chord_radius * np.exp(1j * th_j)
        p1, p2 = pts_i[-1], pts_j[0]
        p3, p4 = pts_j[-1], pts_i[0]
        bez1 = (1 - t) ** 2 * p1 + t**2 * p2
        bez2 = (1 - t) ** 2 * p3 + t**2 * p4

        cx = np.concatenate([pts_i.real, bez1.real, pts_j.real, bez2.real])
        cy = np.concatenate([pts_i.imag, bez1.imag, pts_j.imag, bez2.imag])

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
hover = HoverTool(
    renderers=[chords],
    tooltips="""
<div style="font-size:16px;padding:8px;background:#FFFFFF;border:1px solid #CCC;border-radius:4px;">
<b>@source_name → @target_name</b><br/>
Flow: <b>@value</b> million
</div>
""",
)
p.add_tools(hover)

# Legend below the diagram — horizontal layout
sorted_indices = np.argsort(-total_flows)
cols = 3
legend_y_start = -1.25
legend_spacing = 0.14

for rank, idx in enumerate(sorted_indices):
    col = rank % cols
    row = rank // cols
    lx = -0.85 + col * 0.65
    ly = legend_y_start - row * legend_spacing

    p.rect(x=[lx - 0.06], y=[ly], width=0.06, height=0.055, fill_color=colors[idx], line_color=None)
    p.text(
        x=[lx - 0.02],
        y=[ly],
        text=[f"{entities[idx]}  ({int(total_flows[idx])}M)"],
        text_font_size="18pt",
        text_baseline="middle",
        text_color="#444444",
    )

# Annotation for top flow — focal point for data storytelling
top_idx = np.unravel_index(flow_matrix.argmax(), flow_matrix.shape)
top_src, top_tgt = entities[top_idx[0]], entities[top_idx[1]]
top_val = flow_matrix[top_idx[0], top_idx[1]]

p.add_layout(
    Label(
        x=0,
        y=-1.1,
        text=f"Largest flow: {top_src} → {top_tgt} ({top_val}M)",
        text_font_size="20pt",
        text_color="#666666",
        text_align="center",
        text_font_style="italic",
    )
)

# Save
export_png(p, filename="plot.png")
save(p)
