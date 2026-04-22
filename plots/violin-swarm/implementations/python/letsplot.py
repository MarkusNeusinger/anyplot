""" pyplots.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_text,
    geom_jitter,
    geom_violin,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data: Reaction times (ms) across 4 experimental conditions
np.random.seed(42)

conditions = ["Control", "Low Dose", "Medium Dose", "High Dose"]
n_per_group = 50

data = []
for condition in conditions:
    if condition == "Control":
        # Normal distribution centered at 450ms
        values = np.random.normal(450, 60, n_per_group)
    elif condition == "Low Dose":
        # Slightly faster, narrower distribution
        values = np.random.normal(420, 50, n_per_group)
    elif condition == "Medium Dose":
        # Faster with some variability
        values = np.random.normal(380, 70, n_per_group)
    else:  # High Dose
        # Fastest but bimodal (some responders, some non-responders)
        responders = np.random.normal(320, 40, n_per_group // 2)
        non_responders = np.random.normal(400, 35, n_per_group - n_per_group // 2)
        values = np.concatenate([responders, non_responders])

    for v in values:
        data.append({"Condition": condition, "Reaction Time": v})

df = pd.DataFrame(data)

# Ensure categorical order
df["Condition"] = pd.Categorical(df["Condition"], categories=conditions, ordered=True)

# Create plot with violin and overlaid swarm points
plot = (
    ggplot(df, aes(x="Condition", y="Reaction Time"))
    + geom_violin(aes(fill="Condition"), alpha=0.4, size=1.2)
    + geom_jitter(aes(color="Condition"), width=0.12, height=0, size=3.5, alpha=0.85)
    + scale_fill_manual(values=["#306998", "#FFD43B", "#4A90D9", "#E57373"])
    + scale_color_manual(values=["#1A3A52", "#8B6914", "#1E3A5F", "#B71C1C"])
    + labs(x="Experimental Condition", y="Reaction Time (ms)", title="violin-swarm · lets-plot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_position="none",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
