""" anyplot.ai
histogram-stepwise: Step Histogram
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BINS = 30  # shared bin count for every distribution

# Columns: set these to your table's column names
VALUES = ["Temperature (°C)"]  # role: values
PERIOD = "Time period"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("temperatures.csv")
np.random.seed(42)
morning_temps = np.random.normal(loc=18, scale=4, size=500)
afternoon_temps = np.random.normal(loc=26, scale=5, size=500)
df = pd.DataFrame(
    {
        VALUES[0]: np.concatenate([morning_temps, afternoon_temps]),
        PERIOD: ["Morning"] * len(morning_temps) + ["Afternoon"] * len(afternoon_temps),
    }
)

# Plot: reads only df and the constants above
bin_edges = np.linspace(df[VALUES[0]].min(), df[VALUES[0]].max(), BINS + 1)
groups = list(dict.fromkeys(df[PERIOD]))

# Step outline: each bin contributes a left and a right point at its count
steps = []
for group in groups:
    counts, _ = np.histogram(df.loc[df[PERIOD] == group, VALUES[0]].dropna(), bins=bin_edges)
    steps.append(
        pd.DataFrame(
            {
                VALUES[0]: np.column_stack([bin_edges[:-1], bin_edges[1:]]).ravel(),
                "Frequency": np.repeat(counts, 2),
                PERIOD: group,
            }
        )
    )
df_step = pd.concat(steps, ignore_index=True)

plot = (
    ggplot(df_step, aes(x=VALUES[0], y="Frequency", color=PERIOD))
    + geom_line(size=1.6)
    + scale_color_manual(values=[IMPRINT_PALETTE[i] for i in range(len(groups))], breaks=groups)
    + scale_y_continuous(limits=[0, df_step["Frequency"].max() * 1.08])
    + labs(title="histogram-stepwise · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=GRID, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save PNG (scale=4 gives 3200x1800) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
