""" pyplots.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_jitter,
    geom_violin,
    ggplot,
    guide_legend,
    guides,
    labs,
    position_dodge,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Response times (ms) across task types and expertise levels
np.random.seed(42)

categories = ["Simple", "Moderate", "Complex"]
groups = ["Novice", "Expert"]
n_per_combination = 40

data = []
for category in categories:
    for group in groups:
        # Base response time varies by complexity
        base = {"Simple": 400, "Moderate": 700, "Complex": 1100}[category]
        # Experts are faster
        if group == "Expert":
            base -= 150
        # Generate data with varying spreads
        spread = {"Simple": 60, "Moderate": 100, "Complex": 150}[category]
        values = np.random.normal(base, spread, n_per_combination)
        # Add some variation for visual interest
        values = np.clip(values, base - 3 * spread, base + 3 * spread)
        for v in values:
            data.append({"task_type": category, "expertise": group, "response_time": v})

df = pd.DataFrame(data)
# Set category order
df["task_type"] = pd.Categorical(df["task_type"], categories=categories, ordered=True)
df["expertise"] = pd.Categorical(df["expertise"], categories=groups, ordered=True)

# Colors - Python Blue and Yellow
colors = {"Novice": "#306998", "Expert": "#FFD43B"}

# Create plot
plot = (
    ggplot(df, aes(x="task_type", y="response_time", fill="expertise", color="expertise"))
    + geom_violin(position=position_dodge(width=0.8), alpha=0.5, size=0.8)
    + geom_jitter(position=position_dodge(width=0.8), size=2.5, alpha=0.8)
    + scale_fill_manual(values=colors, name="Expertise")
    + scale_color_manual(values=colors, name="Expertise")
    + guides(fill=guide_legend(), color=guide_legend())
    + labs(title="violin-grouped-swarm · plotnine · pyplots.ai", x="Task Type", y="Response Time (ms)")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        panel_grid_major=element_line(alpha=0.3),
        panel_grid_minor=element_line(alpha=0.15),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
