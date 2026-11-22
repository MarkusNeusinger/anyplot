"""anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_log10,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column names
CITY = "City"  # role: label
TEMPERATURE = "Mean annual temperature (°C)"  # role: x
PRECIPITATION = "Annual precipitation (mm)"  # role: y
CLIMATE = "Climate"  # grouping column that drives the text color

# Data: climate normals (approximate) for cities on five continents
rows = [
    ("Singapore", 27.0, 2340, "Tropical"),
    ("Jakarta", 27.5, 1800, "Tropical"),
    ("Mumbai", 27.2, 2400, "Tropical"),
    ("Bangkok", 28.6, 1500, "Tropical"),
    ("Lagos", 27.0, 1500, "Tropical"),
    ("Manaus", 27.4, 2300, "Tropical"),
    ("Cairo", 22.0, 25, "Arid"),
    ("Dubai", 27.0, 100, "Arid"),
    ("Riyadh", 26.0, 100, "Arid"),
    ("Phoenix", 24.0, 210, "Arid"),
    ("Lima", 19.0, 15, "Arid"),
    ("Alice Springs", 21.0, 280, "Arid"),
    ("Rome", 15.5, 800, "Mediterranean"),
    ("Athens", 18.5, 400, "Mediterranean"),
    ("Lisbon", 17.5, 750, "Mediterranean"),
    ("Los Angeles", 18.5, 380, "Mediterranean"),
    ("Cape Town", 17.0, 515, "Mediterranean"),
    ("Sydney", 18.0, 1200, "Mediterranean"),
    ("London", 11.0, 600, "Oceanic"),
    ("Paris", 12.0, 640, "Oceanic"),
    ("Seattle", 11.5, 950, "Oceanic"),
    ("Wellington", 12.5, 1250, "Oceanic"),
    ("Dublin", 10.0, 760, "Oceanic"),
    ("Vancouver", 10.5, 1150, "Oceanic"),
    ("Moscow", 5.8, 710, "Continental"),
    ("Oslo", 6.0, 760, "Continental"),
    ("Toronto", 9.5, 830, "Continental"),
    ("Chicago", 10.0, 970, "Continental"),
    ("Helsinki", 5.5, 650, "Continental"),
    ("Beijing", 12.9, 570, "Continental"),
    ("Reykjavik", 5.0, 800, "Subarctic"),
    ("Yakutsk", -8.8, 240, "Subarctic"),
    ("Anchorage", 2.8, 400, "Subarctic"),
    ("Ulaanbaatar", -0.4, 260, "Subarctic"),
    ("Fairbanks", -2.5, 280, "Subarctic"),
]
df = pd.DataFrame(rows, columns=[CITY, TEMPERATURE, PRECIPITATION, CLIMATE])

# Plot
climates = df[CLIMATE].unique().tolist()
t_min, t_max = df[TEMPERATURE].min(), df[TEMPERATURE].max()
t_pad = (t_max - t_min) * 0.08

plot = (
    ggplot(df, aes(x=TEMPERATURE, y=PRECIPITATION, label=CITY, color=CLIMATE))
    + geom_text(size=5, alpha=0.9, fontweight="bold")
    + scale_color_manual(values=IMPRINT_PALETTE, limits=climates)
    + scale_x_continuous(limits=(t_min - t_pad, t_max + t_pad))
    + scale_y_log10()
    + labs(title="City climates · scatter-text · python · plotnine · anyplot.ai")
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.06),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.4),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_title=element_text(size=12, color=INK, ha="left"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
