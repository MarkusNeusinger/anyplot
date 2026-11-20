""" anyplot.ai
bar-feature-importance: Feature Importance Bar Chart
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-20
"""

import os

import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_line,
    element_rect,
    element_text,
    geom_col,
    geom_errorbar,
    geom_text,
    ggplot,
    guides,
    labs,
    scale_fill_gradient,
    scale_x_discrete,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential ramp from position 1 to position 3
SEQ_LOW = "#009E73"
SEQ_HIGH = "#4467A3"

# Column names
FEATURE = "feature"  # role: feature
IMPORTANCE = "importance"  # role: importance
STD = "std"  # role: std

# Data - Feature importances from a Random Forest model for house price prediction
df = pd.DataFrame(
    {
        FEATURE: [
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
        ],
        IMPORTANCE: [
            0.285,
            0.198,
            0.124,
            0.089,
            0.072,
            0.058,
            0.043,
            0.032,
            0.028,
            0.024,
            0.019,
            0.014,
            0.008,
            0.004,
            0.002,
        ],
        # Standard deviations from ensemble variability
        STD: [0.018, 0.015, 0.012, 0.009, 0.008, 0.007, 0.006, 0.005, 0.004, 0.004, 0.003, 0.003, 0.002, 0.001, 0.001],
    }
)
df = df.sort_values(IMPORTANCE, ascending=False).reset_index(drop=True)

# Plot
# Error-bar ends and the label position past them, derived from df
LO, HI = "lo", "hi"
df[LO] = df[IMPORTANCE] - df[STD]
df[HI] = df[IMPORTANCE] + df[STD]
label_gap = df[HI].max() * 0.012

plot = (
    ggplot(df, aes(x=FEATURE, y=IMPORTANCE, fill=IMPORTANCE))
    + geom_col(width=0.7)
    + geom_errorbar(aes(ymin="lo", ymax="hi"), width=0.3, color=INK_SOFT, size=0.5)
    + geom_text(aes(y="hi", label=IMPORTANCE), format_string="{:.3f}", nudge_y=label_gap, size=8, color=INK, ha="left")
    + scale_x_discrete(limits=df[FEATURE].tolist()[::-1])
    + coord_flip()
    + scale_fill_gradient(low=SEQ_LOW, high=SEQ_HIGH)
    + guides(fill=False)
    + scale_y_continuous(expand=(0, 0, 0.12, 0))
    + labs(title="bar-feature-importance · python · plotnine · anyplot.ai", x="Feature", y="Importance Score")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK_SOFT),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        panel_grid_major_y=element_line(alpha=0),
        panel_grid_minor=element_line(alpha=0),
        panel_grid_major_x=element_line(color=INK, size=0.2, alpha=0.15),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
