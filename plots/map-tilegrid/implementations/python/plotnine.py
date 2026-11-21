"""anyplot.ai
map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-11-21
"""

import os

import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, to_rgb
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
    scale_fill_gradient,
    scale_y_reverse,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential ramp for unipolar data runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEQ_LOW, SEQ_HIGH = IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]

# Columns: set these to your table's column names
REGION = "State"  # role: region
VALUE = "Renewable energy (%)"  # role: value
ROW = "Grid row"  # role: row
COL = "Grid column"  # role: col

# Data: replace this block with your own table, for example df = pd.read_csv("tiles.csv")
# US state tile grid; the grid approximates geography, row 0 = north
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
df = pd.DataFrame(records, columns=[REGION, COL, ROW, VALUE])

# Plot: reads only df and the constants above
# Label color follows the tile's luminance: dark ink on light tiles, white on dark tiles
ramp = LinearSegmentedColormap.from_list("imprint_seq", [SEQ_LOW, SEQ_HIGH])
share = (df[VALUE] - df[VALUE].min()) / (df[VALUE].max() - df[VALUE].min())


def luminance(rgb):
    r, g, b = rgb[:3]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


df["label_color"] = [("#1A1A17" if luminance(to_rgb(ramp(s))) > 0.5 else "#FFFFFF") for s in share]

top, bottom = df.nlargest(2, VALUE), df.nsmallest(1, VALUE)
subtitle = (
    f"Highest: {top[REGION].iloc[0]} {top[VALUE].iloc[0]:.0f}%, {top[REGION].iloc[1]} {top[VALUE].iloc[1]:.0f}%"
    f"  ·  lowest: {bottom[REGION].iloc[0]} {bottom[VALUE].iloc[0]:.0f}%"
)

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=12),
    plot_subtitle=element_text(color=INK_SOFT, size=9),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
    legend_position="right",
)

plot = (
    ggplot(df, aes(x=COL, y=ROW, fill=VALUE))
    + geom_tile(color=PAGE_BG, size=1.0)
    + geom_text(aes(label=REGION, color="label_color"), size=6.5, fontweight="bold")
    + scale_fill_gradient(low=SEQ_LOW, high=SEQ_HIGH, name="Renewable\nenergy (%)")
    + scale_color_identity()
    + scale_y_reverse()
    + coord_fixed()
    + labs(title="US Renewable Energy Share · map-tilegrid · python · plotnine · anyplot.ai", subtitle=subtitle)
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
