""" pyplots.ai
circos-basic: Circos Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_path,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Data - Trade flows between world regions (bidirectional connections)
# Represents export relationships between major economic regions
flows = [
    ("Asia", "Europe", 85),
    ("Asia", "North America", 72),
    ("Asia", "Middle East", 45),
    ("Asia", "Africa", 28),
    ("Europe", "North America", 55),
    ("Europe", "Asia", 48),
    ("Europe", "Africa", 32),
    ("Europe", "South America", 22),
    ("North America", "Asia", 42),
    ("North America", "Europe", 38),
    ("North America", "South America", 35),
    ("South America", "Europe", 28),
    ("South America", "North America", 25),
    ("South America", "Asia", 18),
    ("Middle East", "Asia", 65),
    ("Middle East", "Europe", 42),
    ("Africa", "Europe", 38),
    ("Africa", "Asia", 22),
]

# Get unique segments and assign colors
segments = list(dict.fromkeys([f[0] for f in flows] + [f[1] for f in flows]))
colors = {
    "Asia": "#306998",  # Python Blue
    "Europe": "#FFD43B",  # Python Yellow
    "North America": "#2ECC71",  # Green (more distinct from South America)
    "South America": "#E67E22",  # Orange (clearly different from North America)
    "Middle East": "#E74C3C",  # Red
    "Africa": "#9B59B6",  # Purple
}

# Calculate total flow for each segment (incoming + outgoing)
segment_totals = dict.fromkeys(segments, 0)
for src, tgt, val in flows:
    segment_totals[src] += val
    segment_totals[tgt] += val

total_flow = sum(segment_totals.values())

# Calculate arc positions around the circle
gap_angle = 0.08  # Gap between segments in radians
total_gap = gap_angle * len(segments)
available_angle = 2 * np.pi - total_gap

# Assign angular positions to each segment (start at top)
segment_arcs = {}
current_angle = -np.pi / 2  # Start at top
for segment in segments:
    arc_size = (segment_totals[segment] / total_flow) * available_angle
    segment_arcs[segment] = {
        "start": current_angle,
        "end": current_angle + arc_size,
        "mid": current_angle + arc_size / 2,
    }
    current_angle += arc_size + gap_angle

# Radii for the circos plot
outer_radius = 1.0
inner_radius = 0.92
chord_radius = 0.88
track_outer = 0.82  # Inner track for additional data
track_inner = 0.72

# Build outer arc segments (the ring around the circle)
arc_data = []
n_arc_points = 80
arc_id = 0
for segment in segments:
    arc = segment_arcs[segment]
    angles = np.linspace(arc["start"], arc["end"], n_arc_points)

    # Outer edge
    for angle in angles:
        arc_data.append(
            {
                "x": outer_radius * np.cos(angle),
                "y": outer_radius * np.sin(angle),
                "segment": segment,
                "arc_id": f"arc_{arc_id}",
            }
        )
    # Inner edge (reversed to close polygon)
    for angle in reversed(angles):
        arc_data.append(
            {
                "x": inner_radius * np.cos(angle),
                "y": inner_radius * np.sin(angle),
                "segment": segment,
                "arc_id": f"arc_{arc_id}",
            }
        )
    arc_id += 1

arc_df = pd.DataFrame(arc_data)

# Build inner data track (concentric ring showing segment "weight")
# This represents additional data layer as mentioned in spec
track_data = []
track_id = 0
for segment in segments:
    arc = segment_arcs[segment]
    angles = np.linspace(arc["start"], arc["end"], n_arc_points)

    for angle in angles:
        track_data.append(
            {
                "x": track_outer * np.cos(angle),
                "y": track_outer * np.sin(angle),
                "segment": segment,
                "track_id": f"track_{track_id}",
            }
        )
    for angle in reversed(angles):
        track_data.append(
            {
                "x": track_inner * np.cos(angle),
                "y": track_inner * np.sin(angle),
                "segment": segment,
                "track_id": f"track_{track_id}",
            }
        )
    track_id += 1

track_df = pd.DataFrame(track_data)

# Track offsets within each segment for chord placement
segment_offsets = {s: segment_arcs[s]["start"] for s in segments}

# Build ribbon/chord polygons connecting segments
chord_data = []
chord_id = 0
n_bezier = 50

for src, tgt, val in flows:
    # Calculate angular width for this connection
    src_width = (val / total_flow) * available_angle * 0.5
    tgt_width = (val / total_flow) * available_angle * 0.5

    # Source arc segment position
    src_start = segment_offsets[src]
    src_end = src_start + src_width
    segment_offsets[src] = src_end + 0.005

    # Target arc segment position
    tgt_start = segment_offsets[tgt]
    tgt_end = tgt_start + tgt_width
    segment_offsets[tgt] = tgt_end + 0.005

    # Build chord polygon with bezier curves
    polygon_x = []
    polygon_y = []

    # Source arc (at chord_radius)
    src_angles = np.linspace(src_start, src_end, 15)
    for angle in src_angles:
        polygon_x.append(chord_radius * np.cos(angle))
        polygon_y.append(chord_radius * np.sin(angle))

    # Bezier curve from source end to target start
    src_end_x = chord_radius * np.cos(src_end)
    src_end_y = chord_radius * np.sin(src_end)
    tgt_start_x = chord_radius * np.cos(tgt_start)
    tgt_start_y = chord_radius * np.sin(tgt_start)

    for i in range(1, n_bezier):
        t = i / n_bezier
        # Quadratic bezier through origin for smooth ribbon
        x = (1 - t) ** 2 * src_end_x + 2 * (1 - t) * t * 0 + t**2 * tgt_start_x
        y = (1 - t) ** 2 * src_end_y + 2 * (1 - t) * t * 0 + t**2 * tgt_start_y
        polygon_x.append(x)
        polygon_y.append(y)

    # Target arc (at chord_radius)
    tgt_angles = np.linspace(tgt_start, tgt_end, 15)
    for angle in tgt_angles:
        polygon_x.append(chord_radius * np.cos(angle))
        polygon_y.append(chord_radius * np.sin(angle))

    # Bezier curve back from target end to source start
    tgt_end_x = chord_radius * np.cos(tgt_end)
    tgt_end_y = chord_radius * np.sin(tgt_end)
    src_start_x = chord_radius * np.cos(src_start)
    src_start_y = chord_radius * np.sin(src_start)

    for i in range(1, n_bezier):
        t = i / n_bezier
        x = (1 - t) ** 2 * tgt_end_x + 2 * (1 - t) * t * 0 + t**2 * src_start_x
        y = (1 - t) ** 2 * tgt_end_y + 2 * (1 - t) * t * 0 + t**2 * src_start_y
        polygon_x.append(x)
        polygon_y.append(y)

    # Add to dataframe
    for x, y in zip(polygon_x, polygon_y, strict=False):
        chord_data.append({"x": x, "y": y, "chord_id": f"chord_{chord_id}", "source": src, "target": tgt, "value": val})

    chord_id += 1

chord_df = pd.DataFrame(chord_data)

# Create segment labels positioned outside the ring
label_data = []
label_radius = 1.15
for segment in segments:
    arc = segment_arcs[segment]
    mid_angle = arc["mid"]
    label_data.append(
        {
            "x": label_radius * np.cos(mid_angle),
            "y": label_radius * np.sin(mid_angle),
            "label": segment,
            "segment": segment,
        }
    )

label_df = pd.DataFrame(label_data)

# Create circular gridlines for visual reference
grid_rows = []
for radius in [0.5, 0.7]:
    grid_angles = np.linspace(0, 2 * np.pi, 100)
    for angle in grid_angles:
        grid_rows.append({"x": radius * np.cos(angle), "y": radius * np.sin(angle), "radius": radius})

grid_df = pd.DataFrame(grid_rows)

# Build the circos plot
plot = (
    ggplot()
    # Background gridlines (subtle circular references)
    + geom_path(aes(x="x", y="y", group="radius"), data=grid_df, color="#EEEEEE", size=0.3, alpha=0.5)
    # Ribbons/chords connecting segments (drawn first, behind arcs)
    + geom_polygon(
        aes(x="x", y="y", group="chord_id", fill="source"), data=chord_df, alpha=0.5, color="white", size=0.15
    )
    # Inner data track (concentric ring)
    + geom_polygon(
        aes(x="x", y="y", group="track_id", fill="segment"), data=track_df, alpha=0.4, color="white", size=0.3
    )
    # Outer arc segments (the main circular ring)
    + geom_polygon(aes(x="x", y="y", group="arc_id", fill="segment"), data=arc_df, alpha=0.95, color="white", size=0.8)
    # Segment labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=14, color="#2C3E50", fontweight="bold")
    # Color scale
    + scale_fill_manual(values=colors, name="Region")
    # Equal aspect ratio for proper circles
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-1.6, 1.6), expand=(0, 0))
    + scale_y_continuous(limits=(-1.5, 1.6), expand=(0, 0))
    # Title
    + labs(title="circos-basic · plotnine · pyplots.ai")
    # Clean theme for circular plot
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", fontweight="bold", margin={"b": 20}),
        plot_margin=0.08,
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_blank(),
        plot_background=element_blank(),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
    )
)

# Save as PNG (3600x3600 px at 300 dpi = 12x12 inches)
plot.save("plot.png", dpi=300)
