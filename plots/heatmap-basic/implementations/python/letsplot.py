"""anyplot.ai
heatmap-basic: Basic Heatmap
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import math
import os
from itertools import pairwise

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    ggsize,
    guide_colorbar,
    labs,
    layer_tooltips,
    scale_color_identity,
    scale_fill_gradientn,
    scale_x_discrete,
    scale_y_discrete,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: continuous fields ramp (colored cells fill the plot), as (position, hex) stops
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    frac = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - frac) + int(c1[i : i + 2], 16) * frac):02X}" for i in (1, 3, 5)
    )


# Columns: set these to your table's column names
ZONE = "Building Zone"  # role: x
MONTH = "Month"  # role: y
KWH = "Energy (kWh)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("energy.csv")
# Monthly energy consumption (kWh) by building zone: seasonal variation + zone-specific baselines
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
zones = ["Lobby", "Offices", "Lab", "Server Room", "Cafeteria", "Warehouse"]
baselines = np.array([120, 280, 350, 520, 180, 90])
seasonal = np.array([1.3, 1.2, 1.0, 0.8, 0.7, 0.75, 0.85, 0.9, 0.8, 0.9, 1.1, 1.25])
noise = np.random.normal(0, 15, (len(months), len(zones)))
values = np.round(np.outer(seasonal, baselines) + noise, 0).astype(int)
df = pd.DataFrame({ZONE: np.tile(zones, len(months)), MONTH: np.repeat(months, len(zones)), KWH: values.flatten()})

# Plot: reads only df and the constants above
zone_order = list(dict.fromkeys(df[ZONE]))
month_order = list(dict.fromkeys(df[MONTH]))
median_val = int(df[KWH].median())


# In-cell text takes whichever ink contrasts more with the cell's fill (WCAG relative luminance)
def rel_lum(hex_color):
    lin = [
        (v / 255 / 12.92) if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4
        for v in (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    ]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


share = (df[KWH] - df[KWH].min()) / (df[KWH].max() - df[KWH].min())
fill_lum = [rel_lum(ramp_color(SEQ_FIELDS, t)) for t in share]
ink_dark, ink_light = "#1A1A17", "#FAF8F1"
dark_lum, light_lum = rel_lum(ink_dark), rel_lum(ink_light)
df["label_color"] = [
    ink_dark if (lum + 0.05) / (dark_lum + 0.05) >= (light_lum + 0.05) / (lum + 0.05) else ink_light for lum in fill_lum
]

plot = (
    ggplot(df, aes(x=ZONE, y=MONTH, fill=KWH))
    + geom_tile(
        width=0.92,
        height=0.92,
        tooltips=layer_tooltips()
        .line(f"@{{{ZONE}}} | @{{{MONTH}}}")
        .line(f"Energy: @{{{KWH}}} kWh")
        .line("Median: " + str(median_val) + " kWh"),
    )
    + geom_text(aes(label=KWH, color="label_color"), size=3.5, fontface="bold")
    + scale_color_identity()
    + scale_fill_gradientn(
        colors=[ramp_color(SEQ_FIELDS, k / 255) for k in range(256)],
        guide=guide_colorbar(barwidth=10, barheight=200, nbin=256),
    )
    + scale_x_discrete(limits=zone_order)
    + scale_y_discrete(limits=month_order[::-1])
    + labs(title="heatmap-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text_x=element_text(size=10, face="bold", color=INK_SOFT),
        axis_text_y=element_text(size=10, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, face="bold", color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_margin=[40, 20, 20, 20],
    )
    + ggsize(600, 600)
)

# Output: square canvas: ggsize(600, 600) × scale=4 → 2400×2400 px
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)

# HTML for interactive tooltips
ggsave(plot, f"plot-{THEME}.html", path=".")
