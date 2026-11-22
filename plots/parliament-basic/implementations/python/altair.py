"""anyplot.ai
parliament-basic: Parliament Seat Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-17
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per party in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_ROWS = 9  # concentric arcs of the chamber
INNER_RADIUS = 2.5  # radius of the innermost arc
ROW_SPACING = 0.45  # radial distance between arcs

# Columns: set these to your table's column names
PARTY = "Party"  # role: party
SEATS = "Seats"  # role: seats
COLOR = "Color"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("chamber.csv")
df = pd.DataFrame(
    {
        PARTY: ["Harbor Union", "Meadow Alliance", "Lantern Guild", "Cedar Forum", "Quarry Circle", "Willow Front"],
        SEATS: [95, 82, 45, 38, 28, 12],
        COLOR: ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"],  # Imprint palette order
    }
)

# Plot: reads only df and the constants above
seats = df[SEATS].round().astype(int).to_numpy()
total_seats = int(seats.sum())

# Seats per arc, proportional to the arc's radius; the remainder goes to the outer arcs
radii = INNER_RADIUS + ROW_SPACING * np.arange(N_ROWS)
seats_per_row = np.floor(total_seats * radii / radii.sum()).astype(int)
seats_per_row[N_ROWS - (total_seats - seats_per_row.sum()) :] += 1

# Seat positions, then ordered by angle from the left end of the chamber to the right
angles = np.concatenate([np.linspace(np.pi, 0, n) for n in seats_per_row])
seat_radii = np.repeat(radii, seats_per_row)
order = np.argsort(-angles, kind="stable")
layout = pd.DataFrame({"x": (seat_radii * np.cos(angles))[order], "y": (seat_radii * np.sin(angles))[order]})

# Each party takes one contiguous block of seats, in data order
legend_labels = [f"{party} ({n})" for party, n in zip(df[PARTY], seats, strict=True)]
layout["label"] = np.repeat(legend_labels, seats)

# Equal scaling on both axes: the view's aspect follows the data extent
pad = 0.35
x_limit = radii.max() + pad
y_limit = radii.max() + pad
VIEW_WIDTH = 600
view_height = round(VIEW_WIDTH * (y_limit + pad) / (2 * x_limit))

chart = (
    alt.Chart(layout)
    .mark_circle(size=135, opacity=1)
    .encode(
        x=alt.X("x", type="quantitative", axis=None, scale=alt.Scale(domain=[-x_limit, x_limit])),
        y=alt.Y("y", type="quantitative", axis=None, scale=alt.Scale(domain=[-pad, y_limit])),
        color=alt.Color(
            "label",
            type="nominal",
            sort=None,
            scale=alt.Scale(domain=legend_labels, range=df[COLOR].tolist()),
            legend=alt.Legend(
                title=None,
                labelFontSize=14,
                symbolSize=260,
                orient="bottom",
                direction="horizontal",
                columns=3,
                labelLimit=260,
                columnPadding=24,
                rowPadding=6,
                padding=10,
                cornerRadius=4,
            ),
        ),
        tooltip=[alt.Tooltip("label", title=PARTY)],
    )
    .properties(
        width=VIEW_WIDTH,
        height=view_height,
        title=alt.Title("parliament-basic · python · altair · anyplot.ai", fontSize=20, anchor="middle"),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad (never crop) the PNG to the exact landscape target
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    # a taller legend (more parties) shrinks the picture, never crops it
    fit = min(TARGET_W / img.width, TARGET_H / img.height)
    img = img.resize((int(img.width * fit), int(img.height * fit)))
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
