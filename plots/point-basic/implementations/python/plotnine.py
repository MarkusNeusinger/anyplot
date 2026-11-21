"""anyplot.ai
point-basic: Point Estimate Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 89/100 | Updated: 2026-11-21
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_errorbarh,
    geom_point,
    geom_vline,
    ggplot,
    labs,
    scale_y_discrete,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the single-series color
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
REFERENCE = 7.0  # the satisfaction level every category is compared against

# Columns: set these to your table's column names
CATEGORY = "Category"  # role: category
ESTIMATE = "Satisfaction score (1-10)"  # role: estimate
LOWER = "Lower bound (95% CI)"  # role: lower_bound
UPPER = "Upper bound (95% CI)"  # role: upper_bound

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
df = pd.DataFrame(
    {
        CATEGORY: [
            "Customer Service",
            "Product Quality",
            "Delivery Speed",
            "Website Usability",
            "Price Value",
            "Return Process",
            "Product Variety",
            "Packaging",
        ],
        ESTIMATE: [7.8, 8.2, 6.5, 7.1, 6.9, 7.4, 8.0, 7.6],
        LOWER: [7.0, 7.7, 5.3, 6.2, 5.9, 6.7, 7.4, 7.2],
        UPPER: [8.6, 8.7, 7.7, 8.0, 7.9, 8.1, 8.6, 8.0],
    }
)

# Plot: reads only df and the constants above
df = df.sort_values(ESTIMATE).reset_index(drop=True)

plot = (
    ggplot(df, aes(x=ESTIMATE, y=CATEGORY))
    + geom_vline(xintercept=REFERENCE, linetype="dashed", color=INK_SOFT, size=0.5)
    + geom_errorbarh(aes(xmin=LOWER, xmax=UPPER), height=0.3, size=0.8, color=IMPRINT_PALETTE[0])
    + geom_point(size=3.5, color=IMPRINT_PALETTE[0])
    + scale_y_discrete(limits=df[CATEGORY].tolist())
    + labs(title="point-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_line(linewidth=0),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(color=INK, size=12, weight="bold"),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
