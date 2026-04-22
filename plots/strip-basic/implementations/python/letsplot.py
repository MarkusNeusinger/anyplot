""" pyplots.ai
strip-basic: Basic Strip Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 96/100 | Created: 2025-12-23
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
    ggplot,
    ggsave,
    ggsize,
    labs,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Survey response scores by department
np.random.seed(42)

departments = ["Marketing", "Engineering", "Sales", "Support"]
data = []

# Create different distributions for each department
distributions = {
    "Marketing": (72, 12),  # Mean 72, moderate spread
    "Engineering": (78, 8),  # Higher mean, tighter distribution
    "Sales": (68, 15),  # Lower mean, wide spread
    "Support": (75, 10),  # Medium-high mean, medium spread
}

for dept in departments:
    n_points = np.random.randint(25, 45)  # 25-44 observations per department
    mean, std = distributions[dept]
    scores = np.clip(np.random.normal(mean, std, n_points), 40, 100)
    for score in scores:
        data.append({"Department": dept, "Score": score})

df = pd.DataFrame(data)

# Plot
plot = (
    ggplot(df, aes(x="Department", y="Score"))
    + geom_jitter(color="#306998", size=4, alpha=0.6, width=0.25, height=0, seed=42)
    + labs(x="Department", y="Survey Score (points)", title="strip-basic · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#cccccc", size=0.5),
    )
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
