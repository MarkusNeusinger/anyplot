"""anyplot.ai
donut-nested: Nested Donut Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-08-18
"""

import os
import sys


# Remove the script's directory from sys.path to avoid circular imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir]

import math  # noqa: E402

import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BORDER_COLOR = "#E8E6DC" if THEME == "light" else "#353531"

# Imprint categorical palette (positions 1-5) — regions are an abstract
# category, so canonical ordinal order applies (default-style-guide.md
# "Semantic Exception": abstract categories keep canonical order).
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data - Global technology revenue ($M) by region (inner ring) and product
# line (outer ring). Region count (5) and children-per-region (2-5) diverge
# from the 4-department budget scenario used by sibling library implementations.
data = {
    "North America": [("Software", 420), ("Hardware", 260), ("Cloud Services", 240), ("Support", 130)],
    "Asia Pacific": [
        ("Software", 310),
        ("Hardware", 220),
        ("Cloud Services", 180),
        ("Consulting", 110),
        ("Support", 70),
    ],
    "Europe": [("Software", 300), ("Cloud Services", 270), ("Hardware", 190)],
    "Latin America": [("Software", 180), ("Hardware", 140)],
    "Middle East & Africa": [("Hardware", 150), ("Cloud Services", 90), ("Support", 70)],
}


def lighten_hex(hex_color, amount):
    """Blend a hex color toward white by `amount` (0-1) for a tonal family member."""
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    r = round(r + (255 - r) * amount)
    g = round(g + (255 - g) * amount)
    b = round(b + (255 - b) * amount)
    return f"#{r:02X}{g:02X}{b:02X}"


# Imprint families - each parent's Imprint hue plus lighter tonal shades for
# its own children in the outer ring (consistent hue, varying lightness).
color_families = {}
for parent, base_color in zip(data.keys(), IMPRINT_PALETTE, strict=True):
    children = data[parent]
    n_children = len(children)
    tints = [lighten_hex(base_color, (i / n_children) * 0.6) for i in range(n_children)]
    color_families[parent] = (base_color, tints)

# Calculate totals for each parent
parent_totals = {parent: sum(v for _, v in children) for parent, children in data.items()}
grand_total = sum(parent_totals.values())

# Ring dimensions
inner_ring_inner = 60  # Inner donut hole
inner_ring_outer = 100  # Inner ring outer radius
outer_ring_inner = 110  # Outer ring inner radius (gap for separation)
outer_ring_outer = 150  # Outer ring outer radius


def create_annular_segment(start_angle, end_angle, inner_radius, outer_radius, n_points=50):
    """Create polygon points for an annular (donut) segment."""
    # Add small gap between segments
    gap = 0.02
    start_angle += gap
    end_angle -= gap

    points = []
    # Inner arc (from start to end)
    for angle in [start_angle + (end_angle - start_angle) * i / (n_points - 1) for i in range(n_points)]:
        points.append((inner_radius * math.cos(angle), inner_radius * math.sin(angle)))

    # Outer arc (from end back to start)
    for angle in [end_angle + (start_angle - end_angle) * i / (n_points - 1) for i in range(n_points)]:
        points.append((outer_radius * math.cos(angle), outer_radius * math.sin(angle)))

    # Close the polygon
    points.append(points[0])
    return points


# Build polygon data for inner ring (regions)
inner_rows = []
current_angle = math.pi / 2  # Start at top (12 o'clock)

parent_angles = {}  # Track start/end angles for each parent

for parent in data.keys():
    parent_total = parent_totals[parent]
    sweep = (parent_total / grand_total) * 2 * math.pi
    end_angle = current_angle - sweep  # Clockwise

    parent_angles[parent] = (current_angle, end_angle)

    points = create_annular_segment(end_angle, current_angle, inner_ring_inner, inner_ring_outer)
    for order, (x, y) in enumerate(points):
        inner_rows.append({"x": x, "y": y, "segment": parent, "order": order, "fill": color_families[parent][0]})

    current_angle = end_angle

inner_df = pd.DataFrame(inner_rows)

# Build polygon data for outer ring (product lines)
outer_rows = []

