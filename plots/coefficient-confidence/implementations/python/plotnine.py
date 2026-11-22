"""anyplot.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-18
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_errorbarh,
    geom_point,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_y_discrete,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NULL_VALUE = 0  # the null hypothesis: a coefficient of zero
SIGNIFICANT = "Significant"
NOT_SIGNIFICANT = "Not significant"

# Columns: set these to your table's column names
VARIABLE = "Predictor variable"  # role: variable
COEFFICIENT = "Coefficient estimate (standardized)"  # role: coefficient
CI_LOWER = "CI lower"  # role: ci_lower
CI_UPPER = "CI upper"  # role: ci_upper

# Data: replace this block with your own table, for example df = pd.read_csv("coefficients.csv")
df = pd.DataFrame(
    {
        VARIABLE: [
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
        COEFFICIENT: [0.42, 0.15, 0.28, 0.18, 0.08, -0.22, -0.14, 0.25, -0.31, 0.12, 0.09, 0.06],
        CI_LOWER: [0.35, 0.02, 0.18, 0.08, -0.02, -0.30, -0.22, 0.15, -0.42, 0.01, 0.02, -0.04],
        CI_UPPER: [0.49, 0.28, 0.38, 0.28, 0.18, -0.14, -0.06, 0.35, -0.20, 0.23, 0.16, 0.16],
    }
)

# Plot: reads only df and the constants above
# Significant when the interval does not cross the null value
crosses = (df[CI_LOWER] <= NULL_VALUE) & (df[CI_UPPER] >= NULL_VALUE)
df["Statistical significance"] = crosses.map({False: SIGNIFICANT, True: NOT_SIGNIFICANT})
SIGNIFICANCE = "Statistical significance"

# Rows ordered by coefficient magnitude: the largest estimate at the top
row_order = df.sort_values(COEFFICIENT)[VARIABLE].tolist()

plot = (
    ggplot(df, aes(x=COEFFICIENT, y=VARIABLE, color=SIGNIFICANCE))
    + geom_vline(xintercept=NULL_VALUE, linetype="dashed", color=INK_SOFT, size=0.6)
    + geom_errorbarh(aes(xmin=CI_LOWER, xmax=CI_UPPER), height=0.3, size=0.8)
    + geom_point(size=3.2)
    + scale_y_discrete(limits=row_order)
    + scale_color_manual(values=[IMPRINT_PALETTE[0], INK_SOFT], limits=[SIGNIFICANT, NOT_SIGNIFICANT])
    + labs(
        x=COEFFICIENT, y=VARIABLE, title="coefficient-confidence · python · plotnine · anyplot.ai", color=SIGNIFICANCE
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.12),
        panel_grid_major_y=element_line(color=INK, size=0.2, alpha=0.06),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_title=element_text(size=12, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
