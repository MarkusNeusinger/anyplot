""" pyplots.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_gradient2,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Create realistic dataset with meaningful correlations
np.random.seed(42)
n = 200

# Generate correlated variables representing financial metrics
revenue = np.random.normal(100, 20, n)
marketing_spend = 0.3 * revenue + np.random.normal(10, 5, n)
employees = 0.5 * revenue + np.random.normal(20, 10, n)
customer_satisfaction = 0.4 * employees - 0.1 * marketing_spend + np.random.normal(50, 15, n)
profit = 0.7 * revenue - 0.5 * marketing_spend + np.random.normal(20, 10, n)
market_share = 0.3 * revenue + 0.2 * customer_satisfaction + np.random.normal(15, 5, n)
innovation_index = np.random.normal(60, 20, n)  # Independent variable
debt_ratio = -0.4 * profit + np.random.normal(30, 10, n)

# Create DataFrame
df = pd.DataFrame(
    {
        "Revenue": revenue,
        "Marketing": marketing_spend,
        "Employees": employees,
        "Satisfaction": customer_satisfaction,
        "Profit": profit,
        "Market Share": market_share,
        "Innovation": innovation_index,
        "Debt Ratio": debt_ratio,
    }
)

# Calculate correlation matrix
corr_matrix = df.corr()
variables = corr_matrix.columns.tolist()

# Prepare data for geom_tile (long format) with tooltips
corr_data = []
for var1 in variables:
    for var2 in variables:
        corr_val = corr_matrix.loc[var1, var2]
        corr_data.append(
            {"x": var1, "y": var2, "correlation": corr_val, "label": f"{corr_val:.2f}", "var_x": var1, "var_y": var2}
        )

corr_df = pd.DataFrame(corr_data)

# Set category order to maintain matrix layout
corr_df["x"] = pd.Categorical(corr_df["x"], categories=variables, ordered=True)
corr_df["y"] = pd.Categorical(corr_df["y"], categories=variables[::-1], ordered=True)

# Plot - Correlation heatmap with annotations and interactive tooltips
plot = (
    ggplot(corr_df, aes(x="x", y="y", fill="correlation"))
    + geom_tile(
        color="white",
        size=0.5,
        tooltips="none",  # Disable tile tooltips, use text tooltips instead
    )
    + geom_text(
        aes(label="label"),
        size=14,
        color="black",
        fontface="bold",
        tooltips={"lines": ["@var_x vs @var_y", "Correlation: @correlation"]},
    )
    + scale_fill_gradient2(
        low="#2166AC",  # Blue for negative
        mid="white",  # White for zero
        high="#B2182B",  # Red for positive
        midpoint=0,
        limits=[-1, 1],
        name="Correlation",
    )
    + labs(x="Financial Metric", y="Financial Metric", title="heatmap-correlation · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_text(size=22),
        axis_text_x=element_text(size=16, angle=45, hjust=1),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        panel_grid=element_blank(),
    )
    + ggsize(1200, 1200)  # Square format for correlation matrix
    + coord_fixed()
)

# Save as PNG (scale 3x for 3600x3600 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML with tooltips
ggsave(plot, "plot.html", path=".")
