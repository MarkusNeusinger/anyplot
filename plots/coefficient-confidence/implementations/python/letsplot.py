""" anyplot.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1 — first series (significant)
NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"  # Non-significant

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
ci_lower = [c - 1.96 * se for c, se in zip(coefficients, std_errors, strict=False)]
ci_upper = [c + 1.96 * se for c, se in zip(coefficients, std_errors, strict=False)]

# Determine significance (CI does not cross zero)
significant = [(ci_low > 0 or ci_hi < 0) for ci_low, ci_hi in zip(ci_lower, ci_upper, strict=False)]

df = pd.DataFrame(
    {
        "variable": variables,
        "coefficient": coefficients,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "significant": significant,
    }
)

# Sort by coefficient magnitude for better visualization
df = df.sort_values("coefficient", ascending=True).reset_index(drop=True)

# Create ordered categorical for proper y-axis ordering
df["variable"] = pd.Categorical(df["variable"], categories=df["variable"].tolist(), ordered=True)

# Add significance label for coloring
df["sig_label"] = df["significant"].map({True: "Significant (p < 0.05)", False: "Not Significant"})
df["sig_label"] = pd.Categorical(
    df["sig_label"], categories=["Significant (p < 0.05)", "Not Significant"], ordered=True
)

# Plot
plot = (
    ggplot(df, aes(x="variable", y="coefficient"))
    # Horizontal reference line at zero
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.8, linetype="dashed")
    # Point range for coefficient with confidence intervals
    + geom_pointrange(aes(ymin="ci_lower", ymax="ci_upper", color="sig_label"), size=1.5, fatten=4)
    # Flip coordinates for horizontal layout
    + coord_flip()
    # Color scale - Okabe-Ito for significant, neutral for non-significant
    + scale_color_manual(values=[BRAND, NEUTRAL], name="Statistical Significance")
    # Labels
    + labs(
        y="Coefficient Estimate",
        x="Predictor Variable",
        title="coefficient-confidence · python · letsplot · anyplot.ai",
    )
    # Theme
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_blank(),
        panel_grid_minor_y=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, face="bold", color=INK),
        axis_title_x=element_text(size=20, color=INK),
        axis_title_y=element_text(size=20, color=INK),
        axis_text_x=element_text(size=16, color=INK_SOFT),
        axis_text_y=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="bottom",
    )
    # Size
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 x 2700)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save interactive HTML
ggsave(plot, f"plot-{THEME}.html", path=".")
