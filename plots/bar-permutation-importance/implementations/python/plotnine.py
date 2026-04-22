""" pyplots.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_line,
    element_text,
    geom_col,
    geom_errorbar,
    geom_hline,
    ggplot,
    labs,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


# Data - Simulating permutation importance results from a random forest model
np.random.seed(42)

# Feature names representing a customer churn prediction model
features = [
    "Contract Length",
    "Monthly Charges",
    "Total Charges",
    "Tenure (months)",
    "Tech Support Calls",
    "Payment Method",
    "Internet Service Type",
    "Online Security",
    "Streaming Services",
    "Paperless Billing",
    "Number of Dependents",
    "Senior Citizen Status",
    "Partner Status",
    "Phone Service",
    "Multiple Lines",
]

# Generate realistic importance values (higher for known predictive features)
base_importances = np.array(
    [0.15, 0.12, 0.10, 0.09, 0.07, 0.05, 0.04, 0.035, 0.03, 0.025, 0.02, 0.015, 0.01, 0.005, -0.002]
)
importance_means = base_importances + np.random.normal(0, 0.005, len(features))
importance_stds = np.abs(np.random.normal(0.01, 0.005, len(features)))

# Create DataFrame and sort by importance
df = pd.DataFrame({"feature": features, "importance_mean": importance_means, "importance_std": importance_stds})
df = df.sort_values("importance_mean", ascending=True).reset_index(drop=True)

# Create ordered categorical for proper sorting in plot
df["feature"] = pd.Categorical(df["feature"], categories=df["feature"], ordered=True)

# Calculate error bar positions (ymin/ymax because coord_flip swaps axes)
df["ymin"] = df["importance_mean"] - df["importance_std"]
df["ymax"] = df["importance_mean"] + df["importance_std"]

# Plot
plot = (
    ggplot(df, aes(x="feature", y="importance_mean", fill="importance_mean"))
    + geom_col(width=0.7)
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.3, color="#333333", size=0.8)
    + geom_hline(yintercept=0, linetype="dashed", color="#666666", size=1)
    + coord_flip()
    + scale_fill_gradient(low="#FFD43B", high="#306998", name="Importance")
    + labs(x="Feature", y="Mean Decrease in Model Score", title="bar-permutation-importance · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        panel_grid_major_y=element_line(alpha=0.3),
        panel_grid_minor=element_line(alpha=0),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
