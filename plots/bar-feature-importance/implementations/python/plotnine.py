""" pyplots.ai
bar-feature-importance: Feature Importance Bar Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_line,
    element_text,
    geom_bar,
    geom_errorbar,
    geom_text,
    ggplot,
    guides,
    labs,
    scale_fill_gradient,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Feature importances from a Random Forest model for house price prediction
features = [
    "Overall Quality",
    "Living Area (sqft)",
    "Garage Cars",
    "Basement Area (sqft)",
    "Year Built",
    "Full Bathrooms",
    "Total Rooms",
    "Fireplaces",
    "Year Remodeled",
    "Lot Area (sqft)",
    "Kitchen Quality",
    "Garage Area (sqft)",
    "Pool Area",
    "Bedrooms",
    "Porch Area (sqft)",
]

importances = [0.285, 0.198, 0.124, 0.089, 0.072, 0.058, 0.043, 0.032, 0.028, 0.024, 0.019, 0.014, 0.008, 0.004, 0.002]

# Standard deviations for error bars (from ensemble variability)
stds = [0.018, 0.015, 0.012, 0.009, 0.008, 0.007, 0.006, 0.005, 0.004, 0.004, 0.003, 0.003, 0.002, 0.001, 0.001]

df = pd.DataFrame({"feature": features, "importance": importances, "std": stds})

# Sort by importance and create ordered categorical for proper display
df = df.sort_values("importance", ascending=True)
df["feature"] = pd.Categorical(df["feature"], categories=df["feature"], ordered=True)

# Create plot
plot = (
    ggplot(df, aes(x="feature", y="importance", fill="importance"))
    + geom_bar(stat="identity", width=0.7)
    + geom_errorbar(aes(ymin="importance - std", ymax="importance + std"), width=0.3, color="#333333", size=0.8)
    + geom_text(aes(label="importance"), format_string="{:.3f}", nudge_y=0.025, size=12, color="#333333", ha="left")
    + coord_flip()
    + scale_fill_gradient(low="#a8d5e5", high="#306998")
    + guides(fill=False)
    + scale_y_continuous(expand=(0, 0, 0.15, 0))
    + labs(title="bar-feature-importance · plotnine · pyplots.ai", x="Feature", y="Importance Score")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#333333"),
        axis_title=element_text(size=20, face="bold"),
        axis_text=element_text(size=16),
        axis_text_y=element_text(size=14),
        plot_title=element_text(size=24, face="bold", ha="center"),
        panel_grid_major_y=element_line(alpha=0),
        panel_grid_minor=element_line(alpha=0),
        panel_grid_major_x=element_line(alpha=0.3, linetype="dashed"),
    )
)

# Save plot
plot.save("plot.png", dpi=300, verbose=False)
