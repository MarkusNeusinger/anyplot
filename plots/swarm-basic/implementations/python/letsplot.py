""" pyplots.ai
swarm-basic: Basic Swarm Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_text,
    geom_crossbar,
    geom_sina,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Performance scores across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Support"]
n_per_group = [45, 38, 52, 40]
colors = ["#306998", "#FFD43B", "#2E8B57", "#DC143C"]

data = []
for dept, n in zip(departments, n_per_group, strict=True):
    if dept == "Engineering":
        # Higher scores, moderate spread
        scores = np.random.normal(82, 8, n)
    elif dept == "Marketing":
        # Mid-range scores, wider spread
        scores = np.random.normal(75, 12, n)
    elif dept == "Sales":
        # Bimodal distribution (high and low performers)
        scores = np.concatenate([np.random.normal(65, 6, n // 2), np.random.normal(88, 5, n - n // 2)])
    else:  # Support
        # Lower average, tight distribution with some outliers
        scores = np.concatenate([np.random.normal(70, 6, n - 3), [45, 48, 95]])

    scores = np.clip(scores, 0, 100)
    for score in scores:
        data.append({"Department": dept, "Performance Score": score})

df = pd.DataFrame(data)

# Calculate means for each department
means = df.groupby("Department")["Performance Score"].mean().reset_index()
means.columns = ["Department", "mean"]

# Plot
plot = (
    ggplot(df, aes(x="Department", y="Performance Score"))
    + geom_sina(aes(color="Department", fill="Department"), size=4, alpha=0.7, seed=42, scale="width")
    + geom_crossbar(
        aes(x="Department", y="mean", ymin="mean", ymax="mean"), data=means, width=0.5, size=1.5, color="#333333"
    )
    + scale_color_manual(values=colors)
    + scale_fill_manual(values=colors)
    + labs(x="Department", y="Performance Score", title="swarm-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#cccccc", size=0.5),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
