""" pyplots.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 94/100 | Created: 2026-02-17
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data
p = np.linspace(0, 1, 200)

gini = 2 * p * (1 - p)

entropy_raw = np.where((p > 0) & (p < 1), -p * np.log2(p) - (1 - p) * np.log2(1 - p), 0.0)
entropy_normalized = entropy_raw  # max of entropy is 1.0 at p=0.5, already in [0,1]

df = pd.DataFrame(
    {
        "p": np.tile(p, 2),
        "impurity": np.concatenate([gini, entropy_normalized]),
        "measure": ["Gini: 2p(1−p)"] * len(p) + ["Entropy: −p log₂p − (1−p) log₂(1−p)"] * len(p),
    }
)

# Plot
plot = (
    ggplot(df, aes(x="p", y="impurity", color="measure"))
    + geom_line(size=2.5)
    + geom_point(
        data=pd.DataFrame(
            {
                "p": [0.5, 0.5],
                "impurity": [0.5, 1.0],
                "measure": ["Gini: 2p(1−p)", "Entropy: −p log₂p − (1−p) log₂(1−p)"],
            }
        ),
        size=5,
        show_legend=False,
    )
    + annotate(
        "text", x=0.5, y=1.06, label="Both maxima at p = 0.5", size=14, ha="center", color="#444444", fontstyle="italic"
    )
    + scale_color_manual(values=["#306998", "#C75B2A"])
    + scale_x_continuous(breaks=np.arange(0, 1.1, 0.1))
    + scale_y_continuous(breaks=np.arange(0, 1.1, 0.2), limits=(0, 1.15))
    + labs(
        x="Probability (p)",
        y="Impurity Measure (normalized)",
        title="line-impurity-comparison · plotnine · pyplots.ai",
        color="Splitting Criterion",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, weight="bold"),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16, weight="bold"),
        legend_position=(0.72, 0.25),
        legend_background=element_blank(),
        legend_key=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.5, alpha=0.2),
        axis_line=element_line(color="#333333", size=0.8),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
