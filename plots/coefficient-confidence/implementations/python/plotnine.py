""" pyplots.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
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
    scale_color_manual,
    theme,
    theme_minimal,
)


# Data: Coefficients from a housing price regression model
np.random.seed(42)
data = {
    "variable": [
        "Living Area (sq ft)",
        "Bedrooms",
        "Bathrooms",
        "Garage Capacity",
        "Lot Size (acres)",
        "Age (years)",
        "Distance to City (mi)",
        "School Rating",
        "Crime Index",
        "Pool",
        "Central AC",
        "Renovated",
    ],
    "coefficient": [0.42, 0.15, 0.28, 0.18, 0.08, -0.22, -0.14, 0.25, -0.31, 0.12, 0.09, 0.06],
    "ci_lower": [0.35, 0.02, 0.18, 0.08, -0.02, -0.30, -0.22, 0.15, -0.42, 0.01, 0.02, -0.04],
    "ci_upper": [0.49, 0.28, 0.38, 0.28, 0.18, -0.14, -0.06, 0.35, -0.20, 0.23, 0.16, 0.16],
}

df = pd.DataFrame(data)

# Determine significance (CI does not cross zero)
df["significant"] = ~((df["ci_lower"] <= 0) & (df["ci_upper"] >= 0))
df["significance"] = df["significant"].map({True: "Significant", False: "Not Significant"})

# Order variables by coefficient magnitude for readability
df["variable"] = pd.Categorical(
    df["variable"], categories=df.sort_values("coefficient")["variable"].tolist(), ordered=True
)

# Create plot
plot = (
    ggplot(df, aes(x="coefficient", y="variable", color="significance"))
    + geom_vline(xintercept=0, linetype="dashed", color="#888888", size=1)
    + geom_errorbarh(aes(xmin="ci_lower", xmax="ci_upper"), height=0.3, size=1.2)
    + geom_point(size=5)
    + scale_color_manual(values={"Significant": "#306998", "Not Significant": "#FFD43B"})
    + labs(
        x="Coefficient Estimate (Standardized)",
        y="Predictor Variable",
        title="coefficient-confidence · plotnine · pyplots.ai",
        color="Statistical Significance",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_y=element_text(size=14),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
        panel_grid_major_y=element_line(color="#EEEEEE", size=0.5),
        panel_grid_major_x=element_line(color="#DDDDDD", size=0.5),
    )
)

# Save
plot.save("plot.png", dpi=300)