for parent, children in data.items():
    parent_start, parent_end = parent_angles[parent]
    parent_total = parent_totals[parent]

    child_current_angle = parent_start
    child_colors = color_families[parent][1]

    for i, (child_name, child_value) in enumerate(children):
        child_sweep = (child_value / parent_total) * (parent_start - parent_end)
        child_end_angle = child_current_angle - child_sweep

        points = create_annular_segment(child_end_angle, child_current_angle, outer_ring_inner, outer_ring_outer)
        segment_id = f"{parent}_{child_name}"
        color = child_colors[i]

        for order, (x, y) in enumerate(points):
            outer_rows.append({"x": x, "y": y, "segment": segment_id, "order": order, "fill": color})

        child_current_angle = child_end_angle

outer_df = pd.DataFrame(outer_rows)

# Create labels for inner ring (region name + revenue share). Name and value
# are nudged apart by a fixed cartesian dy (screen-space stacking) rather than
# a radius difference — a radius-based offset collapses to near-zero vertical
# separation for segments near the 3/9 o'clock angle, since it projects mostly
# horizontally there.
inner_label_radius = (inner_ring_inner + inner_ring_outer) / 2
label_dy = 9

inner_name_labels = []
inner_value_labels = []
for parent in data.keys():
    start_angle, end_angle = parent_angles[parent]
    mid_angle = (start_angle + end_angle) / 2
    share = parent_totals[parent] / grand_total * 100
    label_x = inner_label_radius * math.cos(mid_angle)
    label_y = inner_label_radius * math.sin(mid_angle)
    inner_name_labels.append({"x": label_x, "y": label_y + label_dy, "label": parent})
    inner_value_labels.append(
        {"x": label_x, "y": label_y - label_dy, "label": f"${parent_totals[parent]:,}M · {share:.0f}%"}
    )

inner_name_df = pd.DataFrame(inner_name_labels)
inner_value_df = pd.DataFrame(inner_value_labels)

# Create labels for outer ring (larger segments only; smaller ones stay unlabeled)
outer_labels = []
label_threshold = 100  # $M

for parent, children in data.items():
    parent_start, parent_end = parent_angles[parent]
    parent_total = parent_totals[parent]

    child_current_angle = parent_start

    for child_name, child_value in children:
        child_sweep = (child_value / parent_total) * (parent_start - parent_end)
        child_end_angle = child_current_angle - child_sweep

        if child_value >= label_threshold:
            mid_angle = (child_current_angle + child_end_angle) / 2
            label_radius = (outer_ring_inner + outer_ring_outer) / 2
            outer_labels.append(
                {"x": label_radius * math.cos(mid_angle), "y": label_radius * math.sin(mid_angle), "label": child_name}
            )

        child_current_angle = child_end_angle

outer_label_df = pd.DataFrame(outer_labels)

# Title — mandated format only; the region/revenue story is already told by
# the inner-ring labels, so no descriptive prefix is needed here.
title_text = "donut-nested · python · plotnine · anyplot.ai"
title_ratio = 67 / len(title_text) if len(title_text) > 67 else 1.0
title_fontsize = max(round(12 * title_ratio), 8)

# Plot
plot = (
    ggplot()
    # Inner ring (regions)
    + geom_polygon(
        aes(x="x", y="y", group="segment", fill="fill"), data=inner_df, color=BORDER_COLOR, size=0.5, alpha=0.95
    )
    # Outer ring (product lines)
    + geom_polygon(
        aes(x="x", y="y", group="segment", fill="fill"), data=outer_df, color=BORDER_COLOR, size=0.5, alpha=0.9
    )
    # Inner ring labels (region name + revenue share, as two independently
    # positioned rows rather than a multi-line string)
    + geom_text(aes(x="x", y="y", label="label"), data=inner_name_df, size=9, fontweight="bold", color=INK)
    + geom_text(aes(x="x", y="y", label="label"), data=inner_value_df, size=7, color=INK_SOFT)
    # Outer ring labels (product line names for large-enough segments)
    + geom_text(aes(x="x", y="y", label="label"), data=outer_label_df, size=7, color=INK_SOFT)
    # Use fill colors directly
    + scale_fill_identity()
    # Fixed aspect ratio for proper circles
    + coord_fixed(ratio=1)
    # Axis limits with padding
    + scale_x_continuous(limits=(-180, 180))
    + scale_y_continuous(limits=(-180, 180))
    # Title
    + labs(title=title_text)
    # Clean theme with adaptive background — canonical 2400x2400 square canvas
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=title_fontsize, ha="center", color=INK),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="none",
    )
)

# Save
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"plot-{THEME}.png")
plot.save(output_path, dpi=400, width=6, height=6, units="in")
