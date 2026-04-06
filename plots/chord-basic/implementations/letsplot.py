""" pyplots.ai
chord-basic: Basic Chord Diagram
Library: letsplot 4.8.2 | Python 3.14
Quality: 83/100 | Updated: 2026-04-06
"""

import math

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)
from lets_plot.export import ggsave
from PIL import Image


LetsPlot.setup_html()

# Migration flow data between continents (bidirectional flows)
flows = [
    ("Asia", "Europe", 45),
    ("Asia", "North America", 38),
    ("Asia", "Africa", 12),
    ("Asia", "Oceania", 16),
    ("Europe", "North America", 28),
    ("Europe", "Asia", 22),
    ("Europe", "Africa", 15),
    ("Europe", "South America", 10),
    ("Africa", "Europe", 35),
    ("Africa", "Asia", 18),
    ("Africa", "North America", 8),
    ("North America", "Europe", 20),
    ("North America", "Asia", 15),
    ("North America", "South America", 12),
    ("South America", "North America", 25),
    ("South America", "Europe", 18),
    ("Oceania", "Asia", 14),
    ("Oceania", "Europe", 8),
]

# Get unique entities and assign distinct colors
entities = list(dict.fromkeys([f[0] for f in flows] + [f[1] for f in flows]))
colors = ["#306998", "#E69F00", "#56B4E9", "#D55E00", "#9B59B6", "#009E73"]

# Calculate total flow for each entity (in + out)
entity_totals = dict.fromkeys(entities, 0)
for src, tgt, val in flows:
    entity_totals[src] += val
    entity_totals[tgt] += val

# Calculate arc positions around the circle
total_flow = sum(entity_totals.values())
gap_angle = 0.05  # Gap between entities in radians
total_gap = gap_angle * len(entities)
available_angle = 2 * math.pi - total_gap

# Assign angular positions to each entity
entity_arcs = {}
current_angle = 0
for entity in entities:
    arc_size = (entity_totals[entity] / total_flow) * available_angle
    entity_arcs[entity] = {"start": current_angle, "end": current_angle + arc_size, "mid": current_angle + arc_size / 2}
    current_angle += arc_size + gap_angle

# Track offsets within each entity arc for chord placement
entity_offsets = {e: entity_arcs[e]["start"] for e in entities}

# Chord diagram radius
outer_radius = 1.0
inner_radius = 0.94
chord_radius = 0.92

# Build outer arc segments (the ring around the circle)
arc_data = []
n_arc_points = 60
for entity in entities:
    arc = entity_arcs[entity]
    angles = np.linspace(arc["start"], arc["end"], n_arc_points)

    # Outer edge
    for angle in angles:
        arc_data.append(
            {
                "x": outer_radius * np.cos(angle),
                "y": outer_radius * np.sin(angle),
                "entity": entity,
                "arc_id": f"{entity}_arc",
            }
        )
    # Inner edge (reversed)
    for angle in reversed(angles):
        arc_data.append(
            {
                "x": inner_radius * np.cos(angle),
                "y": inner_radius * np.sin(angle),
                "entity": entity,
                "arc_id": f"{entity}_arc",
            }
        )

arc_df = pd.DataFrame(arc_data)

# Build chord polygons connecting entities
chord_data = []
chord_id = 0

for src, tgt, val in flows:
    # Calculate angular width for this flow based on value proportion
    src_width = (val / total_flow) * available_angle
    tgt_width = (val / total_flow) * available_angle

    # Source arc segment
    src_start = entity_offsets[src]
    src_end = src_start + src_width
    entity_offsets[src] = src_end + 0.003  # Small gap between chords

    # Target arc segment
    tgt_start = entity_offsets[tgt]
    tgt_end = tgt_start + tgt_width
    entity_offsets[tgt] = tgt_end + 0.003

    # Create bezier-like chord using quadratic control points through center
    n_bezier = 50

    # Source arc points
    src_angles = np.linspace(src_start, src_end, 12)
    # Target arc points
    tgt_angles = np.linspace(tgt_end, tgt_start, 12)

    # Build chord polygon
    polygon_x = []
    polygon_y = []

    # Source arc (at chord_radius)
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
        # Quadratic bezier through origin for smooth curves
        x = (1 - t) ** 2 * src_end_x + 2 * (1 - t) * t * 0 + t**2 * tgt_start_x
        y = (1 - t) ** 2 * src_end_y + 2 * (1 - t) * t * 0 + t**2 * tgt_start_y
        polygon_x.append(x)
        polygon_y.append(y)

    # Target arc (at chord_radius)
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

# Create entity labels positioned outside the ring
label_data = []
label_radius = 1.15
for entity in entities:
    arc = entity_arcs[entity]
    mid_angle = arc["mid"]
    label_data.append(
        {
            "x": label_radius * np.cos(mid_angle),
            "y": label_radius * np.sin(mid_angle),
            "label": entity,
            "angle": math.degrees(mid_angle),
        }
    )

label_df = pd.DataFrame(label_data)

# Build plot with square format for circular visualization
plot = (
    ggplot()
    # Chords (flows between entities) - use source color for chord
    + geom_polygon(
        aes(x="x", y="y", group="chord_id", fill="source"),
        data=chord_df,
        alpha=0.55,
        color="white",
        size=0.3,
        tooltips=layer_tooltips().line("@source → @target").line("Flow|@value"),
    )
    # Outer arcs (entity segments)
    + geom_polygon(aes(x="x", y="y", group="arc_id", fill="entity"), data=arc_df, alpha=0.95, color="white", size=0.8)
    # Entity labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=18, color="#2C3E50", fontface="bold")
    + scale_fill_manual(values=colors, name="Continent")
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-1.45, 1.45))
    + scale_y_continuous(limits=(-1.45, 1.45))
    + labs(title="Continental Migration Flows · chord-basic · letsplot · pyplots.ai")
    + ggsize(1200, 1200)  # Square format for circular diagram
    + theme_void()
    + theme(
        plot_title=element_text(size=26, face="bold", color="#2C3E50"),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18, face="bold"),
        legend_position="bottom",
        panel_background=element_rect(fill="#FFFFFF", color="#FFFFFF", size=0),
        plot_background=element_rect(fill="#FFFFFF", color="#FFFFFF", size=0),
    )
)

# Save as PNG (scale 3x for 3600x3600 px output)
ggsave(plot, "plot.png", path=".", scale=3)

# Flatten transparency onto white background
img = Image.open("plot.png").convert("RGBA")
white_bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
Image.alpha_composite(white_bg, img).convert("RGB").save("plot.png")

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
