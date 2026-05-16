""" anyplot.ai
map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Created: 2026-05-14
"""

import os

import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_cmap,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# US state tile grid: (state, col, row, renewable_energy_pct)
# Grid approximates geographic positions; row 0 = north, row 7 = south
records = [
    ("ME", 11, 0, 34),
    ("VT", 10, 1, 71),
    ("NH", 11, 1, 27),
    ("WA", 1, 2, 74),
    ("MT", 3, 2, 61),
    ("ND", 4, 2, 34),
    ("MN", 5, 2, 29),
    ("WI", 6, 2, 14),
    ("MI", 7, 2, 12),
    ("NY", 9, 2, 31),
    ("MA", 10, 2, 37),
    ("RI", 11, 2, 20),
    ("OR", 1, 3, 72),
    ("ID", 2, 3, 67),
    ("WY", 3, 3, 15),
    ("SD", 4, 3, 58),
    ("IA", 5, 3, 62),
    ("IL", 6, 3, 11),
    ("IN", 7, 3, 7),
    ("OH", 8, 3, 5),
    ("PA", 9, 3, 11),
    ("NJ", 10, 3, 7),
    ("CT", 11, 3, 10),
    ("CA", 1, 4, 49),
    ("NV", 2, 4, 22),
    ("UT", 3, 4, 22),
    ("CO", 4, 4, 32),
    ("NE", 5, 4, 24),
    ("MO", 6, 4, 8),
    ("KY", 7, 4, 6),
    ("WV", 8, 4, 4),
    ("VA", 9, 4, 14),
    ("MD", 10, 4, 12),
    ("DE", 11, 4, 8),
    ("AZ", 2, 5, 18),
    ("NM", 3, 5, 31),
    ("KS", 5, 5, 44),
    ("AR", 6, 5, 14),
    ("TN", 7, 5, 17),
    ("NC", 8, 5, 12),
    ("SC", 9, 5, 9),
    ("DC", 10, 5, 2),
    ("TX", 4, 6, 26),
    ("OK", 5, 6, 27),
    ("LA", 6, 6, 6),
    ("MS", 7, 6, 8),
    ("AL", 8, 6, 11),
    ("GA", 9, 6, 14),
    ("FL", 10, 6, 24),
    ("AK", 0, 7, 28),
    ("HI", 1, 7, 34),
]

df = pd.DataFrame(records, columns=["state", "col", "row", "renewable_pct"])
df["row_pos"] = -df["row"]  # Flip so row 0 is at top (geographic north)

# Text contrast: white on dark viridis tiles, dark on bright viridis tiles
mid = (df["renewable_pct"].min() + df["renewable_pct"].max()) / 2
df["label_color"] = df["renewable_pct"].apply(lambda v: "#FFFFFF" if v < mid else "#1A1A17")

# Theme
anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=22),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=14),
    legend_title=element_text(color=INK, size=16),
    legend_position="right",
)

# Plot
plot = (
    ggplot(df, aes(x="col", y="row_pos", fill="renewable_pct"))
    + geom_tile(color=PAGE_BG, size=1.5)
    + geom_text(aes(label="state", color="label_color"), size=11, fontweight="bold")
    + scale_fill_cmap(cmap_name="viridis", name="Renewable\nEnergy (%)")
    + scale_color_identity()
    + coord_fixed()
    + labs(title="US Renewable Energy Share · map-tilegrid · plotnine · anyplot.ai")
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, width=16, height=9)
