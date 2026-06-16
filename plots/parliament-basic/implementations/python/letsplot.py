""" anyplot.ai
parliament-basic: Parliament Seat Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-17
"""
# ruff: noqa: F405
"""anyplot.ai
parliament-basic: Parliament Seat Chart
Library: letsplot | Python 3.13
Quality: pending | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series ALWAYS #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data - Board of Directors composition (neutral, non-political)
parties = [
    "Finance Committee",
    "Technology Board",
    "Operations Division",
    "Research Council",
    "Marketing Team",
    "Legal Advisory",
]
seats = [85, 72, 58, 35, 95, 55]

total_seats = sum(seats)
n_rows = 5

# Calculate seat positions in semicircular arrangement
row_weights = np.array([i + 1 for i in range(n_rows)])
seats_per_row = (row_weights / row_weights.sum() * total_seats).astype(int)
seats_per_row[-1] += total_seats - seats_per_row.sum()  # Adjust for rounding

x_positions = []
y_positions = []
party_labels = []

party_index = 0
remaining_in_party = seats[0]

for row_idx, row_seats in enumerate(seats_per_row):
    radius = 0.5 + row_idx * 0.12  # Radius increases for outer rows
    angles = np.linspace(np.pi, 0, row_seats)  # Semicircle from left to right

    for angle in angles:
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        x_positions.append(x)
        y_positions.append(y)
        party_labels.append(parties[party_index])

        remaining_in_party -= 1
        if remaining_in_party == 0 and party_index < len(seats) - 1:
            party_index += 1
            remaining_in_party = seats[party_index]

# Create DataFrame
df = pd.DataFrame({"x": x_positions, "y": y_positions, "party": party_labels})

# Create legend labels with seat counts
party_seat_counts = dict(zip(parties, seats, strict=True))
df["party_label"] = df["party"].apply(lambda p: f"{p} ({party_seat_counts[p]})")

# Create color mapping (Okabe-Ito in order)
color_map = {
    f"{p} ({s})": IMPRINT[i]
    for i, (p, s) in enumerate(zip(parties, seats, strict=True))
}
color_values = [color_map[label] for label in df["party_label"].unique()]

# Theme-adaptive styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    axis_title=element_text(color=INK),
    axis_text=element_text(color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24, hjust=0.5),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT),
    legend_title=element_text(color=INK),
    plot_margin=[40, 40, 40, 40],
)

# Build the plot
plot = (
    ggplot(df, aes(x="x", y="y", color="party_label"))
    + geom_point(size=5, alpha=0.9)
    + scale_color_manual(values=color_values)
    + coord_fixed(ratio=1)
    + theme_void()
    + anyplot_theme
    + labs(title="parliament-basic · letsplot · anyplot.ai", color="Division (Seats)")
    + ggsize(1600, 900)
)

# Add majority line annotation (horizontal line at y=0)
plot = plot + geom_hline(yintercept=0, color=INK_SOFT, size=1.5, alpha=0.4)

# Add total seats annotation
annotation_df = pd.DataFrame(
    {"x": [0], "y": [-0.15], "label": [f"Total: {total_seats} seats | Majority: {total_seats // 2 + 1}"]}
)
plot = plot + geom_text(data=annotation_df, mapping=aes(x="x", y="y", label="label"), size=14, color=INK_SOFT)

# Save as PNG and HTML with theme suffix
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
