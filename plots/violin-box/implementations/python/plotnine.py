""" pyplots.ai
violin-box: Violin Plot with Embedded Box Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_boxplot, geom_violin, ggplot, labs, scale_fill_manual, theme, theme_minimal


# Data
np.random.seed(42)
n_per_group = 80

# Create groups with different distributions
data = pd.DataFrame(
    {
        "Value": np.concatenate(
            [
                np.random.normal(55, 10, n_per_group),  # Group A: normal
                np.random.exponential(8, n_per_group) + 35,  # Group B: right-skewed
                np.concatenate(
                    [  # Group C: bimodal
                        np.random.normal(40, 5, n_per_group // 2),
                        np.random.normal(65, 5, n_per_group // 2),
                    ]
                ),
                np.random.uniform(30, 70, n_per_group),  # Group D: uniform
            ]
        ),
        "Group": ["Product A"] * n_per_group
        + ["Product B"] * n_per_group
        + ["Product C"] * n_per_group
        + ["Product D"] * n_per_group,
    }
)

# Colors: Python Blue and Yellow plus complementary colors
colors = ["#306998", "#FFD43B", "#6A9BC9", "#D4A84B"]

# Plot
plot = (
    ggplot(data, aes(x="Group", y="Value", fill="Group"))
    + geom_violin(alpha=0.7, color="#333333", size=0.5, width=0.9)
    + geom_boxplot(width=0.15, alpha=0.9, color="#333333", fill="white", size=0.5, outlier_size=3)
    + scale_fill_manual(values=colors)
    + labs(title="violin-box · plotnine · pyplots.ai", x="Product Category", y="Customer Satisfaction Score")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
