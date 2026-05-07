""" anyplot.ai
count-basic: Basic Count Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-07
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Data - Netflix user ratings from a streaming dataset
ratings = ["5 Stars"] * 285 + ["4 Stars"] * 198 + ["3 Stars"] * 142 + ["2 Stars"] * 89 + ["1 Star"] * 56
df = pd.DataFrame({"Rating": ratings})

# Create ordered categories (descending star rating)
rating_order = ["5 Stars", "4 Stars", "3 Stars", "2 Stars", "1 Star"]
df["Rating"] = pd.Categorical(df["Rating"], categories=rating_order, ordered=True)

# Count data for labels
counts = df["Rating"].value_counts().reindex(rating_order)
count_df = pd.DataFrame({"Rating": rating_order, "Count": counts.values})
count_df["Rating"] = pd.Categorical(count_df["Rating"], categories=rating_order, ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="Rating", fill="Rating"))
    + geom_bar(width=0.7, show_legend=False)
    + geom_text(aes(x="Rating", y="Count", label="Count"), data=count_df, size=14, va="bottom", nudge_y=8)
    + scale_fill_manual(values=OKABE_ITO)
    + labs(x="Rating", y="Number of Responses", title="count-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        text=element_text(size=14),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
