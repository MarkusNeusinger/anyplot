""" pyplots.ai
circos-basic: Circos Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import math

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

np.random.seed(42)

# Genomic-style data: 8 chromosomes with connections and expression data
chromosomes = ["Chr1", "Chr2", "Chr3", "Chr4", "Chr5", "Chr6", "Chr7", "Chr8"]
n_chromosomes = len(chromosomes)

# Chromosome sizes (proportional to their arc length)
chr_sizes = [120, 95, 85, 75, 70, 65, 55, 50]  # Megabases

# Connections between chromosomes (inter-chromosomal rearrangements)
connections = [
    ("Chr1", "Chr3", 25),
    ("Chr1", "Chr5", 18),
    ("Chr2", "Chr4", 22),
    ("Chr2", "Chr7", 15),
    ("Chr3", "Chr6", 20),
    ("Chr4", "Chr8", 12),
    ("Chr5", "Chr7", 16),
    ("Chr6", "Chr8", 10),
    ("Chr1", "Chr8", 8),
    ("Chr3", "Chr5", 14),
]

# Track data: expression levels for each chromosome (inner tracks)
expression_track1 = [0.85, 0.72, 0.93, 0.68, 0.81, 0.55, 0.78, 0.62]  # Normalized 0-1
expression_track2 = [0.45, 0.82, 0.38, 0.91, 0.55, 0.73, 0.42, 0.88]  # Normalized 0-1

# Colors for chromosomes (colorblind-friendly palette)
chr_colors = ["#306998", "#FFD43B", "#27AE60", "#E74C3C", "#9B59B6", "#1ABC9C", "#F39C12", "#3498DB"]

# Calculate angular positions for each chromosome
total_size = sum(chr_sizes)
gap_angle = 0.08  # Gap between chromosomes in radians
total_gap = gap_angle * n_chromosomes
available_angle = 2 * math.pi - total_gap

# Assign angular positions to each chromosome
chr_arcs = {}
current_angle = 0
for i, chrom in enumerate(chromosomes):
    arc_size = (chr_sizes[i] / total_size) * available_angle
    chr_arcs[chrom] = {
        "start": current_angle,
        "end": current_angle + arc_size,
        "mid": current_angle + arc_size / 2,
        "size": chr_sizes[i],
        "color": chr_colors[i],
        "idx": i,
    }
    current_angle += arc_size + gap_angle

# Radii for different elements
outer_radius = 1.0  # Outer chromosome ring
inner_ring_radius = 0.92  # Inner edge of chromosome ring
track1_outer = 0.88  # Expression track 1
track1_inner = 0.78
track2_outer = 0.74  # Expression track 2
track2_inner = 0.64
chord_radius = 0.60  # Ribbons connecting chromosomes

# Build outer arc segments (chromosome ring)
arc_data = []
n_arc_points = 50

for chrom in chromosomes:
    arc = chr_arcs[chrom]
    angles = np.linspace(arc["start"], arc["end"], n_arc_points)

    # Outer edge
    for angle in angles:
        arc_data.append(
            {
                "x": outer_radius * np.cos(angle),
                "y": outer_radius * np.sin(angle),
                "chromosome": chrom,
                "arc_id": f"{chrom}_arc",
            }
        )
    # Inner edge (reversed)
    for angle in reversed(angles):
        arc_data.append(
            {
                "x": inner_ring_radius * np.cos(angle),
                "y": inner_ring_radius * np.sin(angle),
                "chromosome": chrom,
                "arc_id": f"{chrom}_arc",
            }
        )

arc_df = pd.DataFrame(arc_data)

# Build track 1 data (bar heights based on expression)
track1_data = []
for chrom in chromosomes:
    arc = chr_arcs[chrom]
    expr = expression_track1[arc["idx"]]

    # Create arc segment for this track
    angles = np.linspace(arc["start"], arc["end"], n_arc_points)
    bar_height = track1_inner + (track1_outer - track1_inner) * expr

    # Outer edge at expression level
    for angle in angles:
        track1_data.append(
            {
                "x": bar_height * np.cos(angle),
                "y": bar_height * np.sin(angle),
                "chromosome": chrom,
                "track_id": f"{chrom}_track1",
            }
        )
    # Inner edge
    for angle in reversed(angles):
        track1_data.append(
            {
                "x": track1_inner * np.cos(angle),
                "y": track1_inner * np.sin(angle),
                "chromosome": chrom,
                "track_id": f"{chrom}_track1",
            }
        )

track1_df = pd.DataFrame(track1_data)

# Build track 2 data
track2_data = []
for chrom in chromosomes:
    arc = chr_arcs[chrom]
    expr = expression_track2[arc["idx"]]

    angles = np.linspace(arc["start"], arc["end"], n_arc_points)
    bar_height = track2_inner + (track2_outer - track2_inner) * expr

    # Outer edge at expression level
    for angle in angles:
        track2_data.append(
            {
                "x": bar_height * np.cos(angle),
                "y": bar_height * np.sin(angle),
                "chromosome": chrom,
                "track_id": f"{chrom}_track2",
            }
        )
    # Inner edge
    for angle in reversed(angles):
        track2_data.append(
            {
                "x": track2_inner * np.cos(angle),
                "y": track2_inner * np.sin(angle),
                "chromosome": chrom,
                "track_id": f"{chrom}_track2",
            }
        )

track2_df = pd.DataFrame(track2_data)

# Build ribbon connections between chromosomes
ribbon_data = []
ribbon_id = 0

# Track offsets for connection placement within each chromosome
chr_offsets = {chrom: chr_arcs[chrom]["start"] for chrom in chromosomes}

for src, tgt, val in connections:
    src_arc = chr_arcs[src]
    tgt_arc = chr_arcs[tgt]

    # Calculate angular width proportional to connection value
    width_factor = val / 100.0  # Normalize
    src_width = (src_arc["end"] - src_arc["start"]) * width_factor * 0.8
    tgt_width = (tgt_arc["end"] - tgt_arc["start"]) * width_factor * 0.8

    # Source position
    src_start = chr_offsets[src]
    src_end = src_start + src_width
    chr_offsets[src] = src_end + 0.01

    # Target position
    tgt_start = chr_offsets[tgt]
    tgt_end = tgt_start + tgt_width
    chr_offsets[tgt] = tgt_end + 0.01

    # Create bezier-like ribbon
    n_bezier = 40
    polygon_x = []
    polygon_y = []

    # Source arc at chord radius
    src_angles = np.linspace(src_start, src_end, 10)
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
        x = (1 - t) ** 2 * src_end_x + 2 * (1 - t) * t * 0 + t**2 * tgt_start_x
        y = (1 - t) ** 2 * src_end_y + 2 * (1 - t) * t * 0 + t**2 * tgt_start_y
        polygon_x.append(x)
        polygon_y.append(y)

    # Target arc (reversed)
    tgt_angles = np.linspace(tgt_end, tgt_start, 10)
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

    # Add points to dataframe
    for x, y in zip(polygon_x, polygon_y, strict=False):
        ribbon_data.append({"x": x, "y": y, "ribbon_id": f"ribbon_{ribbon_id}", "source": src})

    ribbon_id += 1

ribbon_df = pd.DataFrame(ribbon_data)

# Create chromosome labels
label_data = []
label_radius = 1.12
for chrom in chromosomes:
    arc = chr_arcs[chrom]
    mid_angle = arc["mid"]
    label_data.append({"x": label_radius * np.cos(mid_angle), "y": label_radius * np.sin(mid_angle), "label": chrom})

label_df = pd.DataFrame(label_data)

# Build the circos plot
plot = (
    ggplot()
    # Ribbons connecting chromosomes (innermost, with transparency)
    + geom_polygon(
        aes(x="x", y="y", group="ribbon_id", fill="source"), data=ribbon_df, alpha=0.45, color="white", size=0.2
    )
    # Expression track 2 (inner track)
    + geom_polygon(
        aes(x="x", y="y", group="track_id", fill="chromosome"), data=track2_df, alpha=0.65, color="white", size=0.3
    )
    # Expression track 1 (middle track)
    + geom_polygon(
        aes(x="x", y="y", group="track_id", fill="chromosome"), data=track1_df, alpha=0.8, color="white", size=0.3
    )
    # Outer chromosome ring
    + geom_polygon(
        aes(x="x", y="y", group="arc_id", fill="chromosome"), data=arc_df, alpha=0.95, color="white", size=0.8
    )
    # Chromosome labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=14, color="#2C3E50", fontface="bold")
    + scale_fill_manual(values=chr_colors, name="Chromosome")
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-1.45, 1.45))
    + scale_y_continuous(limits=(-1.45, 1.45))
    + labs(title="Genomic Rearrangements · circos-basic · letsplot · pyplots.ai")
    + ggsize(1200, 1200)  # Square format for circular diagram
    + theme(
        plot_title=element_text(size=26, face="bold", color="#2C3E50"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16, face="bold"),
        legend_position="bottom",
        panel_background=element_blank(),
        plot_background=element_blank(),
    )
)

# Save as PNG (scale 3x for 3600x3600 px output)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
