""" pyplots.ai
parliament-basic: Parliament Seat Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


np.random.seed(42)

# Data: Fictional parliament with 300 seats
parties = [
    {"party": "Progressive", "seats": 95, "color": "#306998"},
    {"party": "Conservative", "seats": 82, "color": "#FFD43B"},
    {"party": "Green", "seats": 45, "color": "#2CA02C"},
    {"party": "Liberal", "seats": 38, "color": "#FF7F0E"},
    {"party": "Social Dem.", "seats": 28, "color": "#9467BD"},
    {"party": "Independent", "seats": 12, "color": "#8C564B"},
]

total_seats = sum(p["seats"] for p in parties)

# Generate seat positions in semicircular arcs
# Calculate number of rows based on total seats (more seats = more rows)
n_rows = 5  # For 300 seats
inner_radius = 3.0
row_spacing = 1.0

# Calculate seats per row (more seats in outer rows)
row_weights = [(inner_radius + i * row_spacing) for i in range(n_rows)]
total_weight = sum(row_weights)
seats_per_row = [max(1, int(total_seats * w / total_weight)) for w in row_weights]

# Adjust to match total exactly
diff = total_seats - sum(seats_per_row)
for i in range(abs(diff)):
    if diff > 0:
        seats_per_row[-(i % n_rows) - 1] += 1
    else:
        seats_per_row[i % n_rows] -= 1

# Generate positions for each seat
all_seats = []
seat_idx = 0

for row_idx, n_seats_in_row in enumerate(seats_per_row):
    radius = inner_radius + row_idx * row_spacing
    angles = np.linspace(np.pi, 0, n_seats_in_row)
    for angle in angles:
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        all_seats.append({"x": x, "y": y, "seat_idx": seat_idx, "angle": angle})
        seat_idx += 1

# Sort seats by angle descending (pi to 0 = left to right)
seats_sorted = sorted(all_seats, key=lambda s: -s["angle"])

# Assign parties to seats in order
seat_data = []
current_idx = 0
for party_info in parties:
    party_name = party_info["party"]
    party_color = party_info["color"]
    n_seats = party_info["seats"]
    for _ in range(n_seats):
        if current_idx < len(seats_sorted):
            seat = seats_sorted[current_idx]
            seat_data.append(
                {"x": seat["x"], "y": seat["y"], "party": party_name, "color": party_color, "seats_count": n_seats}
            )
            current_idx += 1

df = pd.DataFrame(seat_data)

# Create color scale from party data
party_colors = {p["party"]: p["color"] for p in parties}
color_domain = list(party_colors.keys())
color_range = list(party_colors.values())

# Create legend labels with seat counts
legend_labels = {p["party"]: f"{p['party']} ({p['seats']})" for p in parties}
df["party_label"] = df["party"].map(legend_labels)

# Create the parliament chart
chart = (
    alt.Chart(df)
    .mark_circle(size=250, opacity=0.9)
    .encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-0.5, inner_radius + n_rows * row_spacing])),
        color=alt.Color(
            "party_label:N",
            scale=alt.Scale(domain=[legend_labels[p["party"]] for p in parties], range=color_range),
            legend=alt.Legend(
                title="Parties",
                titleFontSize=20,
                labelFontSize=16,
                labelLimit=200,
                symbolSize=300,
                orient="bottom",
                direction="horizontal",
                columns=3,
                titleOrient="top",
                titleAnchor="middle",
            ),
        ),
        tooltip=["party:N", "seats_count:Q"],
    )
    .properties(
        width=1500, height=800, title=alt.Title("parliament-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_view(strokeWidth=0)
    .configure_legend(padding=20, offset=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
