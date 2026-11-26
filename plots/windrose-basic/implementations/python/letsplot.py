"""anyplot.ai
windrose-basic: Wind Rose Chart
Library: letsplot 4.11.0 | Python 3.13.14
Quality: 84/100 | Updated: 2026-08-05
"""

import os
from itertools import pairwise

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_polar,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
# element_line has no alpha argument; lets-plot reads the alpha from an rgba() color
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette (canonical order); the ordered speed bins below use the Imprint marks ramp instead
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Constants
N_SECTORS = 16  # compass sectors of the rose
COMPASS_16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
SPEED_EDGES = [0, 3, 6, 9, 12, 15]  # lower edges of the speed bins in m/s; the last bin is open-ended

# Columns: set these to your table's column names
DIRECTION = "Wind direction (°)"  # role: direction
SPEED = "Wind speed (m/s)"  # role: speed

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
# Hourly wind measurements over one year with prevailing westerly winds
np.random.seed(42)
n_obs = 8760
direction_weights = np.array([0.05, 0.08, 0.06, 0.04, 0.08, 0.12, 0.25, 0.32])
direction_centers = np.array([0, 45, 90, 135, 180, 225, 270, 315])
chosen_sectors = np.random.choice(8, size=n_obs, p=direction_weights / direction_weights.sum())
directions = (direction_centers[chosen_sectors] + np.random.uniform(-22.5, 22.5, n_obs)) % 360
# Weibull-like speeds that vary with the direction
base_speed = np.random.weibull(2.2, n_obs) * 6
speeds = np.clip(base_speed * (1 + 0.3 * np.sin(np.radians(directions - 250))), 0, 25)
df = pd.DataFrame({DIRECTION: directions, SPEED: speeds})

# Plot: reads only df and the constants above
sector_size = 360 / N_SECTORS
df = df.dropna(subset=[DIRECTION, SPEED])  # an observation without direction or speed has no place on the rose
sector = (((df[DIRECTION] + sector_size / 2) % 360) // sector_size).astype(int)

speed_labels = [f"{lo}-{hi} m/s" for lo, hi in pairwise(SPEED_EDGES)] + [f"{SPEED_EDGES[-1]}+ m/s"]
speed_bin = pd.cut(df[SPEED], bins=[*SPEED_EDGES, max(df[SPEED].max(), SPEED_EDGES[-1]) + 1], labels=speed_labels)

counts = (
    pd.DataFrame({"direction": sector, "speed_bin": speed_bin})
    .groupby(["direction", "speed_bin"], observed=True)
    .size()
)
counts = counts.reset_index(name="count")
counts["frequency"] = counts["count"] / counts["count"].sum() * 100
counts["direction_label"] = counts["direction"].map(dict(enumerate(COMPASS_16)))
counts["speed_bin"] = pd.Categorical(counts["speed_bin"], categories=speed_labels, ordered=True)

# Ordered speed bins: steps of the Imprint marks ramp, calm to strong
n_bins = len(speed_labels)
speed_colors = [ramp_color(SEQ_MARKS, k / (n_bins - 1)) for k in range(n_bins)]

# Distinctive lets-plot feature: per-segment tooltips in the interactive HTML export
bar_tooltips = (
    layer_tooltips()
    .title("@direction_label")
    .line("@speed_bin: @{frequency}%")
    .format(field="@frequency", format=".1f")
)

# Style
plot = (
    ggplot(counts, aes(x="direction", y="frequency", fill="speed_bin"))
    + geom_bar(stat="identity", width=0.9, position="stack", tooltips=bar_tooltips, color=PAGE_BG, size=0.3)
    + coord_polar(start=0, direction=1)
    + scale_x_continuous(
        breaks=list(range(0, N_SECTORS, 2)), labels=COMPASS_16[::2], limits=[-0.5, N_SECTORS - 0.5], expand=[0, 0]
    )
    + scale_y_continuous(expand=[0, 0])
    + scale_fill_manual(values=speed_colors, name="Wind Speed")
    + labs(title="windrose-basic · python · letsplot · anyplot.ai", x="", y="Frequency (%)")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=GRID, size=0.4),
        panel_grid_minor=element_line(color=GRID, size=0.2),
        plot_title=element_text(size=16, color=INK, hjust=0.5),
        axis_text=element_text(size=12, color=INK_SOFT),
        axis_title_y=element_text(size=13, color=INK),
        legend_title=element_text(size=13, color=INK),
        legend_text=element_text(size=12, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
        legend_key_size=18,
        legend_key_spacing_y=6,
        legend_margin=10,
    )
)

# coord_polar keeps its aspect and leaves the rest of the canvas transparent;
# a one-panel grid carries the page color over the whole 2400 x 2400 canvas
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
