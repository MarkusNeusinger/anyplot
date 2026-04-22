""" pyplots.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import sys


sys.path = [p for p in sys.path if not p.endswith("implementations")]

import math  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    arrow,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Portfolio allocation data - top-level asset classes and holdings
np.random.seed(42)

# Main asset classes with holdings breakdown
portfolio_data = {
    "Equities": {
        "weight": 45,
        "color": "#306998",
        "holdings": [
            {"name": "Tech Stocks", "weight": 18},
            {"name": "Healthcare", "weight": 12},
            {"name": "Financials", "weight": 10},
            {"name": "Energy", "weight": 5},
        ],
    },
    "Fixed Income": {
        "weight": 30,
        "color": "#FFD43B",
        "holdings": [
            {"name": "Treasury Bonds", "weight": 15},
            {"name": "Corporate Bonds", "weight": 10},
            {"name": "Municipal Bonds", "weight": 5},
        ],
    },
    "Alternatives": {
        "weight": 15,
        "color": "#2ECC71",
        "holdings": [
            {"name": "Real Estate", "weight": 8},
            {"name": "Commodities", "weight": 4},
            {"name": "Private Equity", "weight": 3},
        ],
    },
    "Cash": {
        "weight": 10,
        "color": "#9B59B6",
        "holdings": [{"name": "Money Market", "weight": 7}, {"name": "Short-term T-Bills", "weight": 3}],
    },
}


def create_donut_segment(start_angle, end_angle, inner_radius, outer_radius, cx, cy, n_points=50):
    """Create polygon points for a donut segment."""
    gap = 0.02
    start_angle += gap
    end_angle -= gap

    points = []
    # Outer arc
    angles = np.linspace(start_angle, end_angle, n_points)
    for angle in angles:
        x = cx + outer_radius * math.cos(angle)
        y = cy + outer_radius * math.sin(angle)
        points.append((x, y))
    # Inner arc (reversed)
    for angle in reversed(angles):
        x = cx + inner_radius * math.cos(angle)
        y = cy + inner_radius * math.sin(angle)
        points.append((x, y))
    # Close
    points.append(points[0])
    return points


# Donut chart parameters
outer_radius = 100
inner_radius = 55  # Creates donut hole
center_x_main = -70
center_y = 0

# Build main donut chart (left side - asset classes)
rows = []
label_rows = []
current_angle = math.pi / 2  # Start at top

for asset_class, data in portfolio_data.items():
    weight = data["weight"]
    color = data["color"]
    sweep = (weight / 100) * 2 * math.pi
    end_angle = current_angle - sweep

    # Create donut segment
    points = create_donut_segment(end_angle, current_angle, inner_radius, outer_radius, center_x_main, center_y)
    for order, (x, y) in enumerate(points):
        rows.append({"x": x, "y": y, "segment": asset_class, "order": order, "fill": color})

    # Label position (middle of segment, middle of donut thickness)
    mid_angle = (current_angle + end_angle) / 2
    label_radius = (inner_radius + outer_radius) / 2
    label_x = center_x_main + label_radius * math.cos(mid_angle)
    label_y = center_y + label_radius * math.sin(mid_angle)
    label_rows.append({"x": label_x, "y": label_y, "label": f"{weight}%", "segment": asset_class})

    current_angle = end_angle

main_df = pd.DataFrame(rows)
main_label_df = pd.DataFrame(label_rows)

# Build detail donut chart (right side - Equities breakdown as drill-down example)
detail_center_x = 110
detail_outer_radius = 80
detail_inner_radius = 40
detail_rows = []
detail_label_rows = []

equities_data = portfolio_data["Equities"]
equities_total = equities_data["weight"]
base_color = equities_data["color"]

# Generate shades of blue for holdings
blue_shades = ["#1A3D5C", "#2A5F8F", "#4B8BBE", "#7FB3D5"]

current_angle = math.pi / 2
for i, holding in enumerate(equities_data["holdings"]):
    name = holding["name"]
    weight = holding["weight"]
    color = blue_shades[i % len(blue_shades)]
    sweep = (weight / equities_total) * 2 * math.pi
    end_angle = current_angle - sweep

    points = create_donut_segment(
        end_angle, current_angle, detail_inner_radius, detail_outer_radius, detail_center_x, center_y
    )
    for order, (x, y) in enumerate(points):
        detail_rows.append({"x": x, "y": y, "segment": name, "order": order, "fill": color})

    # Label position
    mid_angle = (current_angle + end_angle) / 2
    label_radius = (detail_inner_radius + detail_outer_radius) / 2
    label_x = detail_center_x + label_radius * math.cos(mid_angle)
    label_y = center_y + label_radius * math.sin(mid_angle)
    pct_of_total = weight  # percentage of total portfolio
    detail_label_rows.append({"x": label_x, "y": label_y, "label": f"{pct_of_total}%", "segment": name})

    current_angle = end_angle

detail_df = pd.DataFrame(detail_rows)
detail_label_df = pd.DataFrame(detail_label_rows)

# Arrow connecting main chart to detail (drill-down indicator)
arrow_data = pd.DataFrame(
    [{"x": center_x_main + outer_radius + 10, "y": 30, "xend": detail_center_x - detail_outer_radius - 10, "yend": 10}]
)

# Section titles
section_titles = pd.DataFrame(
    [
        {"x": center_x_main, "y": 130, "label": "Portfolio Allocation"},
        {"x": detail_center_x, "y": 115, "label": "Equities Breakdown"},
    ]
)

# Instruction text (simulating interactivity)
instruction_text = pd.DataFrame(
    [{"x": 20, "y": -140, "label": "Click segment to drill down (interactive feature shown as static example)"}]
)

# Center labels for donut holes
center_labels = pd.DataFrame(
    [
        {"x": center_x_main, "y": 8, "label": "Total"},
        {"x": center_x_main, "y": -12, "label": "$1.2M"},
        {"x": detail_center_x, "y": 5, "label": "45%"},
        {"x": detail_center_x, "y": -12, "label": "Equities"},
    ]
)

# Legend data (positioned at bottom)
legend_rows = []
legend_x_start = -150
legend_y = -115
legend_spacing = 85

for i, (asset_class, data) in enumerate(portfolio_data.items()):
    legend_rows.append(
        {"x": legend_x_start + i * legend_spacing, "y": legend_y, "label": asset_class, "fill": data["color"]}
    )

legend_df = pd.DataFrame(legend_rows)

# Legend color boxes
legend_box_rows = []
box_size = 12
for i, (asset_class, data) in enumerate(portfolio_data.items()):
    x_pos = legend_x_start + i * legend_spacing - 18
    y_pos = legend_y
    box_points = [
        (x_pos, y_pos - box_size / 2),
        (x_pos + box_size, y_pos - box_size / 2),
        (x_pos + box_size, y_pos + box_size / 2),
        (x_pos, y_pos + box_size / 2),
        (x_pos, y_pos - box_size / 2),
    ]
    for order, (x, y) in enumerate(box_points):
        legend_box_rows.append(
            {"x": x, "y": y, "segment": f"legend_{asset_class}", "order": order, "fill": data["color"]}
        )

legend_box_df = pd.DataFrame(legend_box_rows)

# Plot
plot = (
    ggplot()
    # Main donut chart
    + geom_polygon(aes(x="x", y="y", group="segment", fill="fill"), data=main_df, color="#FFFFFF", size=1.2, alpha=0.95)
    # Detail donut chart
    + geom_polygon(
        aes(x="x", y="y", group="segment", fill="fill"), data=detail_df, color="#FFFFFF", size=1.0, alpha=0.95
    )
    # Labels on main donut
    + geom_text(aes(x="x", y="y", label="label"), data=main_label_df, size=14, fontweight="bold", color="#FFFFFF")
    # Labels on detail donut
    + geom_text(aes(x="x", y="y", label="label"), data=detail_label_df, size=12, fontweight="bold", color="#FFFFFF")
    # Arrow for drill-down
    + geom_segment(
        aes(x="x", xend="xend", y="y", yend="yend"),
        data=arrow_data,
        color="#666666",
        size=1.5,
        linetype="dashed",
        arrow=arrow(length=0.15, type="closed"),
    )
    # Section titles
    + geom_text(aes(x="x", y="y", label="label"), data=section_titles, size=16, fontweight="bold", color="#306998")
    # Center labels
    + geom_text(aes(x="x", y="y", label="label"), data=center_labels, size=12, color="#333333")
    # Instruction text
    + geom_text(aes(x="x", y="y", label="label"), data=instruction_text, size=10, color="#888888", fontstyle="italic")
    # Legend boxes
    + geom_polygon(aes(x="x", y="y", group="segment", fill="fill"), data=legend_box_df, color="#333333", size=0.5)
    # Legend text
    + geom_text(aes(x="x", y="y", label="label"), data=legend_df, size=12, ha="left", color="#333333")
    # Fill colors directly
    + scale_fill_identity()
    # Fixed aspect ratio
    + coord_fixed(ratio=1)
    # Axis limits
    + scale_x_continuous(limits=(-220, 220))
    + scale_y_continuous(limits=(-160, 160))
    # Title
    + labs(title="pie-portfolio-interactive · plotnine · pyplots.ai")
    # Clean theme
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold", color="#306998"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#FAFAFA"),
        plot_background=element_rect(fill="#FAFAFA"),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300)
