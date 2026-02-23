""" pyplots.ai
density-basic: Basic Density Plot
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    after_stat,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_text,
    geom_area,
    geom_line,
    geom_rug,
    geom_vline,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - simulating test scores with bimodal distribution
np.random.seed(42)
test_scores = np.concatenate(
    [
        np.random.normal(72, 10, 150),  # Main distribution
        np.random.normal(88, 5, 50),  # High achievers
    ]
)
test_scores = np.clip(test_scores, 0, 100)

df = pd.DataFrame({"score": test_scores})

# Plot - layered density with bimodal emphasis
plot = (
    ggplot(df, aes(x="score"))
    + geom_area(aes(y=after_stat("density")), stat="density", fill="#306998", alpha=0.45, color="none")
    + geom_line(aes(y=after_stat("density")), stat="density", color="#1a3d5c", size=1.8)
    + geom_vline(xintercept=72, linetype="dashed", color="#5a6d7e", size=0.6, alpha=0.5)
    + geom_vline(xintercept=88, linetype="dashed", color="#5a6d7e", size=0.6, alpha=0.5)
    + geom_rug(color="#8B7355", alpha=0.4, size=0.7)
    + annotate("text", x=72, y=0.034, label="Main Group (μ ≈ 72)", size=11, color="#1a3d5c")
    + annotate("text", x=89, y=0.029, label="High Achievers (μ ≈ 88)", size=11, color="#6B4226")
    + labs(x="Test Score (points)", y="Probability Density", title="density-basic · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=range(45, 101, 10))
    + scale_y_continuous(expand=(0, 0, 0.2, 0))
    + coord_cartesian(xlim=(45, 102))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#cccccc", alpha=0.2, size=0.5),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
