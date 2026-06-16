""" anyplot.ai
histogram-stepwise: Step Histogram
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Generate two distributions for comparison (temperature readings)
np.random.seed(42)
morning_temps = np.random.normal(loc=18, scale=4, size=500)
afternoon_temps = np.random.normal(loc=26, scale=5, size=500)

# Compute histogram bins manually for step representation
bins = 30
all_data = np.concatenate([morning_temps, afternoon_temps])
bin_edges = np.linspace(all_data.min(), all_data.max(), bins + 1)

# Calculate histogram counts for each distribution
morning_counts, _ = np.histogram(morning_temps, bins=bin_edges)
afternoon_counts, _ = np.histogram(afternoon_temps, bins=bin_edges)

# Create step data: duplicate each point for step appearance
step_data = []
for counts, label in [(morning_counts, "Morning"), (afternoon_counts, "Afternoon")]:
    for i in range(len(counts)):
        step_data.append({"x": bin_edges[i], "y": counts[i], "period": label})
        step_data.append({"x": bin_edges[i + 1], "y": counts[i], "period": label})

df_step = pd.DataFrame(step_data)

# Plot - Step histogram using geom_line
plot = (
    ggplot(df_step, aes(x="x", y="y", color="period"))
    + geom_line(size=2.5)
    + scale_color_manual(values=IMPRINT[:2])
    + labs(x="Temperature (°C)", y="Frequency", title="histogram-stepwise · letsplot · anyplot.ai", color="Time Period")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")

# Save HTML for interactivity
ggsave(plot, f"plot-{THEME}.html", path=".")
