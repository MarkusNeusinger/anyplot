""" pyplots.ai
parliament-basic: Parliament Seat Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - fictional parliament with 5 parties (400 total seats)
parties = ["Progressive Alliance", "Liberty Union", "Green Future", "Conservative Party", "Reform Movement"]
seats = [145, 110, 45, 80, 20]
colors = ["#E69F00", "#56B4E9", "#009E73", "#D55E00", "#CC79A7"]  # Colorblind-safe palette
total_seats = sum(seats)

# Parliament layout parameters
n_rows = 8  # Number of concentric rows
inner_radius = 3.0
row_gap = 0.8
angle_margin = 0.08  # Small margin at edges

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
    # Angles from pi (left) to 0 (right)
    angles = np.linspace(np.pi - angle_margin, angle_margin, n_seats_in_row)
    for angle in angles:
        seat_positions.append((radius, angle))

# Sort all seats by angle (left to right = pi to 0)
seat_positions.sort(key=lambda p: -p[1])

# Assign colors based on sorted position (parties arranged left to right)
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

    # Find which party this seat belongs to
    while party_idx < len(seats) - 1 and i >= cumulative_seats[party_idx + 1]:
        party_idx += 1
    all_colors.append(colors[party_idx])

all_x = np.array(all_x)
all_y = np.array(all_y)

# Create figure (16:9 aspect for 4800x2700)
fig, ax = plt.subplots(figsize=(16, 9))

# Plot seats as circles
ax.scatter(all_x, all_y, c=all_colors, s=160, edgecolors="white", linewidths=0.8, zorder=2)

# Create legend entries with seat counts
legend_elements = []
for party, seat_count, color in zip(parties, seats, colors, strict=True):
    legend_elements.append(
        plt.scatter([], [], c=color, s=200, edgecolors="white", linewidths=0.5, label=f"{party} ({seat_count})")
    )

ax.legend(handles=legend_elements, loc="lower center", ncol=3, fontsize=14, framealpha=0.9, bbox_to_anchor=(0.5, -0.02))

# Add majority threshold annotation (text only - clearer than misleading line)
majority = total_seats // 2 + 1
ax.text(0, -0.6, f"Majority threshold: {majority} seats", ha="center", fontsize=14, color="#555555", style="italic")

# Styling
ax.set_xlim(-8.5, 8.5)
ax.set_ylim(-2.5, 8)
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.set_title("parliament-basic · matplotlib · pyplots.ai", fontsize=24, pad=20, fontweight="bold")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
