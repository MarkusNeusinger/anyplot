""" pyplots.ai
circos-basic: Circos Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


np.random.seed(42)

# Data: Regional trade flows between economic regions
regions = ["Asia", "Europe", "N. America", "S. America", "Africa", "Oceania"]
n_regions = len(regions)

# Connection matrix (trade flows between regions in billions USD)
# Row = source, Column = target
flow_matrix = np.array(
    [
        [0, 45, 52, 18, 15, 22],  # Asia exports to...
        [38, 0, 35, 12, 20, 8],  # Europe exports to...
        [48, 42, 0, 28, 10, 15],  # N. America exports to...
        [15, 18, 25, 0, 8, 5],  # S. America exports to...
        [12, 25, 8, 10, 0, 3],  # Africa exports to...
        [20, 10, 18, 6, 4, 0],  # Oceania exports to...
    ]
)

# Segment sizes (total trade volume for each region)
segment_sizes = flow_matrix.sum(axis=0) + flow_matrix.sum(axis=1)

# Track data (GDP growth rate for each region)
track_values = np.array([4.2, 1.8, 2.5, 1.5, 3.8, 2.2])

# Color palette for regions
colors = ["#306998", "#FFD43B", "#E85C47", "#4DAF4A", "#984EA3", "#FF7F00"]

# Calculate segment positions (angles)
total_size = segment_sizes.sum()
gap = 0.03  # Gap between segments (radians)
total_gap = gap * n_regions
available_angle = 2 * np.pi - total_gap

segment_angles = []
current_angle = 0
for size in segment_sizes:
    angle_span = (size / total_size) * available_angle
    start = current_angle
    end = current_angle + angle_span
    segment_angles.append((start, end))
    current_angle = end + gap

# Create figure (square for circular plot)
p = figure(
    width=3600,
    height=3600,
    title="circos-basic · bokeh · pyplots.ai",
    x_range=(-1.5, 1.5),
    y_range=(-1.5, 1.5),
    tools="",
    toolbar_location=None,
)

# Styling
p.title.text_font_size = "48pt"
p.title.align = "center"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.background_fill_color = "white"

outer_radius = 1.0
inner_radius = 0.85
track_outer = 0.82
track_inner = 0.70
ribbon_radius = 0.65


# Draw outer segments (arcs)
for i, (start, end) in enumerate(segment_angles):
    # Outer arc
    theta = np.linspace(start, end, 50)
    outer_x = outer_radius * np.cos(theta)
    outer_y = outer_radius * np.sin(theta)
    inner_x = inner_radius * np.cos(theta[::-1])
    inner_y = inner_radius * np.sin(theta[::-1])

    xs = np.concatenate([outer_x, inner_x, [outer_x[0]]])
    ys = np.concatenate([outer_y, inner_y, [outer_y[0]]])

    source = ColumnDataSource(data={"xs": [xs], "ys": [ys]})
    p.patches(xs="xs", ys="ys", source=source, fill_color=colors[i], line_color="white", line_width=2, alpha=0.9)

    # Add region label
    mid_angle = (start + end) / 2
    label_radius = outer_radius + 0.12
    label_x = label_radius * np.cos(mid_angle)
    label_y = label_radius * np.sin(mid_angle)

    # Rotate text based on position
    angle = mid_angle * 180 / np.pi
    if 90 < angle < 270:
        angle += 180

    p.text(
        x=[label_x],
        y=[label_y],
        text=[regions[i]],
        text_font_size="28pt",
        text_align="center",
        text_baseline="middle",
        text_color="#333333",
        angle=[np.radians(angle - 90)],
    )

# Draw inner track (GDP growth rate)
max_track = track_values.max()
min_track = track_values.min()
track_range = max_track - min_track

for i, (start, end) in enumerate(segment_angles):
    # Normalized track value
    norm_val = (track_values[i] - min_track) / track_range if track_range > 0 else 0.5
    bar_radius = track_inner + norm_val * (track_outer - track_inner)

    theta = np.linspace(start, end, 30)
    outer_x = bar_radius * np.cos(theta)
    outer_y = bar_radius * np.sin(theta)
    inner_x = track_inner * np.cos(theta[::-1])
    inner_y = track_inner * np.sin(theta[::-1])

    xs = np.concatenate([outer_x, inner_x, [outer_x[0]]])
    ys = np.concatenate([outer_y, inner_y, [outer_y[0]]])

    source = ColumnDataSource(data={"xs": [xs], "ys": [ys]})
    p.patches(xs="xs", ys="ys", source=source, fill_color=colors[i], line_color=None, alpha=0.6)

# Draw track reference circle
track_ref_theta = np.linspace(0, 2 * np.pi, 100)
track_ref_x = track_inner * np.cos(track_ref_theta)
track_ref_y = track_inner * np.sin(track_ref_theta)
p.line(track_ref_x, track_ref_y, line_color="#cccccc", line_width=1, line_alpha=0.5)

# Draw ribbons (connections between regions)
# Filter significant flows
flow_threshold = 15

for i in range(n_regions):
    for j in range(i + 1, n_regions):  # Only upper triangle to avoid duplicates
        flow_ij = flow_matrix[i, j]
        flow_ji = flow_matrix[j, i]
        total_flow = flow_ij + flow_ji

        if total_flow < flow_threshold:
            continue

        # Calculate ribbon widths proportional to flow
        # Source segment i
        start_i, end_i = segment_angles[i]
        seg_span_i = end_i - start_i
        ribbon_width_i = (total_flow / segment_sizes[i]) * seg_span_i * 0.8

        # Target segment j
        start_j, end_j = segment_angles[j]
        seg_span_j = end_j - start_j
        ribbon_width_j = (total_flow / segment_sizes[j]) * seg_span_j * 0.8

        # Position ribbons at center of segments
        mid_i = (start_i + end_i) / 2
        mid_j = (start_j + end_j) / 2

        # Ribbon endpoints on source
        theta_i_start = mid_i - ribbon_width_i / 2
        theta_i_end = mid_i + ribbon_width_i / 2

        # Ribbon endpoints on target
        theta_j_start = mid_j - ribbon_width_j / 2
        theta_j_end = mid_j + ribbon_width_j / 2

        # Create bezier-like ribbon using quadratic curves
        n_curve = 30

        # Path: from i_start arc to j_start, then j arc, then back via bezier
        # Side 1: from i_start to j_start
        t = np.linspace(0, 1, n_curve)
        # Control point at center
        ctrl_x, ctrl_y = 0, 0

        # Start point
        x1_start = ribbon_radius * np.cos(theta_i_start)
        y1_start = ribbon_radius * np.sin(theta_i_start)
        # End point
        x1_end = ribbon_radius * np.cos(theta_j_start)
        y1_end = ribbon_radius * np.sin(theta_j_start)

        # Quadratic bezier
        curve1_x = (1 - t) ** 2 * x1_start + 2 * (1 - t) * t * ctrl_x + t**2 * x1_end
        curve1_y = (1 - t) ** 2 * y1_start + 2 * (1 - t) * t * ctrl_y + t**2 * y1_end

        # Arc at j
        arc_j_theta = np.linspace(theta_j_start, theta_j_end, 10)
        arc_j_x = ribbon_radius * np.cos(arc_j_theta)
        arc_j_y = ribbon_radius * np.sin(arc_j_theta)

        # Side 2: from j_end back to i_end
        x2_start = ribbon_radius * np.cos(theta_j_end)
        y2_start = ribbon_radius * np.sin(theta_j_end)
        x2_end = ribbon_radius * np.cos(theta_i_end)
        y2_end = ribbon_radius * np.sin(theta_i_end)

        curve2_x = (1 - t) ** 2 * x2_start + 2 * (1 - t) * t * ctrl_x + t**2 * x2_end
        curve2_y = (1 - t) ** 2 * y2_start + 2 * (1 - t) * t * ctrl_y + t**2 * y2_end

        # Arc at i
        arc_i_theta = np.linspace(theta_i_end, theta_i_start, 10)
        arc_i_x = ribbon_radius * np.cos(arc_i_theta)
        arc_i_y = ribbon_radius * np.sin(arc_i_theta)

        # Combine all points
        ribbon_x = np.concatenate([curve1_x, arc_j_x, curve2_x, arc_i_x])
        ribbon_y = np.concatenate([curve1_y, arc_j_y, curve2_y, arc_i_y])

        # Use gradient color (blend of source and target)
        ribbon_color = colors[i]

        source = ColumnDataSource(data={"xs": [ribbon_x], "ys": [ribbon_y]})
        p.patches(
            xs="xs", ys="ys", source=source, fill_color=ribbon_color, line_color=ribbon_color, line_width=0.5, alpha=0.5
        )

# Add legend manually
legend_x = 1.15
legend_y_start = 0.8
legend_spacing = 0.15

for i, region in enumerate(regions):
    y_pos = legend_y_start - i * legend_spacing
    # Color box
    p.rect(x=[legend_x], y=[y_pos], width=0.08, height=0.08, fill_color=colors[i], line_color=None)
    # Label
    p.text(
        x=[legend_x + 0.08],
        y=[y_pos],
        text=[region],
        text_font_size="16pt",
        text_align="left",
        text_baseline="middle",
        text_color="#333333",
    )

# Add title for track (positioned near the inner track for clarity)
p.text(x=[-0.45], y=[-0.45], text=["Inner track:"], text_font_size="20pt", text_color="#666666", text_align="center")
p.text(x=[-0.45], y=[-0.55], text=["GDP Growth (%)"], text_font_size="20pt", text_color="#666666", text_align="center")

# Save outputs
export_png(p, filename="plot.png")

# Save HTML for interactivity
output_file("plot.html")
save(p)
