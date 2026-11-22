""" anyplot.ai
parliament-basic: Parliament Seat Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_y_continuous,
    theme,
    theme_void,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per party in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_ROWS = 8  # concentric arcs of the chamber
INNER_RADIUS = 0.45
ROW_GAP = 0.075

# Columns: set these to your table's column names
PARTY = "Division"  # role: party
SEATS = "Seats"  # role: seats
COLOR = "Color"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("chamber.csv")
df = pd.DataFrame(
    {
        PARTY: [
            "Finance Committee",
            "Technology Board",
            "Operations Division",
            "Research Council",
            "Marketing Team",
            "Legal Advisory",
        ],
        SEATS: [85, 72, 58, 35, 95, 55],
        COLOR: ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"],
    }
)

# Plot
total = int(df[SEATS].astype(int).sum())
majority = total // 2 + 1

# Rows hold seats in proportion to their radius, so seat spacing is even
radii = INNER_RADIUS + ROW_GAP * np.arange(N_ROWS)
per_row = np.floor(radii / radii.sum() * total).astype(int)
per_row[-1] += total - per_row.sum()

angle = np.concatenate([np.linspace(np.pi, 0, n) for n in per_row])
radius = np.concatenate([np.full(n, r) for n, r in zip(per_row, radii, strict=True)])

# Sweep the seats from left to right and hand them out party by party
order = np.lexsort((radius, -angle))
angle, radius = angle[order], radius[order]
labels = [f"{p} ({int(s)})" for p, s in zip(df[PARTY], df[SEATS], strict=True)]
seat_party = np.repeat(labels, df[SEATS].astype(int))

seats = pd.DataFrame(
    {"x": radius * np.cos(angle), "y": radius * np.sin(angle), "label": pd.Categorical(seat_party, categories=labels)}
)

# Majority threshold: a radial line between the last seat of the majority and the next one,
# drawn in the gaps inside and outside the seat arcs so it never covers a seat
cut = (angle[majority - 1] + angle[majority]) / 2
r_in, r_out = radii[0] - 0.09, radii[-1] + 0.09
r_label = r_out + 0.17
threshold = pd.DataFrame(
    {
        "x": [r_in * np.cos(cut)],
        "y": [r_in * np.sin(cut)],
        "xend": [(r_in - 0.1) * np.cos(cut)],
        "yend": [(r_in - 0.1) * np.sin(cut)],
    }
)
threshold_out = pd.DataFrame(
    {
        "x": [r_out * np.cos(cut)],
        "y": [r_out * np.sin(cut)],
        "xend": [(r_out + 0.07) * np.cos(cut)],
        "yend": [(r_out + 0.07) * np.sin(cut)],
    }
)
threshold_label = pd.DataFrame(
    {"x": [r_label * np.cos(cut)], "y": [r_label * np.sin(cut)], "text": [f"Majority: {majority} of {total}"]}
)

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    plot_title=element_text(color=INK, size=16, hjust=0.5),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=11),
    legend_title=element_text(color=INK, size=12),
    plot_margin=[24, 0, 0, 0],
)

plot = (
    ggplot()
    + geom_point(aes(x="x", y="y", color="label"), data=seats, size=3.2)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=threshold, color=INK, size=0.8)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=threshold_out, color=INK, size=0.8)
    + geom_text(aes(x="x", y="y", label="text"), data=threshold_label, color=INK_SOFT, size=5)
    + scale_color_manual(values=IMPRINT_PALETTE, breaks=labels)
    + scale_y_continuous(expand=[0.105, 0])
    + coord_fixed()
    + theme_void()
    + anyplot_theme
    + labs(title="parliament-basic · python · letsplot · anyplot.ai", color="Division (seats)")
    + ggsize(800, 450)
)

# Save as PNG and HTML with theme suffix
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
