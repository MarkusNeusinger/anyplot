""" anyplot.ai
polar-line: Polar Line Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 88/100 | Updated: 2026-11-09
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_polar,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.22)" if THEME == "light" else "rgba(240,239,232,0.22)"

# Imprint palette: one hue per series, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
THETA = "Angle (°)"  # role: theta
RADII = ["Lisbon", "Madrid"]  # role: radius
MONTH = "Month"  # role: extra
RADIUS_TITLE = "Mean temperature (°C)"  # what the radius columns measure: the radial axis title

# Data: replace this block with your own table, for example df = pd.read_csv("monthly_temperatures.csv")
# Monthly mean temperatures (1981–2010 normals), one month every 30 degrees around the circle:
# maritime Lisbon swings little over the year, continental Madrid is colder in winter and hotter in summer
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        THETA: range(0, 360, 30),
        RADII[0]: [11.6, 12.6, 14.9, 16.0, 18.2, 21.3, 23.1, 23.6, 22.2, 19.0, 15.0, 12.6],
        RADII[1]: [6.3, 7.9, 11.2, 12.9, 16.9, 22.6, 25.6, 25.2, 20.8, 15.1, 9.9, 6.9],
    }
)

# Plot: reads only df and the constants above
points = df.melt(id_vars=[THETA, MONTH], value_vars=RADII, var_name="Series", value_name="Radius")
# Close each loop: the cycle wraps from its last angle back to its first one, a full turn later
wrap = points.sort_values(THETA, kind="stable").groupby("Series", sort=False).head(1).copy()
wrap[THETA] = wrap[THETA] + 360
loops = pd.concat([points, wrap], ignore_index=True)
ticks = df.dropna(subset=[THETA, MONTH]).drop_duplicates(THETA).sort_values(THETA)

plot = (
    ggplot(loops, aes(x=THETA, y="Radius", color="Series"))
    + geom_line(size=1.4)
    + geom_point(data=points, size=3.2)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + scale_x_continuous(limits=[0, 360], breaks=ticks[THETA].tolist(), labels=ticks[MONTH].tolist())
    + scale_y_continuous(limits=[min(0, points["Radius"].min()), points["Radius"].max() * 1.08])
    # Months run clockwise from January at 12 o'clock
    + coord_polar(start=0, direction=1)
    + labs(title="polar-line · python · letsplot · anyplot.ai", y=RADIUS_TITLE)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        # The round panel's outline runs through the month labels' descenders: no stroke, so none is painted over
        panel_background=element_rect(fill=PAGE_BG, size=0),
        panel_grid_major=element_line(color=GRID, size=0.5),
        panel_grid_minor=element_blank(),
        axis_title_x=element_blank(),
        # The radial scale runs from the center to the top of the panel: center its title on that half
        axis_title_y=element_text(size=12, color=INK, hjust=0.75),
        axis_ticks=element_blank(),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_text_x=element_text(size=12, color=INK),
        axis_text_y=element_text(size=10, color=INK_SOFT),
        legend_position="bottom",
        legend_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_title=element_blank(),
        legend_text=element_text(size=11, color=INK_SOFT),
    )
)
# coord_polar keeps the panel round and narrows the plot box to fit; a one-cell grid paints the whole canvas
figure = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(figure, f"plot-{THEME}.png", path=".", scale=4)
ggsave(figure, f"plot-{THEME}.html", path=".")
