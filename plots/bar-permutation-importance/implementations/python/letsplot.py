""" pyplots.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_flip,
    element_line,
    element_text,
    geom_bar,
    geom_errorbar,
    geom_vline,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_gradient,
    scale_x_discrete,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data: Simulated permutation importance from a Random Forest model
np.random.seed(42)

features = [
    "Income Level",
    "Credit Score",
    "Employment Years",
    "Debt Ratio",
    "Account Age",
    "Payment History",
    "Loan Amount",
    "Interest Rate",
    "Property Value",
    "Monthly Expenses",
    "Savings Balance",
    "Number of Accounts",
    "Recent Inquiries",
    "Education Level",
    "Region Code",
]

# Generate importance values - higher for more predictive features
base_importance = np.array(
    [0.15, 0.12, 0.09, 0.08, 0.06, 0.05, 0.04, 0.03, 0.025, 0.02, 0.015, 0.01, 0.008, 0.005, 0.002]
)
# Add some noise
importance_mean = base_importance + np.random.uniform(-0.005, 0.005, len(features))
importance_std = np.random.uniform(0.003, 0.02, len(features))

# Create DataFrame and sort by importance
df = pd.DataFrame({"feature": features, "importance_mean": importance_mean, "importance_std": importance_std})
df = df.sort_values("importance_mean", ascending=True).reset_index(drop=True)

# Create ordered categorical for proper y-axis ordering
df["feature"] = pd.Categorical(df["feature"], categories=df["feature"].tolist(), ordered=True)

# Calculate error bar positions
df["ymin"] = df["importance_mean"] - df["importance_std"]
df["ymax"] = df["importance_mean"] + df["importance_std"]

# Create the plot with horizontal bars using geom_bar + coord_flip
plot = (
    ggplot(df, aes(x="feature", y="importance_mean", fill="importance_mean"))
    + geom_bar(stat="identity", width=0.7, alpha=0.9)
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.25, size=0.8, color="#333333")
    + geom_vline(xintercept=0, color="#888888", size=0.8, linetype="dashed")
    + coord_flip()
    + scale_fill_gradient(low="#FFD43B", high="#306998", guide="none")
    + scale_x_discrete()
    + labs(x="Feature", y="Mean Decrease in Model Score", title="bar-permutation-importance · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_y=element_text(size=14),
        panel_grid_major_x=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor_x=element_line(color="#EEEEEE", size=0.3),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700) - path="." saves to current directory
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive view
ggsave(plot, "plot.html", path=".")
