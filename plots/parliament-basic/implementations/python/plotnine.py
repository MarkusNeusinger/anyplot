""" pyplots.ai
parliament-basic: Parliament Seat Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_point,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    theme,
    theme_void,
)


# Data - fictional parliament with neutral party names
parties = [
    {"party": "Progressive Alliance", "seats": 85, "color": "#306998"},
    {"party": "Center Coalition", "seats": 72, "color": "#FFD43B"},
    {"party": "Conservative Union", "seats": 68, "color": "#4ECDC4"},
    {"party": "Green Future", "seats": 42, "color": "#2ECC71"},
    {"party": "Liberal Democrats", "seats": 35, "color": "#9B59B6"},
    {"party": "Independent Group", "seats": 18, "color": "#95A5A6"},
]

total_seats = sum(p["seats"] for p in parties)

# Calculate seat positions in semicircular arcs
# Determine optimal row configuration
n_rows = 8
inner_radius = 2.0
row_spacing = 1.0

# Calculate seats per row (more seats in outer rows)
seats_per_row = []
for i in range(n_rows):
    radius = inner_radius + i * row_spacing
    # Seats roughly proportional to arc length
    row_seats = int(np.ceil(radius * 3.5))
    seats_per_row.append(row_seats)

# Adjust to match total seats
total_calc = sum(seats_per_row)
scale = total_seats / total_calc
seats_per_row = [max(3, int(round(s * scale))) for s in seats_per_row]

# Fine-tune to exact total
diff = total_seats - sum(seats_per_row)
for i in range(abs(diff)):
    idx = i % n_rows
    if diff > 0:
        seats_per_row[n_rows - 1 - idx] += 1
    else:
        seats_per_row[n_rows - 1 - idx] -= 1

# Generate all seat positions with angles
all_seats = []
for row_idx, num_seats in enumerate(seats_per_row):
    radius = inner_radius + row_idx * row_spacing
    angles = np.linspace(np.pi * 0.95, np.pi * 0.05, num_seats)
    for angle in angles:
        all_seats.append({"angle": angle, "radius": radius, "x": radius * np.cos(angle), "y": radius * np.sin(angle)})

# Sort seats by angle (left to right) for party assignment
all_seats.sort(key=lambda s: -s["angle"])

# Assign parties to seats (left to right across the hemicycle)
seat_data = []
cumulative = 0
for seat in all_seats:
    # Find which party this seat belongs to
    running_total = 0
    for party in parties:
        running_total += party["seats"]
        if cumulative < running_total:
            seat_data.append({"x": seat["x"], "y": seat["y"], "party": party["party"]})
            break
    cumulative += 1

df = pd.DataFrame(seat_data)

# Create color mapping and legend labels
party_colors = {p["party"]: p["color"] for p in parties}
party_order = [p["party"] for p in parties]
seat_counts = {p["party"]: p["seats"] for p in parties}
legend_labels = {p: f"{p} ({seat_counts[p]})" for p in party_order}

# Convert party to categorical with order
df["party"] = pd.Categorical(df["party"], categories=party_order, ordered=True)

# Create plot
plot = (
    ggplot(df, aes(x="x", y="y", color="party"))
    + geom_point(size=5, alpha=0.95)
    + scale_color_manual(values=party_colors, labels=lambda x: [legend_labels.get(p, p) for p in x])
    + labs(title="parliament-basic · plotnine · pyplots.ai", color="")
    + coord_fixed(ratio=1)
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=26, ha="center", weight="bold", ma="center"),
        legend_title=element_text(size=16),
        legend_text=element_text(size=13),
        legend_position="bottom",
        legend_direction="horizontal",
        legend_key_size=20,
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
        plot_margin=0.1,
    )
    + guides(color=guide_legend(nrow=2, override_aes={"size": 8}))
)

# Save
plot.save("plot.png", dpi=300, width=16, height=9, verbose=False)
