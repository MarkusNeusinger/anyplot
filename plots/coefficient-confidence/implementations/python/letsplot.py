""" pyplots.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Regression coefficients for housing price prediction model
np.random.seed(42)

variables = [
    "Square Footage",
    "Number of Bedrooms",
    "Number of Bathrooms",
    "Lot Size (acres)",
    "Age of Home (years)",
    "Distance to Downtown",
    "School District Rating",
    "Garage Spaces",
    "Has Pool",
    "Has Fireplace",
    "Renovated Recently",
    "Crime Rate Index",
]

# Generate realistic coefficients - some significant, some not
coefficients = [0.45, 0.12, 0.28, 0.18, -0.15, -0.22, 0.35, 0.08, 0.14, 0.05, 0.20, -0.32]
std_errors = [0.08, 0.09, 0.07, 0.06, 0.04, 0.05, 0.06, 0.07, 0.10, 0.08, 0.09, 0.07]

# Calculate confidence intervals (95%)
ci_lower = [c - 1.96 * se for c, se in zip(coefficients, std_errors)]
ci_upper = [c + 1.96 * se for c, se in zip(coefficients, std_errors)]

# Determine significance (CI does not cross zero)
significant = [(l > 0 or u < 0) for l, u in zip(ci_lower, ci_upper)]

df = pd.DataFrame(
    {
        "variable": variables,
        "coefficient": coefficients,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "significant": significant,
    }
)

# Sort by coefficient magnitude for better visualization (ascending so largest shows at top after flip)
df = df.sort_values("coefficient", ascending=True).reset_index(drop=True)

# Create ordered categorical for proper y-axis ordering
df["variable"] = pd.Categorical(df["variable"], categories=df["variable"].tolist(), ordered=True)

# Add significance label for coloring (ordered so Significant comes first in legend)
df["sig_label"] = df["significant"].map({True: "Significant (p < 0.05)", False: "Not Significant"})
df["sig_label"] = pd.Categorical(
    df["sig_label"], categories=["Significant (p < 0.05)", "Not Significant"], ordered=True
)

# Plot - use pointrange with coord_flip for horizontal layout
plot = (
    ggplot(df, aes(x="variable", y="coefficient"))
    # Horizontal reference line at zero (will be vertical after flip)
    + geom_hline(yintercept=0, color="#888888", size=1, linetype="dashed")
    # Point range for coefficient with confidence intervals
    + geom_pointrange(aes(ymin="ci_lower", ymax="ci_upper", color="sig_label"), size=1.5, fatten=4)
    # Flip coordinates for horizontal layout
    + coord_flip()
    # Color scale - Python Blue for significant, muted for non-significant
    + scale_color_manual(values=["#306998", "#999999"], name="Statistical Significance")
    # Labels
    + labs(
        y="Coefficient Estimate (Standardized)",
        x="Predictor Variable",
        title="coefficient-confidence · letsplot · pyplots.ai",
    )
    # Theme
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="bottom",
        panel_grid_major_x=element_blank(),
    )
    # Size
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 x 2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML
ggsave(plot, "plot.html", path=".")
