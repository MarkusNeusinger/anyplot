""" pyplots.ai
density-basic: Basic Density Plot
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 87/100 | Updated: 2026-02-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    after_stat,
    coord_cartesian,
    element_blank,
    element_line,
    element_text,
    geom_area,
    geom_line,
    geom_rug,
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

# Plot - layered density using stat_density for filled area + outline
plot = (
    ggplot(df, aes(x="score"))
    + geom_area(aes(y=after_stat("density")), stat="density", fill="#306998", alpha=0.5, color="none")
    + geom_line(aes(y=after_stat("density")), stat="density", color="#1a3d5c", size=1.8)
    + geom_rug(color="#306998", alpha=0.4, size=0.8)
    + labs(x="Test Score (points)", y="Probability Density", title="density-basic · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=range(40, 101, 10))
    + scale_y_continuous(expand=(0, 0, 0.05, 0))
    + coord_cartesian(xlim=(40, 102))
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
