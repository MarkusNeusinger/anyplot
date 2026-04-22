""" pyplots.ai
point-basic: Point Estimate Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_errorbarh,
    geom_point,
    geom_vline,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


# Data: Product satisfaction scores with 95% confidence intervals
np.random.seed(42)

categories = [
    "Customer Service",
    "Product Quality",
    "Delivery Speed",
    "Website Usability",
    "Price Value",
    "Return Process",
    "Product Variety",
    "Packaging",
]

# Generate realistic satisfaction scores (1-10 scale) with varying uncertainty
estimates = np.array([7.8, 8.2, 6.5, 7.1, 6.9, 7.4, 8.0, 7.6])
# Confidence intervals vary by sample size/variance
ci_widths = np.array([0.8, 0.5, 1.2, 0.9, 1.0, 0.7, 0.6, 0.4])

df = pd.DataFrame(
    {"category": categories, "estimate": estimates, "lower": estimates - ci_widths, "upper": estimates + ci_widths}
)

# Sort by estimate for better visualization
df = df.sort_values("estimate").reset_index(drop=True)
df["category"] = pd.Categorical(df["category"], categories=df["category"], ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="estimate", y="category"))
    + geom_vline(xintercept=7.0, linetype="dashed", color="#888888", size=1)
    + geom_errorbarh(aes(xmin="lower", xmax="upper"), height=0.3, size=1.5, color="#306998")
    + geom_point(size=5, color="#306998")
    + labs(x="Satisfaction Score (1-10)", y="Category", title="point-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(alpha=0),
    )
)

# Save
plot.save("plot.png", dpi=300)
