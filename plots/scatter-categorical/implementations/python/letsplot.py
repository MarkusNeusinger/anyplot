""" anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SHAPES = [21, 22, 23, 24, 25, 21, 22, 23]  # circle, square, diamond, triangle, then repeats

# Columns
TEMPERATURE = "Temperature (°C)"  # role: x
GROWTH = "Growth Rate (%)"  # role: y
TREATMENT = "Treatment"  # role: category

# Data: plant growth by treatment type
rng = np.random.default_rng(42)
groups = [  # (name, size, temp mean, temp sd, slope, offset, noise sd)
    ("Treatment A", 40, 45, 8, 1.10, 5, 6),
    ("Treatment B", 35, 52, 9, 0.95, 3, 7),
    ("Treatment C", 38, 38, 7, 1.25, 8, 5),
    ("Treatment D", 37, 55, 10, 0.85, 2, 8),
]
frames = []
for name, size, mean, sd, slope, offset, noise in groups:
    temp = rng.normal(mean, sd, size)
    frames.append(
        pd.DataFrame({TEMPERATURE: temp, GROWTH: temp * slope + rng.normal(offset, noise, size), TREATMENT: name})
    )
df = pd.concat(frames, ignore_index=True)

# Plot
plot = (
    ggplot(df, aes(x=TEMPERATURE, y=GROWTH, color=TREATMENT, fill=TREATMENT, shape=TREATMENT))
    + geom_point(size=3, alpha=0.75, stroke=0.8)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + scale_shape_manual(values=SHAPES)
    + labs(title="scatter-categorical · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=None),
        panel_grid_major=element_line(color=INK_SOFT, size=0.15),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=16, color=INK, face="bold"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK),
    )
)

# Save
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
