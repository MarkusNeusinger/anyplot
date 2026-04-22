""" pyplots.ai
line-styled: Styled Line Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    theme,
    theme_minimal,
)


# Data - quarterly product performance over 3 years
np.random.seed(42)
quarters = np.arange(1, 13)  # 12 quarters (3 years)
quarter_labels = [f"Q{(i - 1) % 4 + 1} {2022 + (i - 1) // 4}" for i in quarters]

# Generate realistic sales trends for different product lines
base = 100
product_a = base + np.cumsum(np.random.randn(12) * 5 + 3)  # Strong growth
product_b = base + np.cumsum(np.random.randn(12) * 4 + 1)  # Moderate growth
product_c = base + np.cumsum(np.random.randn(12) * 6 - 0.5)  # Volatile, slight decline
product_d = base + np.cumsum(np.random.randn(12) * 3 + 2)  # Steady growth

# Create long-format DataFrame for plotnine
df = pd.DataFrame(
    {
        "Quarter": np.tile(quarters, 4),
        "Quarter_Label": np.tile(quarter_labels, 4),
        "Sales": np.concatenate([product_a, product_b, product_c, product_d]),
        "Product": ["Product A"] * 12 + ["Product B"] * 12 + ["Product C"] * 12 + ["Product D"] * 12,
    }
)

# Define line styles and colors
linetype_values = {"Product A": "solid", "Product B": "dashed", "Product C": "dotted", "Product D": "dashdot"}
color_values = {
    "Product A": "#306998",  # Python Blue
    "Product B": "#FFD43B",  # Python Yellow
    "Product C": "#4CAF50",  # Green
    "Product D": "#E91E63",  # Pink
}

# Create plot
plot = (
    ggplot(df, aes(x="Quarter", y="Sales", color="Product", linetype="Product"))
    + geom_line(size=2)
    + scale_linetype_manual(values=linetype_values)
    + scale_color_manual(values=color_values)
    + labs(
        title="line-styled · plotnine · pyplots.ai",
        x="Quarter",
        y="Sales (thousands USD)",
        color="Product Line",
        linetype="Product Line",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#eeeeee", size=0.25, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300)
