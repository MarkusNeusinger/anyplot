""" pyplots.ai
chord-basic: Basic Chord Diagram
Library: altair 6.0.0 | Python 3.14
Quality: 77/100 | Updated: 2026-04-06
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Migration flows between continents (thousands of people, bidirectional)
flows_data = [
    {"source": "Europe", "target": "North America", "value": 45},
    {"source": "North America", "target": "Europe", "value": 30},
    {"source": "Europe", "target": "Asia", "value": 25},
    {"source": "Asia", "target": "Europe", "value": 35},
    {"source": "Asia", "target": "North America", "value": 40},
    {"source": "North America", "target": "Asia", "value": 20},
    {"source": "Africa", "target": "Europe", "value": 55},
    {"source": "Europe", "target": "Africa", "value": 15},
    {"source": "Africa", "target": "North America", "value": 25},
    {"source": "South America", "target": "North America", "value": 50},
    {"source": "North America", "target": "South America", "value": 18},
    {"source": "South America", "target": "Europe", "value": 22},
    {"source": "Oceania", "target": "Asia", "value": 30},
    {"source": "Asia", "target": "Oceania", "value": 25},
    {"source": "Oceania", "target": "Europe", "value": 12},
]

df = pd.DataFrame(flows_data)

# Target output: 4800x2700 px (16:9 aspect ratio) with scale_factor=3.0
# Internal canvas: 1600x900 pixels
width = 1600
height = 900
center_x = width / 2
center_y = height / 2

# Circle parameters
outer_radius = 350
inner_radius = 320
chord_inner_radius = 310

# Get unique entities and compute totals
entities = list(pd.concat([df["source"], df["target"]]).unique())
entity_totals = {}
for entity in entities:
    entity_totals[entity] = df[df["source"] == entity]["value"].sum() + df[df["target"] == entity]["value"].sum()

total_flow = sum(entity_totals.values())

# Color palette for entities
colors = {
    "Europe": "#306998",
    "North America": "#FFD43B",
    "Asia": "#4ECDC4",
    "Africa": "#FF6B6B",
    "South America": "#95E1D3",
    "Oceania": "#A86EDB",
}

# Calculate arc positions for each entity
gap = 0.04
total_gap = gap * len(entities)
available_angle = 2 * np.pi - total_gap

# Starting angle (top of circle)
start_angle = -np.pi / 2

entity_arcs = {}
current_angle = start_angle

for entity in entities:
    arc_angle = (entity_totals[entity] / total_flow) * available_angle
    entity_arcs[entity] = {"start": current_angle, "end": current_angle + arc_angle, "angle": arc_angle}
    current_angle += arc_angle + gap

# Create outer arc segments as closed polygons
num_arc_points = 50
arcs_data = []

for entity in entities:
    arc = entity_arcs[entity]
    angles = np.linspace(arc["start"], arc["end"], num_arc_points)

    for i, angle in enumerate(angles):
        arcs_data.append(
            {
                "entity": entity,
                "x": center_x + outer_radius * np.cos(angle),
                "y": center_y + outer_radius * np.sin(angle),
                "order": i,
            }
        )

    for i, angle in enumerate(reversed(angles)):
        arcs_data.append(
            {
                "entity": entity,
                "x": center_x + inner_radius * np.cos(angle),
                "y": center_y + inner_radius * np.sin(angle),
                "order": num_arc_points + i,
            }
        )

arcs_df = pd.DataFrame(arcs_data)

# Track offset within each entity's arc for chord placement
source_offsets = {}
target_offsets = {}

entity_source_total = {entity: df[df["source"] == entity]["value"].sum() for entity in entities}

for entity in entities:
    arc = entity_arcs[entity]
    source_fraction = entity_source_total[entity] / entity_totals[entity] if entity_totals[entity] > 0 else 0.5
    source_offsets[entity] = arc["start"]
    target_offsets[entity] = arc["start"] + source_fraction * arc["angle"]

# Create chord paths using bezier curves
num_chord_points = 40
chords_data = []
chord_id = 0

for _, row in df.iterrows():
    src = row["source"]
    tgt = row["target"]
    val = row["value"]

    src_arc = entity_arcs[src]
    src_width = (val / entity_totals[src]) * src_arc["angle"] if entity_totals[src] > 0 else 0

    tgt_arc = entity_arcs[tgt]
    tgt_width = (val / entity_totals[tgt]) * tgt_arc["angle"] if entity_totals[tgt] > 0 else 0

    src_start_angle = source_offsets[src]
    src_end_angle = src_start_angle + src_width
    source_offsets[src] = src_end_angle

    tgt_start_angle = target_offsets[tgt]
    tgt_end_angle = tgt_start_angle + tgt_width
    target_offsets[tgt] = tgt_end_angle

    chord_points = []

    # Source arc (small arc at the source entity)
    src_angles = np.linspace(src_start_angle, src_end_angle, 10)
    for angle in src_angles:
        chord_points.append(
            (center_x + chord_inner_radius * np.cos(angle), center_y + chord_inner_radius * np.sin(angle))
        )

    # Bezier from source end to target start
    for i in range(num_chord_points):
        t = i / (num_chord_points - 1)
        x = (
            (1 - t) ** 2 * (center_x + chord_inner_radius * np.cos(src_end_angle))
            + 2 * (1 - t) * t * center_x
            + t**2 * (center_x + chord_inner_radius * np.cos(tgt_start_angle))
        )
        y = (
            (1 - t) ** 2 * (center_y + chord_inner_radius * np.sin(src_end_angle))
            + 2 * (1 - t) * t * center_y
            + t**2 * (center_y + chord_inner_radius * np.sin(tgt_start_angle))
        )
        chord_points.append((x, y))

    # Target arc (small arc at the target entity)
    tgt_angles = np.linspace(tgt_start_angle, tgt_end_angle, 10)
    for angle in tgt_angles:
        chord_points.append(
            (center_x + chord_inner_radius * np.cos(angle), center_y + chord_inner_radius * np.sin(angle))
        )

    # Bezier from target end back to source start
    for i in range(num_chord_points):
        t = i / (num_chord_points - 1)
        x = (
            (1 - t) ** 2 * (center_x + chord_inner_radius * np.cos(tgt_end_angle))
            + 2 * (1 - t) * t * center_x
            + t**2 * (center_x + chord_inner_radius * np.cos(src_start_angle))
        )
        y = (
            (1 - t) ** 2 * (center_y + chord_inner_radius * np.sin(tgt_end_angle))
            + 2 * (1 - t) * t * center_y
            + t**2 * (center_y + chord_inner_radius * np.sin(src_start_angle))
        )
        chord_points.append((x, y))

    for pt_idx, (x, y) in enumerate(chord_points):
        chords_data.append(
            {
                "chord_id": f"{src}-{tgt}-{chord_id}",
                "source": src,
                "target": tgt,
                "value": val,
                "x": x,
                "y": y,
                "order": pt_idx,
            }
        )

    chord_id += 1

chords_df = pd.DataFrame(chords_data)

# Entity labels positioned outside arcs
labels_data = []
for entity in entities:
    arc = entity_arcs[entity]
    mid_angle = (arc["start"] + arc["end"]) / 2
    label_radius = outer_radius + 35

    text_angle_deg = np.degrees(mid_angle)
    if -90 < text_angle_deg < 90 or text_angle_deg > 270 or text_angle_deg < -270:
        align = "left"
    else:
        align = "right"

    labels_data.append(
        {
            "entity": entity,
            "x": center_x + label_radius * np.cos(mid_angle),
            "y": center_y + label_radius * np.sin(mid_angle),
            "align": align,
        }
    )

labels_df = pd.DataFrame(labels_data)

# Outer arc ring
arcs_chart = (
    alt.Chart(arcs_df)
    .mark_line(filled=True, strokeWidth=0)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, width]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, height]), axis=None),
        color=alt.Color(
            "entity:N",
            scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())),
            legend=alt.Legend(title="Region", titleFontSize=18, labelFontSize=14, orient="right", symbolSize=200),
        ),
        detail="entity:N",
        order="order:Q",
    )
)

# Chords as filled polygons
chords_chart = (
    alt.Chart(chords_df)
    .mark_line(filled=True, opacity=0.55, strokeWidth=0)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, width]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, height]), axis=None),
        color=alt.Color(
            "source:N", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=None
        ),
        detail="chord_id:N",
        order="order:Q",
        tooltip=[
            alt.Tooltip("source:N", title="From"),
            alt.Tooltip("target:N", title="To"),
            alt.Tooltip("value:Q", title="Flow (thousands)"),
        ],
    )
)

# Labels with data-driven horizontal alignment
label_encoding = {
    "x": alt.X("x:Q", scale=alt.Scale(domain=[0, width])),
    "y": alt.Y("y:Q", scale=alt.Scale(domain=[0, height])),
    "text": "entity:N",
    "color": alt.Color(
        "entity:N", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=None
    ),
}

labels_left = (
    alt.Chart(labels_df[labels_df["align"] == "left"])
    .mark_text(fontSize=18, fontWeight="bold", align="left")
    .encode(**label_encoding)
)

labels_right = (
    alt.Chart(labels_df[labels_df["align"] == "right"])
    .mark_text(fontSize=18, fontWeight="bold", align="right")
    .encode(**label_encoding)
)

# Combine layers
chart = (
    alt.layer(chords_chart, arcs_chart, labels_left, labels_right)
    .properties(
        width=width,
        height=height,
        title=alt.Title(text="chord-basic · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(padding=10, cornerRadius=5, fillColor="#FFFFFF", strokeColor="#DDDDDD")
)

# Save as PNG (4800x2700 px with scale_factor=3.0)
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
