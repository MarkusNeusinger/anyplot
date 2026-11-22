"""anyplot.ai
parliament-basic: Parliament Seat Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (canonical order, starting with brand green)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_ROWS = 8
INNER_RADIUS = 3.0
ROW_GAP = 0.8
ANGLE_MARGIN = 0.08

# Columns
PARTY = "party"  # role: party
SEATS = "seats"  # role: seats
COLOR = "color"  # role: color

# Data - fictional chamber with 6 made-up parties
df = pd.DataFrame(
    {
        PARTY: [
            "Harbor Union",
            "Willow Assembly",
            "Granite League",
            "Meadow Circle",
            "Lantern Alliance",
            "Copper Guild",
        ],
        SEATS: [98, 87, 76, 65, 48, 26],
    }
)
df[COLOR] = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(len(df))]

# Plot: reads only df and the constants above
# Layout: seats per arc grow with the arc radius
total_seats = int(df[SEATS].sum())
radii = INNER_RADIUS + np.arange(N_ROWS) * ROW_GAP
seats_per_row = np.round(radii / radii.sum() * total_seats).astype(int)
seats_per_row[-1] += total_seats - seats_per_row.sum()

seat_radius = np.concatenate([np.full(n, r) for r, n in zip(radii, seats_per_row, strict=True)])
seat_angle = np.concatenate([np.linspace(np.pi - ANGLE_MARGIN, ANGLE_MARGIN, n) for n in seats_per_row])

# Left to right = angle from pi to 0; blocks of seats follow the data order
order = np.argsort(-seat_angle, kind="stable")
seat_x = (seat_radius * np.cos(seat_angle))[order]
seat_y = (seat_radius * np.sin(seat_angle))[order]
seat_party = np.repeat(np.arange(len(df)), df[SEATS].fillna(0).to_numpy().astype(int))
majority = total_seats // 2 + 1

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, (party, seats, color) in enumerate(zip(df[PARTY], df[SEATS], df[COLOR], strict=True)):
    mask = seat_party == i
    ax.scatter(
        seat_x[mask], seat_y[mask], color=color, s=40, edgecolors=PAGE_BG, linewidth=0.3, label=f"{party} ({seats})"
    )

ax.set_xlim(seat_x.min() * 1.05, seat_x.max() * 1.05)
ax.set_ylim(-0.4, seat_radius.max() * 1.05)
ax.set_aspect("equal")
ax.axis("off")

leg = fig.legend(*ax.get_legend_handles_labels(), loc="lower center", ncol=3, fontsize=8, frameon=True, markerscale=1.2)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.6)
plt.setp(leg.get_texts(), color=INK_SOFT)

ax.text(0, 0.1, f"Majority threshold: {majority} seats", ha="center", fontsize=8, color=INK_SOFT, style="italic")

ax.set_title("parliament-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=6)
fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.15)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
