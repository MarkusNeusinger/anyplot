"""anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
"""

import os
import sys


# Prevent current directory from shadowing the plotnine package
sys.path = [p for p in sys.path if not p.endswith("implementations") and not p.endswith("python")]

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_equal,
    element_blank,
    element_rect,
    element_text,
    geom_label,
    geom_polygon,
    ggplot,
    labs,
    lims,
    scale_fill_gradient,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential ramp runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEQ_LOW, SEQ_HIGH = IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]

# Constants
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]  # ordered scale, first = innermost ring
ARC_POINTS = 10  # vertices per cell arc

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: angular
DAY = "Day of week"  # role: radial
VISITS = "Visits/hr"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
rng = np.random.default_rng(42)
rows = []
for d_idx, day in enumerate(WEEKDAYS):
    for h in range(24):
        if d_idx >= 5:
            base = 140 + np.exp(-0.5 * ((h - 12) / 3.5) ** 2) * 320
        else:
            base = (
                180
                + np.exp(-0.5 * ((h - 9) / 1.5) ** 2) * 520
                + np.exp(-0.5 * ((h - 13) / 1.8) ** 2) * 360
                + np.exp(-0.5 * ((h - 20) / 2.0) ** 2) * 290
            )
        rows.append({HOUR: h, DAY: day, VISITS: max(0.0, base + rng.normal(0, 20))})
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
days = df[DAY].unique().tolist()
n_hours = df[HOUR].max() + 1
step = 2 * np.pi / n_hours


def hour_label(h):
    h = int(h) % 24
    return f"{h % 12 or 12}{'am' if h < 12 else 'pm'}"


# Wedge polygons: 12am at the top, hours run clockwise, first day is the innermost ring
poly = []
for cell_id, rec in enumerate(df.itertuples(index=False)):
    h, day, val = rec
    ring = days.index(day)
    r_in, r_out = ring + 1.0, ring + 2.0
    t0 = np.pi / 2 - h * step
    t1 = np.pi / 2 - (h + 1) * step
    for t in np.linspace(t0, t1, ARC_POINTS):
        poly.append((r_in * np.cos(t), r_in * np.sin(t), cell_id, val))
    for t in np.linspace(t1, t0, ARC_POINTS):
        poly.append((r_out * np.cos(t), r_out * np.sin(t), cell_id, val))
df_poly = pd.DataFrame(poly, columns=["px", "py", "g", "v"])

# Ring labels at 12am, on a page-colored plate so they read over any cell color
df_day = pd.DataFrame({"px": 0.0, "py": np.arange(len(days)) + 1.5, "label": days})

r_out_max = len(days) + 1.0
r_text = r_out_max + 0.7
quarter = n_hours // 4

# Busiest hour of the week, found from the data
peak_hour = int(df.groupby(HOUR)[VISITS].mean().idxmax())
t_peak = np.pi / 2 - (peak_hour + 0.5) * step
r_peak = r_out_max + 0.5

plot = (
    ggplot(df_poly, aes(x="px", y="py", group="g", fill="v"))
    + geom_polygon(color=ELEVATED_BG, size=0.1)
    + geom_label(
        data=df_day,
        mapping=aes(x="px", y="py", label="label"),
        inherit_aes=False,
        color=INK,
        fill=ELEVATED_BG,
        size=7,
        label_size=0,
        ha="center",
        va="center",
    )
    + annotate("text", x=0, y=r_text, label=hour_label(0), color=INK_SOFT, size=8, ha="center", va="bottom")
    + annotate("text", x=r_text, y=0, label=hour_label(quarter), color=INK_SOFT, size=8, ha="left", va="center")
    + annotate("text", x=0, y=-r_text, label=hour_label(2 * quarter), color=INK_SOFT, size=8, ha="center", va="top")
    + annotate("text", x=-r_text, y=0, label=hour_label(3 * quarter), color=INK_SOFT, size=8, ha="right", va="center")
    + annotate(
        "text",
        x=r_peak * np.cos(t_peak),
        y=r_peak * np.sin(t_peak),
        label=f"Busiest hour:\n{hour_label(peak_hour)}",
        color=INK_SOFT,
        size=6,
        ha="left",
        va="bottom",
    )
    + coord_equal()
    + lims(x=(-(r_text + 1.0), r_text + 1.0), y=(-(r_text + 0.3), r_text + 0.3))
    + scale_fill_gradient(low=SEQ_LOW, high=SEQ_HIGH, name=VISITS)
    + labs(title="Website Traffic · heatmap-polar · python · plotnine · anyplot.ai", x="", y="")
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_line=element_blank(),
        axis_ticks=element_blank(),
        plot_title=element_text(color=INK, size=10, ha="center"),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_text(color=INK, size=8),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
