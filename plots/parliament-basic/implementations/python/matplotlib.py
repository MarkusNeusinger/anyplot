""" anyplot.ai
parliament-basic: Parliament Seat Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (canonical order, starting with brand green)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - fictional parliament with 6 parties (400 total seats)
parties = [
    "Green Alliance",
    "Labor Coalition",
    "Conservative bloc",
    "Reform Party",
    "Centrist Union",
    "Progressive Front",
]
seats = [98, 87, 76, 65, 48, 26]
colors = IMPRINT[: len(parties)]
total_seats = sum(seats)

# Parliament layout parameters
n_rows = 8
inner_radius = 3.0
row_gap = 0.8
angle_margin = 0.08

# Calculate seats per row (more seats in outer rows)
row_weights = np.array([inner_radius + i * row_gap for i in range(n_rows)])
row_weights = row_weights / row_weights.sum()
seats_per_row = np.round(row_weights * total_seats).astype(int)

# Adjust to match total
diff = total_seats - seats_per_row.sum()
seats_per_row[-1] += diff

# Generate all seat positions with angles
seat_positions = []
for row_idx in range(n_rows):
    radius = inner_radius + row_idx * row_gap
    n_seats_in_row = seats_per_row[row_idx]
    angles = np.linspace(np.pi - angle_margin, angle_margin, n_seats_in_row)
    for angle in angles:
        seat_positions.append((radius, angle))

# Sort all seats by angle (left to right = pi to 0)
seat_positions.sort(key=lambda p: -p[1])

# Assign colors based on sorted position
all_x = []
all_y = []
all_colors = []

party_idx = 0
cumulative_seats = np.cumsum([0] + seats)

for i, (radius, angle) in enumerate(seat_positions):
    x = radius * np.cos(angle)
    y = radius * np.sin(angle)
    all_x.append(x)
    all_y.append(y)

    while party_idx < len(seats) - 1 and i >= cumulative_seats[party_idx + 1]:
        party_idx += 1
    all_colors.append(colors[party_idx])

all_x = np.array(all_x)
all_y = np.array(all_y)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot seats as circles
ax.scatter(all_x, all_y, c=all_colors, s=160, edgecolors=PAGE_BG, linewidth=0.5, zorder=2)

# Create legend entries with seat counts
legend_elements = []
for party, seat_count, color in zip(parties, seats, colors, strict=True):
    legend_elements.append(
        plt.scatter([], [], c=color, s=200, edgecolors=PAGE_BG, linewidth=0.5, label=f"{party} ({seat_count})")
    )

leg = ax.legend(
    handles=legend_elements, loc="lower center", ncol=3, fontsize=16, frameon=True, bbox_to_anchor=(0.5, -0.05)
)
leg.get_frame().set_facecolor(PAGE_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
for text in leg.get_texts():
    text.set_color(INK_SOFT)

# Add majority threshold annotation
majority = total_seats // 2 + 1
ax.text(0, -0.8, f"Majority threshold: {majority} seats", ha="center", fontsize=14, color=INK_SOFT, style="italic")

# Styling
ax.set_xlim(-8.5, 8.5)
ax.set_ylim(-2.5, 8)
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.set_title("parliament-basic · matplotlib · anyplot.ai", fontsize=24, pad=20, fontweight="medium", color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
