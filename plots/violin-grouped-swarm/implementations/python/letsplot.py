""" pyplots.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_point,
    geom_violin,
    ggplot,
    ggsize,
    labs,
    position_dodge,
    position_jitterdodge,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Response times across task types and expertise levels
np.random.seed(42)

categories = ["Simple", "Moderate", "Complex"]
groups = ["Novice", "Expert"]

data = []
for cat in categories:
    for grp in groups:
        # Create different distributions based on task and expertise
        if cat == "Simple":
            base = 200 if grp == "Novice" else 150
            spread = 40 if grp == "Novice" else 25
        elif cat == "Moderate":
            base = 400 if grp == "Novice" else 280
            spread = 80 if grp == "Novice" else 50
        else:  # Complex
            base = 700 if grp == "Novice" else 450
            spread = 120 if grp == "Novice" else 80

        n = 40
        values = np.random.normal(base, spread, n)
        # Add some outliers
        values = np.concatenate([values, np.random.normal(base + spread * 2, spread / 2, 3)])

        for v in values:
            data.append({"Task Type": cat, "Expertise": grp, "Response Time (ms)": max(50, v)})

df = pd.DataFrame(data)

# Create plot with grouped violins and jittered points overlay
plot = (
    ggplot(df, aes(x="Task Type", y="Response Time (ms)", fill="Expertise", color="Expertise"))
    + geom_violin(alpha=0.5, position=position_dodge(width=0.8), size=0.8, trim=False)
    + geom_point(alpha=0.6, size=2.5, position=position_jitterdodge(jitter_width=0.15, dodge_width=0.8))
    + scale_fill_manual(values=["#306998", "#FFD43B"])
    + scale_color_manual(values=["#1a3d5c", "#c9a82c"])
    + labs(x="Task Type", y="Response Time (ms)", title="violin-grouped-swarm · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major_x=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
