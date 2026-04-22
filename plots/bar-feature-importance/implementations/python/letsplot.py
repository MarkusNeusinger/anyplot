""" pyplots.ai
bar-feature-importance: Feature Importance Bar Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_flip,
    element_line,
    element_text,
    geom_bar,
    geom_errorbar,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Feature importances from a Random Forest model (loan default prediction)
data = {
    "feature": [
        "income",
        "credit_score",
        "age",
        "employment_years",
        "debt_ratio",
        "num_accounts",
        "loan_amount",
        "education_level",
        "housing_status",
        "num_dependents",
        "payment_history",
        "savings_balance",
        "loan_term",
        "marital_status",
        "region",
    ],
    "importance": [
        0.182,
        0.156,
        0.124,
        0.098,
        0.087,
        0.072,
        0.065,
        0.054,
        0.048,
        0.038,
        0.032,
        0.022,
        0.012,
        0.007,
        0.003,
    ],
    "std": [0.025, 0.022, 0.018, 0.015, 0.012, 0.010, 0.009, 0.008, 0.007, 0.006, 0.005, 0.004, 0.003, 0.002, 0.001],
}

df = pd.DataFrame(data)

# Sort by importance (highest at top after coord_flip)
df = df.sort_values("importance", ascending=True)
df["feature"] = pd.Categorical(df["feature"], categories=df["feature"].tolist(), ordered=True)

# Calculate error bar limits (ymin/ymax before flip becomes xmin/xmax after flip)
df["ymin"] = df["importance"] - df["std"]
df["ymax"] = df["importance"] + df["std"]

# Label position (slightly beyond error bar)
df["label_pos"] = df["ymax"] + 0.008

# Format labels
df["label"] = df["importance"].apply(lambda x: f"{x:.3f}")

# Create plot
plot = (
    ggplot(df, aes(x="feature", y="importance", fill="importance"))
    + geom_bar(stat="identity", width=0.7)
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.3, size=0.8, color="#333333")
    + geom_text(aes(x="feature", y="label_pos", label="label"), hjust=0, size=10, color="#333333")
    + scale_fill_gradient(low="#A8D5E5", high="#306998", name="Importance")
    + coord_flip()
    + labs(title="bar-feature-importance · letsplot · pyplots.ai", x="Feature", y="Importance Score")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        panel_grid_major_x=element_line(color="#E0E0E0", size=0.5),
        panel_grid_minor_x=element_line(color="#F0F0F0", size=0.3),
        panel_grid_major_y=element_line(size=0),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 x 2700 px)
ggsave(plot, "plot.png", scale=3, path=".")

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
