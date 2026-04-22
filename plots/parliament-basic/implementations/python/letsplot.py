# ruff: noqa: F405
"""pyplots.ai
parliament-basic: Parliament Seat Chart
Library: lets-plot | Python 3.13
Quality: pending | Created: 2025-12-30
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Data - Board of Directors composition (neutral, non-political)
groups = [
    "Finance Committee",
    "Technology Board",
    "Operations Division",
    "Research Council",
    "Marketing Team",
    "Legal Advisory",
]
seats = [85, 72, 58, 35, 95, 55]
# Colorblind-safe palette with distinct colors
colors = ["#306998", "#FFD43B", "#E69F00", "#56B4E9", "#DC143C", "#9370DB"]

total_seats = sum(seats)
n_rows = 5

# Calculate seat positions in semicircular arrangement (inline, KISS)
row_weights = np.array([i + 1 for i in range(n_rows)])
seats_per_row = (row_weights / row_weights.sum() * total_seats).astype(int)
seats_per_row[-1] += total_seats - seats_per_row.sum()  # Adjust for rounding

x_positions = []
y_positions = []
group_labels = []

group_index = 0
remaining_in_group = seats[0]

for row_idx, row_seats in enumerate(seats_per_row):
    radius = 0.5 + row_idx * 0.12  # Radius increases for outer rows
    angles = np.linspace(np.pi, 0, row_seats)  # Semicircle from left to right

    for angle in angles:
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        x_positions.append(x)
        y_positions.append(y)
        group_labels.append(groups[group_index])

        remaining_in_group -= 1
        if remaining_in_group == 0 and group_index < len(seats) - 1:
            group_index += 1
            remaining_in_group = seats[group_index]

x_coords, y_coords, group_assignment = x_positions, y_positions, group_labels

# Create DataFrame
df = pd.DataFrame({"x": x_coords, "y": y_coords, "group": group_assignment})

# Create legend labels with seat counts
group_seat_counts = dict(zip(groups, seats, strict=True))
df["group_label"] = df["group"].apply(lambda g: f"{g} ({group_seat_counts[g]})")

# Create color mapping for labels
label_colors = {f"{g} ({s})": c for g, s, c in zip(groups, seats, colors, strict=True)}
color_values = [label_colors[label] for label in df["group_label"].unique()]

# Build the plot
plot = (
    ggplot(df, aes(x="x", y="y", color="group_label"))
    + geom_point(size=5, alpha=0.9)
    + scale_color_manual(values=color_values)
    + coord_fixed(ratio=1)
    + theme_void()
    + labs(title="parliament-basic · lets-plot · pyplots.ai", color="Division (Seats)")
    + ggsize(1600, 900)
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
        plot_margin=[40, 40, 40, 40],
    )
)

# Add majority line annotation (horizontal line at y=0)
plot = plot + geom_hline(yintercept=0, color="#333333", size=1.5, alpha=0.6)

# Add total seats annotation using geom_text with a data point
annotation_df = pd.DataFrame(
    {"x": [0], "y": [-0.15], "label": [f"Total: {total_seats} seats | Majority: {total_seats // 2 + 1}"]}
)
plot = plot + geom_text(data=annotation_df, mapping=aes(x="x", y="y", label="label"), size=14, color="#333333")

# Save as PNG and HTML
current_dir = os.getcwd()
ggsave(plot, os.path.join(current_dir, "plot.png"), scale=3)
ggsave(plot, os.path.join(current_dir, "plot.html"))
