"""anyplot.ai
band-basic: Basic Band Plot
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BAND_FILL = IMPRINT_PALETTE[0]  # brand green — Imprint position 1
LINE_COLOR = IMPRINT_PALETTE[2]  # blue — Imprint position 3
# A translucent green sinks into the dark page, so the dark theme takes a stronger fill (spec: alpha 0.2-0.4)
BAND_ALPHA = 0.25 if THEME == "light" else 0.4

# Columns: set these to your table's column names
CYCLES = "Charge cycles"  # role: x
LOWER = "Lower bound (%)"  # role: y_lower
UPPER = "Upper bound (%)"  # role: y_upper
CENTER = "Capacity (%)"  # role: y_center

# Data: replace this block with your own table, for example df = pd.read_csv("capacity.csv")
# Battery capacity, exponential decay over charge cycles, with a widening 95% tolerance band
cycles = np.linspace(0, 500, 100)
capacity_mean = 100 * np.exp(-0.002 * cycles)
tolerance = 2.5 + 0.008 * cycles
df = pd.DataFrame(
    {
        CYCLES: cycles,
        LOWER: capacity_mean - 1.96 * tolerance,
        UPPER: capacity_mean + 1.96 * tolerance,
        CENTER: capacity_mean,
    }
)

# Plot
x_pad = (df[CYCLES].max() - df[CYCLES].min()) * 0.02
y_pad = (df[UPPER].max() - df[LOWER].min()) * 0.05

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_blank(),
    panel_grid_major_y=element_line(color=INK_MUTED, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    axis_line_x=element_line(color=INK_SOFT),
    axis_line_y=element_blank(),
    plot_title=element_text(size=16, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG),
    legend_text=element_text(size=10, color=INK_SOFT),
)

plot = (
    ggplot(df, aes(x=CYCLES))
    + geom_ribbon(aes(ymin=LOWER, ymax=UPPER), fill=BAND_FILL, alpha=BAND_ALPHA, size=0)
    + geom_line(aes(y=CENTER), color=LINE_COLOR, size=1.5)
    + labs(x=CYCLES, y=CENTER, title="band-basic · python · letsplot · anyplot.ai")
    + scale_x_continuous(limits=[df[CYCLES].min() - x_pad, df[CYCLES].max() + x_pad])
    + scale_y_continuous(limits=[df[LOWER].min() - y_pad, df[UPPER].max() + y_pad])
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
