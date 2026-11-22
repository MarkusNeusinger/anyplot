"""anyplot.ai
parliament-basic: Parliament Seat Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
N_ROWS = 5  # concentric arcs
INNER_RADIUS = 0.4
ROW_GAP = 0.15

# Columns
PARTY = "Party"  # role: party
SEATS = "Seats"  # role: seats
COLOR = "Color"  # role: color

# Data: a fictional chamber, party names and seat counts are made up
df = pd.DataFrame(
    {
        PARTY: ["Harbor Alliance", "Willow Bloc", "Granite Union", "Cedar League", "Marsh Circle"],
        SEATS: [90, 54, 32, 20, 12],
        COLOR: ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"],  # Imprint palette order
    }
)

# Plot: seat layout derived from df
total_seats = int(df[SEATS].sum())

# Seats per arc grow with the radius, the last arc absorbs rounding
row_weights = np.arange(1, N_ROWS + 1)
seats_per_row = (total_seats * row_weights / row_weights.sum()).astype(int)
seats_per_row[-1] += total_seats - seats_per_row.sum()

positions = []
for row_idx, n_row in enumerate(seats_per_row):
    radius = INNER_RADIUS + row_idx * ROW_GAP
    for angle in np.linspace(np.pi, 0, n_row):
        positions.append((radius * np.cos(angle), radius * np.sin(angle)))
positions.sort(key=lambda p: (p[0], -p[1]))  # left to right, so each party is one contiguous block

legend_labels = df[PARTY] + ": " + df[SEATS].astype(str)
seat_df = pd.DataFrame(positions, columns=["seat_x", "seat_y"])
seat_df["party"] = np.repeat(legend_labels.to_numpy(), df[SEATS].to_numpy())

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

sns.scatterplot(
    data=seat_df,
    x="seat_x",
    y="seat_y",
    hue="party",
    hue_order=list(legend_labels),
    palette=list(df[COLOR]),
    s=55,
    edgecolor=PAGE_BG,
    linewidth=0.6,
    ax=ax,
    zorder=2,
)

# Majority threshold: vertical line between the last seat of the majority and the next one
majority = total_seats // 2 + 1
sorted_x = seat_df["seat_x"].to_numpy()
majority_x = (sorted_x[majority - 1] + sorted_x[majority]) / 2
top = seat_df["seat_y"].max() + 0.1
ax.plot([majority_x, majority_x], [0, top], color=INK_SOFT, linestyle="--", linewidth=1.0, zorder=1)
ax.text(
    majority_x,
    top + 0.02,
    f"Majority: {majority} of {total_seats} seats",
    fontsize=8,
    color=INK_SOFT,
    ha="center",
    va="bottom",
)

legend = ax.legend(
    loc="lower center",
    ncol=3,
    fontsize=8,
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    labelcolor=INK,
    title="Party: seats",
    title_fontsize=9,
    markerscale=1.2,
)

ax.set_xlim(-1.08, 1.08)
ax.set_ylim(-0.38, 1.1)
ax.set_aspect("equal")
ax.axis("off")

ax.set_title("parliament-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="bold", color=INK, pad=22)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
