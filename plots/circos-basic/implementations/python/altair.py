""" pyplots.ai
circos-basic: Circos Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Software module dependencies
np.random.seed(42)

# Define segments (software modules)
segments = ["Core", "API", "Database", "Auth", "Cache", "Queue", "Logger", "Config"]
n_segments = len(segments)

# Segment sizes (relative importance/size of each module)
segment_sizes = np.array([25, 20, 18, 15, 12, 10, 8, 6])
segment_sizes_normalized = segment_sizes / segment_sizes.sum()

# Connection matrix (dependencies between modules)
connections = [
    ("Core", "API", 15),
    ("Core", "Database", 12),
    ("Core", "Logger", 8),
    ("API", "Auth", 10),
    ("API", "Cache", 8),
    ("Database", "Cache", 6),
    ("Database", "Logger", 5),
    ("Auth", "Logger", 4),
    ("Queue", "Logger", 7),
    ("Queue", "Database", 5),
    ("Config", "Core", 9),
    ("Config", "Logger", 3),
    ("Cache", "Logger", 4),
    ("API", "Queue", 6),
]

# Inner track data (simulated importance/activity values)
track_data = np.random.uniform(0.3, 1.0, n_segments)

# Colors for each segment (colorblind-safe palette)
colors = {
    "Core": "#306998",  # Python Blue
    "API": "#FFD43B",  # Python Yellow
    "Database": "#2E8B57",  # Sea Green
    "Auth": "#DC143C",  # Crimson
    "Cache": "#9370DB",  # Medium Purple
    "Queue": "#20B2AA",  # Light Sea Green
    "Logger": "#FF8C00",  # Dark Orange
    "Config": "#708090",  # Slate Gray
}

# Target output: 3600x3600 px (1:1 aspect ratio for circular plot) with scale_factor=3.0
# Internal canvas: 1200x1200 pixels
width = 1200
height = 1200
center_x = width / 2
center_y = height / 2

# Circle parameters
outer_radius = 400
inner_radius = 360
track_outer_radius = 340
track_inner_radius = 280
ribbon_radius = 270

# Calculate segment positions
gap = 0.05  # Gap between segments in radians
total_gap = gap * n_segments
available_angle = 2 * np.pi - total_gap
segment_angles = segment_sizes_normalized * available_angle

# Calculate start and end angles for each segment (starting at top)
start_angle = np.pi / 2
segment_arcs = {}
current_angle = start_angle

for i, name in enumerate(segments):
    arc_angle = segment_angles[i]
    segment_arcs[name] = {"start": current_angle, "end": current_angle - arc_angle, "angle": arc_angle, "idx": i}
    current_angle = current_angle - arc_angle - gap

segment_dict = {name: i for i, name in enumerate(segments)}

# Create outer ring segments data
n_arc_points = 50
outer_ring_data = []

for name in segments:
    arc = segment_arcs[name]
    theta = np.linspace(arc["end"], arc["start"], n_arc_points)

    # Outer arc (clockwise)
    for j, angle in enumerate(theta):
        outer_ring_data.append(
            {
                "segment": name,
                "x": center_x + outer_radius * np.cos(angle),
                "y": center_y + outer_radius * np.sin(angle),
                "order": j,
                "color": colors[name],
            }
        )

    # Inner arc (counter-clockwise to close the shape)
    for j, angle in enumerate(reversed(theta)):
        outer_ring_data.append(
            {
                "segment": name,
                "x": center_x + inner_radius * np.cos(angle),
                "y": center_y + inner_radius * np.sin(angle),
                "order": n_arc_points + j,
                "color": colors[name],
            }
        )

outer_ring_df = pd.DataFrame(outer_ring_data)

# Create inner track data (concentric data track)
inner_track_data = []

for i, name in enumerate(segments):
    arc = segment_arcs[name]
    theta = np.linspace(arc["end"], arc["start"], n_arc_points)

    # Height proportional to track data value
    track_height = (track_outer_radius - track_inner_radius) * track_data[i]
    actual_outer = track_inner_radius + track_height

    # Outer arc
    for j, angle in enumerate(theta):
        inner_track_data.append(
            {
                "segment": name,
                "x": center_x + actual_outer * np.cos(angle),
                "y": center_y + actual_outer * np.sin(angle),
                "order": j,
                "value": track_data[i],
            }
        )

    # Inner arc (counter-clockwise)
    for j, angle in enumerate(reversed(theta)):
        inner_track_data.append(
            {
                "segment": name,
                "x": center_x + track_inner_radius * np.cos(angle),
                "y": center_y + track_inner_radius * np.sin(angle),
                "order": n_arc_points + j,
                "value": track_data[i],
            }
        )

inner_track_df = pd.DataFrame(inner_track_data)

# Create ribbons (connections between segments)
max_value = max(c[2] for c in connections)
n_ribbon_points = 30
ribbons_data = []
ribbon_id = 0

for source, target, value in connections:
    arc1 = segment_arcs[source]
    arc2 = segment_arcs[target]

    # Calculate positions at segment midpoints
    mid1 = (arc1["start"] + arc1["end"]) / 2
    mid2 = (arc2["start"] + arc2["end"]) / 2

    # Ribbon width proportional to value (minimum 0.04 for visibility)
    width_factor = max(0.04, value / max_value * 0.12)

    # Points for source segment
    angle1_start = mid1 - width_factor
    angle1_end = mid1 + width_factor

    # Points for target segment
    angle2_start = mid2 - width_factor
    angle2_end = mid2 + width_factor

    ribbon_points = []

    # Arc at source
    src_angles = np.linspace(angle1_start, angle1_end, 8)
    for angle in src_angles:
        ribbon_points.append((center_x + ribbon_radius * np.cos(angle), center_y + ribbon_radius * np.sin(angle)))

    # Bezier curve from source end to target start
    for i in range(n_ribbon_points):
        t = i / (n_ribbon_points - 1)
        # Quadratic bezier with control point at center
        x = (
            (1 - t) ** 2 * (center_x + ribbon_radius * np.cos(angle1_end))
            + 2 * (1 - t) * t * center_x
            + t**2 * (center_x + ribbon_radius * np.cos(angle2_start))
        )
        y = (
            (1 - t) ** 2 * (center_y + ribbon_radius * np.sin(angle1_end))
            + 2 * (1 - t) * t * center_y
            + t**2 * (center_y + ribbon_radius * np.sin(angle2_start))
        )
        ribbon_points.append((x, y))

    # Arc at target
    tgt_angles = np.linspace(angle2_start, angle2_end, 8)
    for angle in tgt_angles:
        ribbon_points.append((center_x + ribbon_radius * np.cos(angle), center_y + ribbon_radius * np.sin(angle)))

    # Bezier curve from target end back to source start
    for i in range(n_ribbon_points):
        t = i / (n_ribbon_points - 1)
        x = (
            (1 - t) ** 2 * (center_x + ribbon_radius * np.cos(angle2_end))
            + 2 * (1 - t) * t * center_x
            + t**2 * (center_x + ribbon_radius * np.cos(angle1_start))
        )
        y = (
            (1 - t) ** 2 * (center_y + ribbon_radius * np.sin(angle2_end))
            + 2 * (1 - t) * t * center_y
            + t**2 * (center_y + ribbon_radius * np.sin(angle1_start))
        )
        ribbon_points.append((x, y))

    # Add points to dataframe
    for pt_idx, (x, y) in enumerate(ribbon_points):
        ribbons_data.append(
            {
                "ribbon_id": f"{source}-{target}-{ribbon_id}",
                "source": source,
                "target": target,
                "value": value,
                "x": x,
                "y": y,
                "order": pt_idx,
            }
        )

    ribbon_id += 1

ribbons_df = pd.DataFrame(ribbons_data)

# Create segment labels data
labels_data = []
for name in segments:
    arc = segment_arcs[name]
    mid_angle = (arc["start"] + arc["end"]) / 2
    label_radius = outer_radius + 45

    labels_data.append(
        {
            "segment": name,
            "x": center_x + label_radius * np.cos(mid_angle),
            "y": center_y + label_radius * np.sin(mid_angle),
        }
    )

labels_df = pd.DataFrame(labels_data)

# Create outer ring chart
outer_ring_chart = (
    alt.Chart(outer_ring_df)
    .mark_line(filled=True, strokeWidth=1, stroke="white")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, width]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, height]), axis=None),
        color=alt.Color(
            "segment:N",
            scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())),
            legend=alt.Legend(title="Modules", titleFontSize=18, labelFontSize=14, orient="right", symbolSize=200),
        ),
        detail="segment:N",
        order="order:Q",
    )
)

# Define darker shades for inner track (to distinguish from outer ring)
inner_colors = {
    "Core": "#1E4A6E",  # Darker Python Blue
    "API": "#C4A12B",  # Darker Python Yellow
    "Database": "#1E6B42",  # Darker Sea Green
    "Auth": "#A01030",  # Darker Crimson
    "Cache": "#6A4AAB",  # Darker Medium Purple
    "Queue": "#18877D",  # Darker Light Sea Green
    "Logger": "#C46B00",  # Darker Dark Orange
    "Config": "#505A64",  # Darker Slate Gray
}

# Create inner track chart with distinct styling
inner_track_chart = (
    alt.Chart(inner_track_df)
    .mark_line(filled=True, strokeWidth=2, stroke="#333333", opacity=0.85)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, width]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, height]), axis=None),
        color=alt.Color(
            "segment:N",
            scale=alt.Scale(domain=list(inner_colors.keys()), range=list(inner_colors.values())),
            legend=None,
        ),
        detail="segment:N",
        order="order:Q",
    )
)

# Create ribbons chart
ribbons_chart = (
    alt.Chart(ribbons_df)
    .mark_line(filled=True, opacity=0.5, strokeWidth=0)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, width]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, height]), axis=None),
        color=alt.Color(
            "source:N", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=None
        ),
        detail="ribbon_id:N",
        order="order:Q",
        tooltip=[
            alt.Tooltip("source:N", title="From"),
            alt.Tooltip("target:N", title="To"),
            alt.Tooltip("value:Q", title="Dependency"),
        ],
    )
)

# Create labels chart with larger font for 3600px canvas
labels_chart = (
    alt.Chart(labels_df)
    .mark_text(fontSize=22, fontWeight="bold")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, width])),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, height])),
        text="segment:N",
        color=alt.Color(
            "segment:N", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=None
        ),
    )
)

# Combine all layers
chart = (
    alt.layer(ribbons_chart, inner_track_chart, outer_ring_chart, labels_chart)
    .properties(
        width=width,
        height=height,
        title=alt.Title(text="circos-basic · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(
        padding=15,
        cornerRadius=5,
        fillColor="#FFFFFF",
        strokeColor="#CCCCCC",
        strokeWidth=1,
        titleFontSize=20,
        labelFontSize=16,
        symbolSize=250,
        offset=20,
    )
)

# Save as PNG (3600x3600 px with scale_factor=3.0)
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
