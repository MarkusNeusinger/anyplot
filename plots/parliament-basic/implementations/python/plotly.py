""" pyplots.ai
parliament-basic: Parliament Seat Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Fictional parliament with neutral party names (avoiding political references)
parties = [
    {"name": "Progressive Alliance", "seats": 145, "color": "#306998"},
    {"name": "Civic Union", "seats": 118, "color": "#FFD43B"},
    {"name": "Green Future", "seats": 52, "color": "#2CA02C"},
    {"name": "Liberty Party", "seats": 48, "color": "#9467BD"},
    {"name": "Reform Coalition", "seats": 35, "color": "#FF7F0E"},
    {"name": "Independent Group", "seats": 22, "color": "#E377C2"},
]

total_seats = sum(p["seats"] for p in parties)
majority_threshold = total_seats // 2 + 1

# Calculate seat positions in semicircular arrangement
# Seats are arranged by angle across all rows, with parties grouped from left to right
n_rows = 7 if total_seats <= 500 else 9
inner_radius = 0.4
row_spacing = 0.11

# Calculate seats per row (outer rows have more seats due to larger circumference)
row_seats = []
for row in range(n_rows):
    radius = inner_radius + row * row_spacing
    # Seats proportional to arc length (radius)
    seats_in_row = int(total_seats * radius / sum(inner_radius + i * row_spacing for i in range(n_rows)))
    row_seats.append(max(seats_in_row, 1))

# Adjust to match total seats exactly
diff = total_seats - sum(row_seats)
for i in range(abs(diff)):
    idx = (n_rows - 1 - i % n_rows) if diff > 0 else (i % n_rows)
    row_seats[idx] += 1 if diff > 0 else -1

# Generate all seat positions sorted by angle (left to right = pi to 0)
all_seats = []
for row, n_seats in enumerate(row_seats):
    radius = inner_radius + row * row_spacing
    for i in range(n_seats):
        # Angle from left (pi) to right (0) - seats go left to right
        angle = np.pi - (i + 0.5) * np.pi / n_seats
        all_seats.append({"x": radius * np.cos(angle), "y": radius * np.sin(angle), "angle": angle, "row": row})

# Sort all seats by angle (descending = left to right in parliament view)
all_seats.sort(key=lambda s: -s["angle"])

# Assign parties to seats (parties fill seats from left to right)
positions = []
seat_idx = 0
for party in parties:
    for _ in range(party["seats"]):
        if seat_idx < len(all_seats):
            seat = all_seats[seat_idx]
            positions.append(
                {"x": seat["x"], "y": seat["y"], "party": party["name"], "color": party["color"], "row": seat["row"]}
            )
            seat_idx += 1

# Create figure
fig = go.Figure()

# Add seats grouped by party for legend
for party in parties:
    party_positions = [p for p in positions if p["party"] == party["name"]]
    fig.add_trace(
        go.Scatter(
            x=[p["x"] for p in party_positions],
            y=[p["y"] for p in party_positions],
            mode="markers",
            marker=dict(size=14, color=party["color"], line=dict(color="white", width=1)),
            name=f"{party['name']} ({party['seats']})",
            hovertemplate=f"{party['name']}<br>Seats: {party['seats']}<extra></extra>",
        )
    )

# Add majority threshold arc (dashed line)
threshold_angle = np.linspace(0, np.pi, 100)
threshold_radius = 0.5 + 0.12 * (len(set(p["row"] for p in positions)) / 2)
fig.add_trace(
    go.Scatter(
        x=threshold_radius * np.cos(threshold_angle),
        y=threshold_radius * np.sin(threshold_angle),
        mode="lines",
        line=dict(color="rgba(0,0,0,0.3)", width=2, dash="dash"),
        name=f"Majority ({majority_threshold})",
        hoverinfo="skip",
    )
)

# Layout
fig.update_layout(
    title=dict(
        text="parliament-basic · plotly · pyplots.ai", font=dict(size=28, color="#333"), x=0.5, xanchor="center"
    ),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.3, 1.3], scaleanchor="y", scaleratio=1),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.15, 1.2]),
    legend=dict(
        orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=16), itemsizing="constant"
    ),
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=50, r=50, t=100, b=120),
)

# Add annotation for total seats
fig.add_annotation(
    x=0,
    y=0.05,
    text=f"<b>{total_seats}</b><br>seats",
    font=dict(size=24, color="#333"),
    showarrow=False,
    align="center",
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
