""" anyplot.ai
bar-feature-importance: Feature Importance Bar Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 74/100 | Updated: 2026-05-10
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_errorbar,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    guide_colorbar,
    guides,
    labs,
    scale_fill_gradient,
    scale_x_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette; imprint_seq runs from brand green (low) to blue (high)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEQ_LOW, SEQ_HIGH = IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Importance (mean decrease in impurity)"  # role: importance
STD = "Std. deviation"  # role: std

# Data: replace this block with your own table, for example df = pd.read_csv("feature_importances.csv")
# Normalized feature importances of a random forest that predicts loan default
df = pd.DataFrame(
    {
        FEATURE: [
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
        IMPORTANCE: [
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
        STD: [0.025, 0.022, 0.018, 0.015, 0.012, 0.010, 0.009, 0.008, 0.007, 0.006, 0.005, 0.004, 0.003, 0.002, 0.001],
    }
)

# Plot: reads only df and the constants above
# Ascending order puts the most important feature at the top of the discrete y axis
bars = df.sort_values(IMPORTANCE, kind="stable").reset_index(drop=True)
bars["lower"] = bars[IMPORTANCE] - bars[STD]
bars["upper"] = bars[IMPORTANCE] + bars[STD]
# Value labels start just past the error bar, or past the bar end where no std is given
bars["label_at"] = bars["upper"].fillna(bars[IMPORTANCE])

plot = (
    ggplot(bars, aes(x=IMPORTANCE, y=FEATURE))
    + geom_bar(aes(fill=IMPORTANCE), stat="identity", orientation="y", width=0.72, color=PAGE_BG, size=0.4)
    # Page-colored halo under the ink error bar keeps it visible on both ends of the gradient
    + geom_errorbar(aes(xmin="lower", xmax="upper"), width=0.36, size=1.6, color=PAGE_BG)
    + geom_errorbar(aes(xmin="lower", xmax="upper"), width=0.3, size=0.6, color=INK)
    + geom_text(
        aes(x="label_at", label=IMPORTANCE), label_format=".3~g", hjust=0, nudge_x=8, nudge_unit="px", size=4, color=INK
    )
    + scale_fill_gradient(low=SEQ_LOW, high=SEQ_HIGH)
    # Headroom on the right for the value label of the longest bar
    + scale_x_continuous(limits=[0, bars["label_at"].max() * 1.12])
    + guides(fill=guide_colorbar(title=IMPORTANCE.replace(" (", "\n("), barheight=140))
    + labs(title="bar-feature-importance · python · letsplot · anyplot.ai", x=IMPORTANCE, y=FEATURE)
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_x=element_line(color=RULE, size=0.4),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line_y=element_line(color=INK_SOFT, size=0.5),
        axis_ticks=element_blank(),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=RULE),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=9, color=INK_SOFT),
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
