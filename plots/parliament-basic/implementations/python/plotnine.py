""" anyplot.ai
parliament-basic: Parliament Seat Chart
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os

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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per party in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ROWS = 8  # concentric arcs of the hemicycle
INNER_RADIUS = 3.0  # radius of the innermost arc
ROW_SPACING = 1.0  # gap between neighbouring arcs

# Columns: set these to your table's column names
PARTY = "Party"  # role: party
SEATS = "Seats"  # role: seats
COLOR = "Color"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("seats.csv")
# A fictional river-basin authority council with invented groups
df = pd.DataFrame(
    {
        PARTY: [
            "Harbor Guild",
            "Lantern Bloc",
            "Willow Assembly",
            "Anvil Union",
            "Cedar Circle",
            "Tidewater League",
            "Quarry Collective",
        ],
        SEATS: [64, 52, 41, 33, 24, 15, 11],
        COLOR: ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"],
    }
)

# Plot: reads only df and the constants above
table = df.groupby(PARTY, sort=False)[SEATS].sum()
counts = table.round().astype(int).to_numpy()
total_seats = int(counts.sum())

# Seats per arc grow with the radius (largest-remainder rounding keeps the exact total)
radii = INNER_RADIUS + ROW_SPACING * np.arange(ROWS)
share = radii / radii.sum() * total_seats
per_row = np.floor(share).astype(int)
extra = total_seats - per_row.sum()
per_row[np.argsort(share - per_row)[::-1][:extra]] += 1

# Seat coordinates, spread over the full half circle on every arc
seats = pd.concat(
    [pd.DataFrame({"angle": np.linspace(np.pi, 0, n), "radius": r}) for r, n in zip(radii, per_row, strict=True)],
    ignore_index=True,
)
seats["x"] = seats["radius"] * np.cos(seats["angle"])
seats["y"] = seats["radius"] * np.sin(seats["angle"])

# Sweep from left to right and hand the seats to the parties in data order
seats = seats.sort_values(["angle", "radius"], ascending=[False, True], ignore_index=True)
parties = table.index.tolist()
seats[PARTY] = pd.Categorical(np.repeat(parties, counts), categories=parties, ordered=True)

legend_labels = [f"{p} ({n})" for p, n in zip(parties, counts, strict=True)]
colors = {p: IMPRINT_PALETTE[i] for i, p in enumerate(parties)}

plot = (
    ggplot(seats, aes(x="x", y="y", color=PARTY))
    + geom_point(size=3.2, alpha=0.95)
    + scale_color_manual(values=colors, limits=parties, labels=legend_labels)
    + labs(title="parliament-basic · python · plotnine · anyplot.ai", color="")
    + coord_fixed(ratio=1)
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=13, ha="center", weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="bottom",
        legend_direction="horizontal",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_margin=0.03,
    )
    + guides(color=guide_legend(nrow=2, override_aes={"size": 4}))
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
