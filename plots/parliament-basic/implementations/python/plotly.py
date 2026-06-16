""" anyplot.ai
parliament-basic: Parliament Seat Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os
import site
import sys


# Remove current directory from sys.path to avoid shadowing installed packages
sys.path = [p for p in sys.path if p not in ("", ".") and not p.endswith("/python")]

# Ensure site-packages are at the front
for sp in reversed(site.getsitepackages()):
    sys.path.insert(0, sp)

import numpy as np  # noqa: E402
import plotly.graph_objects as go  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (positions 1→6, first is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data - Fictional parliament with neutral party names
parties = [
    {"name": "Progressive Alliance", "seats": 145},
    {"name": "Civic Union", "seats": 118},
    {"name": "Green Future", "seats": 52},
    {"name": "Liberty Party", "seats": 48},
    {"name": "Reform Coalition", "seats": 35},
    {"name": "Independent Group", "seats": 22},
]

# Assign Okabe-Ito colors to parties
for i, party in enumerate(parties):
    party["color"] = IMPRINT[i % len(IMPRINT)]

total_seats = sum(p["seats"] for p in parties)
majority_threshold = total_seats // 2 + 1

# Calculate seat positions in semicircular arrangement
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
            marker=dict(size=14, color=party["color"], line=dict(color=PAGE_BG, width=1)),
            name=f"{party['name']} ({party['seats']})",
            hovertemplate=f"{party['name']}<br>Seats: {party['seats']}<extra></extra>",
        )
    )

# Add majority threshold arc (more visible with increased alpha)
threshold_angle = np.linspace(0, np.pi, 100)
threshold_radius = 0.5 + 0.12 * (len(set(p["row"] for p in positions)) / 2)
fig.add_trace(
    go.Scatter(
        x=threshold_radius * np.cos(threshold_angle),
        y=threshold_radius * np.sin(threshold_angle),
        mode="lines",
        line=dict(color=INK_SOFT, width=3, dash="dash"),
        name=f"Majority ({majority_threshold})",
        hoverinfo="skip",
    )
)

# Layout
fig.update_layout(
    title=dict(text="parliament-basic · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.3, 1.3], scaleanchor="y", scaleratio=1),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.15, 1.2]),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.15,
        xanchor="center",
        x=0.5,
        font=dict(size=16, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        itemsizing="constant",
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=50, r=50, t=100, b=120),
)

# Add annotation for total seats
fig.add_annotation(
    x=0, y=0.05, text=f"<b>{total_seats}</b><br>seats", font=dict(size=24, color=INK), showarrow=False, align="center"
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
