""" pyplots.ai
chord-basic: Basic Chord Diagram
Library: letsplot 4.8.2 | Python 3.14
Quality: 87/100 | Updated: 2026-04-06
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
    geom_segment,
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

# Entities and colorblind-safe palette (Okabe-Ito derived, starting with Python Blue)
entities = list(dict.fromkeys([f[0] for f in flows] + [f[1] for f in flows]))
colors = ["#306998", "#E69F00", "#56B4E9", "#D55E00", "#9B59B6", "#009E73"]

# Calculate total flow for each entity (in + out)
entity_totals = dict.fromkeys(entities, 0)
for src, tgt, val in flows:
    entity_totals[src] += val
    entity_totals[tgt] += val

# Angular layout: proportional arc sizes with gaps
total_flow = sum(entity_totals.values())
gap_angle = 0.06
total_gap = gap_angle * len(entities)
available_angle = 2 * math.pi - total_gap

entity_arcs = {}
current_angle = math.pi / 2  # Start from top for better visual balance
for entity in entities:
    arc_size = (entity_totals[entity] / total_flow) * available_angle
    entity_arcs[entity] = {"start": current_angle, "end": current_angle + arc_size, "mid": current_angle + arc_size / 2}
    current_angle += arc_size + gap_angle

# Track offsets within each entity arc for chord placement
entity_offsets = {e: entity_arcs[e]["start"] for e in entities}

# Radius configuration
outer_radius = 1.0
inner_radius = 0.93
chord_radius = 0.91

# Build outer arc segments (the ring)
arc_data = []
n_arc_points = 80
for entity in entities:
    arc = entity_arcs[entity]
    angles = np.linspace(arc["start"], arc["end"], n_arc_points)
    for angle in angles:
        arc_data.append(
            {
                "x": outer_radius * np.cos(angle),
                "y": outer_radius * np.sin(angle),
                "entity": entity,
                "arc_id": f"{entity}_arc",
            }
        )
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

# Build inner ring outline for visual refinement
inner_ring_data = []
ring_angles = np.linspace(0, 2 * math.pi, 200)
for angle in ring_angles:
    inner_ring_data.append({"x": inner_radius * np.cos(angle), "y": inner_radius * np.sin(angle), "ring_id": "inner"})

# Build chord polygons
flow_values = [f[2] for f in flows]
min_flow = min(flow_values)
max_flow = max(flow_values)

chord_data = []
chord_id = 0

for src, tgt, val in flows:
    src_width = (val / total_flow) * available_angle
    tgt_width = (val / total_flow) * available_angle

    src_start = entity_offsets[src]
    src_end = src_start + src_width
    entity_offsets[src] = src_end + 0.003

    tgt_start = entity_offsets[tgt]
    tgt_end = tgt_start + tgt_width
    entity_offsets[tgt] = tgt_end + 0.003

    n_bezier = 50
    src_angles = np.linspace(src_start, src_end, 12)
    tgt_angles = np.linspace(tgt_end, tgt_start, 12)

    polygon_x = []
    polygon_y = []

    # Source arc at chord_radius
    for angle in src_angles:
        polygon_x.append(chord_radius * np.cos(angle))
        polygon_y.append(chord_radius * np.sin(angle))

    # Bezier curve source → target
    src_end_x = chord_radius * np.cos(src_end)
    src_end_y = chord_radius * np.sin(src_end)
    tgt_start_x = chord_radius * np.cos(tgt_start)
    tgt_start_y = chord_radius * np.sin(tgt_start)

    for i in range(1, n_bezier):
        t = i / n_bezier
        x = (1 - t) ** 2 * src_end_x + 2 * (1 - t) * t * 0 + t**2 * tgt_start_x
        y = (1 - t) ** 2 * src_end_y + 2 * (1 - t) * t * 0 + t**2 * tgt_start_y
        polygon_x.append(x)
        polygon_y.append(y)

    # Target arc at chord_radius
    for angle in tgt_angles:
        polygon_x.append(chord_radius * np.cos(angle))
        polygon_y.append(chord_radius * np.sin(angle))

    # Bezier curve target → source
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

    alpha_scaled = 0.25 + 0.55 * (val - min_flow) / (max_flow - min_flow)

    for x, y in zip(polygon_x, polygon_y, strict=False):
        chord_data.append(
            {
                "x": x,
                "y": y,
                "chord_id": f"chord_{chord_id}",
                "source": src,
                "target": tgt,
                "value": val,
                "alpha_val": alpha_scaled,
            }
        )
    chord_id += 1

chord_df = pd.DataFrame(chord_data)

# Three-tier chord split for visual hierarchy
flow_threshold_high = min_flow + 0.66 * (max_flow - min_flow)
flow_threshold_mid = min_flow + 0.33 * (max_flow - min_flow)
chord_high = chord_df[chord_df["value"] >= flow_threshold_high]
chord_mid = chord_df[(chord_df["value"] >= flow_threshold_mid) & (chord_df["value"] < flow_threshold_high)]
chord_low = chord_df[chord_df["value"] < flow_threshold_mid]

# Entity labels with adaptive positioning to avoid crowding
label_data = []
for entity in entities:
    arc = entity_arcs[entity]
    mid_angle = arc["mid"]
    arc_size = arc["end"] - arc["start"]
    # Larger offset for small arcs to prevent label crowding
    label_radius = 1.14 + max(0, 0.10 * (1.0 - arc_size / 0.7))
    label_data.append({"x": label_radius * np.cos(mid_angle), "y": label_radius * np.sin(mid_angle), "label": entity})

label_df = pd.DataFrame(label_data)

# Tick marks connecting arcs to labels (visual refinement)
tick_data = []
for entity in entities:
    arc = entity_arcs[entity]
    mid_angle = arc["mid"]
    tick_data.append(
        {
            "x": outer_radius * np.cos(mid_angle),
            "y": outer_radius * np.sin(mid_angle),
            "xend": 1.08 * np.cos(mid_angle),
            "yend": 1.08 * np.sin(mid_angle),
        }
    )

tick_df = pd.DataFrame(tick_data)

# Annotation for dominant flow — data storytelling (positioned at center)
top_flow = max(flows, key=lambda f: f[2])
annotation_df = pd.DataFrame(
    [{"x": 0.0, "y": -0.02, "label": f"Strongest: {top_flow[0]}→{top_flow[1]} ({top_flow[2]})"}]
)

# Build the plot
plot = (
    ggplot()
    # Low-magnitude chords (background layer)
    + geom_polygon(
        aes(x="x", y="y", group="chord_id", fill="source"),
        data=chord_low,
        alpha=0.2,
        color="white",
        size=0.15,
        tooltips=layer_tooltips().line("@source → @target").line("Flow|@value"),
    )
    # Mid-magnitude chords
    + geom_polygon(
        aes(x="x", y="y", group="chord_id", fill="source"),
        data=chord_mid,
        alpha=0.45,
        color="white",
        size=0.2,
        tooltips=layer_tooltips().line("@source → @target").line("Flow|@value"),
    )
    # High-magnitude chords (foreground, most prominent)
    + geom_polygon(
        aes(x="x", y="y", group="chord_id", fill="source"),
        data=chord_high,
        alpha=0.75,
        color="white",
        size=0.25,
        tooltips=layer_tooltips().line("@source → @target").line("Flow|@value"),
    )
    # Outer arc segments
    + geom_polygon(aes(x="x", y="y", group="arc_id", fill="entity"), data=arc_df, alpha=0.95, color="#FAFAFA", size=0.5)
    # Tick marks from arcs to labels
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=tick_df, color="#90A4AE", size=0.6)
    # Entity labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=18, color="#263238", fontface="bold")
    # Dominant flow annotation for storytelling
    + geom_text(aes(x="x", y="y", label="label"), data=annotation_df, size=11, color="#37474F", fontface="bold")
    # Scales and coordinates
    + scale_fill_manual(values=colors, name="Continent")
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-1.6, 1.6))
    + scale_y_continuous(limits=(-1.6, 1.6))
    + labs(
        title="chord-basic · letsplot · pyplots.ai",
        caption="Width proportional to migration flow magnitude  ·  Opacity indicates relative strength",
    )
    + ggsize(1200, 1200)
    + theme_void()
    + theme(
        plot_title=element_text(size=28, face="bold", color="#1A237E"),
        plot_caption=element_text(size=13, color="#78909C", face="italic"),
        legend_text=element_text(size=16, color="#37474F"),
        legend_title=element_text(size=18, face="bold", color="#263238"),
        legend_position=[0.5, 0.04],
        legend_justification=[0.5, 0.0],
        legend_direction="horizontal",
        legend_background=element_rect(fill="#FFFFFF", color="#E0E0E0", size=0.5),
        panel_background=element_rect(fill="#FAFAFA", color="#FAFAFA", size=0),
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA", size=0),
        plot_margin=[40, 20, 20, 20],
    )
)

# Save PNG (scale 3x → 3600x3600 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Flatten transparency onto white background
img = Image.open("plot.png").convert("RGBA")
white_bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
Image.alpha_composite(white_bg, img).convert("RGB").save("plot.png")

# Save interactive HTML export
ggsave(plot, "plot.html", path=".")
