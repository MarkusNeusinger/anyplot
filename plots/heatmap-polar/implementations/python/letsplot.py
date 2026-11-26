"""anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: letsplot 4.11.0 | Python 3.14.10
Quality: pending | Updated: 2026-11-22
"""

import os
from itertools import pairwise

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_polar,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    gggrid,
    ggplot,
    ggsize,
    labs,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single-polarity sequential ramp (fields stops, as colored cells fill the plot)
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Constants
LABEL_EVERY = 6  # hours between angular labels

# Columns: set these to your table's column names
DAY = "Day of week"  # role: radial
HOUR = "Hour of day"  # role: angular
VISITS = "Hourly visits"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
np.random.seed(42)
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
records = []
for d_idx, day in enumerate(days):
    for h in range(24):
        if d_idx < 5:
            if 9 <= h <= 17:
                base = 750
            elif (6 <= h <= 8) or (18 <= h <= 21):
                base = 380
            else:
                base = 80
        else:
            if 11 <= h <= 20:
                base = 550
            elif (21 <= h <= 23) or h == 0:
                base = 260
            else:
                base = 60
        visits = max(10, int(base + np.random.normal(0, base * 0.10)))
        records.append({DAY: day, HOUR: h, VISITS: visits})
df = pd.DataFrame(records)

# Plot
n_hours = int(df[HOUR].max()) + 1
day_order = list(dict.fromkeys(df[DAY]))
plot_df = df.assign(
    hour_mid=df[HOUR] + 0.5,  # tile centre
    ring=df[DAY].map({d: i + 1 for i, d in enumerate(day_order)}),  # first day innermost
)
label_hours = list(range(0, n_hours, LABEL_EVERY))
hour_labels = [f"{h % 12 or 12}{'am' if h < 12 else 'pm'}" for h in label_hours]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=14, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=12),
)

plot = (
    ggplot(plot_df, aes(x="hour_mid", y="ring", fill=VISITS))
    + geom_tile(color=PAGE_BG, size=0.4)
    + coord_polar(theta="x")
    + scale_fill_gradientn(
        colors=[ramp_color(SEQ_FIELDS, k / 255) for k in range(256)], name=VISITS.replace(" ", "\n", 1)
    )
    + scale_x_continuous(breaks=[h + 0.5 for h in label_hours], labels=hour_labels, limits=[0, n_hours], expand=[0, 0])
    + scale_y_continuous(
        breaks=list(range(1, len(day_order) + 1)), labels=day_order, limits=[0, len(day_order) + 0.5], expand=[0, 0]
    )
    + labs(title="Website Traffic · heatmap-polar · python · letsplot · anyplot.ai", x=HOUR, y=DAY)
    + anyplot_theme
    + ggsize(600, 600)
)

# The polar aspect leaves the canvas edges transparent: a one-panel grid paints the page color
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
