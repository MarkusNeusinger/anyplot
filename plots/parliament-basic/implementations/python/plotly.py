"""anyplot.ai
parliament-basic: Parliament Seat Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order (first series is always #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_ROWS = 12  # concentric arcs
INNER_RADIUS = 0.35
ROW_SPACING = 0.055
MARKER_SIZE = 11

# Column constants
PARTY = "party"  # role: party
SEATS = "seats"  # role: seats

# Data - fictional chamber with made-up party names
df = pd.DataFrame(
    {
        PARTY: [
            "Progressive Alliance",
            "Civic Union",
            "Harbor Union",
            "Lantern Party",
            "Reform Coalition",
            "Independent Group",
        ],
        SEATS: [145, 118, 52, 48, 35, 22],
    }
)

# Plot
seats = df[SEATS].fillna(0).round().astype(int).to_numpy()
total_seats = int(seats.sum())
majority_threshold = total_seats // 2 + 1

# Seats per arc, proportional to the arc's radius, adjusted to the exact total
radii = INNER_RADIUS + ROW_SPACING * np.arange(N_ROWS)
row_seats = np.floor(total_seats * radii / radii.sum()).astype(int)
for i in range(total_seats - row_seats.sum()):
    row_seats[N_ROWS - 1 - i % N_ROWS] += 1

# Seat layout: angle runs from left (pi) to right (0) along each arc
seat_x, seat_y, seat_angle = [], [], []
for radius, n in zip(radii, row_seats, strict=True):
    angle = np.pi - (np.arange(n) + 0.5) * np.pi / n
    seat_x.extend(radius * np.cos(angle))
    seat_y.extend(radius * np.sin(angle))
    seat_angle.extend(angle)
order = np.argsort(-np.array(seat_angle), kind="stable")
seat_x = np.array(seat_x)[order]
seat_y = np.array(seat_y)[order]
seat_angle = np.array(seat_angle)[order]

# Parties take consecutive blocks of seats from left to right
ends = seats.cumsum()
starts = ends - seats

fig = go.Figure()
for i, (party, n) in enumerate(zip(df[PARTY], seats, strict=True)):
    sl = slice(starts[i], ends[i])
    fig.add_trace(
        go.Scatter(
            x=seat_x[sl],
            y=seat_y[sl],
            mode="markers",
            marker={"size": MARKER_SIZE, "color": IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]},
            name=f"{party} ({n})",
            hovertemplate=f"{party}<br>Seats: {n}<extra></extra>",
        )
    )

# Majority threshold: radial tick outside the arcs, clear of seats, between the last seat of the majority and the next one
cut = 0.5 * (seat_angle[majority_threshold - 1] + seat_angle[majority_threshold])
r_in, r_out = radii[-1] + 0.05, radii[-1] + 0.14
fig.add_trace(
    go.Scatter(
        x=[r_in * np.cos(cut), r_out * np.cos(cut)],
        y=[r_in * np.sin(cut), r_out * np.sin(cut)],
        mode="lines",
        line={"color": INK_SOFT, "width": 2, "dash": "dash"},
        name=f"Majority line ({majority_threshold})",
        hoverinfo="skip",
    )
)
fig.add_annotation(
    x=(r_out + 0.03) * np.cos(cut),
    y=(r_out + 0.03) * np.sin(cut),
    text=f"Majority: {majority_threshold}",
    showarrow=False,
    yanchor="bottom",
    font={"size": 12, "color": INK_SOFT},
)
fig.add_annotation(
    x=0, y=0.08, text=f"<b>{total_seats}</b><br>seats", font={"size": 18, "color": INK}, showarrow=False, align="center"
)

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={
        "text": "parliament-basic · python · plotly · anyplot.ai",
        "font": {"size": 20, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "range": [-1.2, 1.2],
        "scaleanchor": "y",
        "scaleratio": 1,
    },
    yaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-0.1, 1.2]},
    legend={
        "orientation": "h",
        "yanchor": "top",
        "y": -0.02,
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 11, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "itemsizing": "constant",
    },
    font={"color": INK},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 30, "r": 30, "t": 60, "b": 70},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
