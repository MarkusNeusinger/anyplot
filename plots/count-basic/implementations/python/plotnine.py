""" anyplot.ai
count-basic: Basic Count Plot
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 94/100 | Updated: 2026-08-11
"""

import os

import pandas as pd
from plotnine import (
    aes,
    after_stat,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — brand green marks the modal category, muted grey covers the rest
BRAND = "#009E73"

# Data - Netflix user ratings from a streaming survey
ratings = ["5 Stars"] * 285 + ["4 Stars"] * 198 + ["3 Stars"] * 142 + ["2 Stars"] * 89 + ["1 Star"] * 56
rating_order = ["5 Stars", "4 Stars", "3 Stars", "2 Stars", "1 Star"]
df = pd.DataFrame({"Rating": pd.Categorical(ratings, categories=rating_order, ordered=True)})

# Highlight the modal category so the count plot makes a point, not just a tally
mode_rating = df["Rating"].value_counts().idxmax()
df["Highlight"] = df["Rating"].apply(lambda r: "Mode" if r == mode_rating else "Other")

# Plot - native stat='count' drives the bars and the count labels; the percentage
# labels read plotnine's own `prop` stat variable, forced to share-of-total (its
# default is share-of-fill-group) via the aes(group=1) override — a
# grammar-of-graphics idiom that keeps the annotation fully data-driven.
plot = (
    ggplot(df, aes(x="Rating", fill="Highlight"))
    + geom_bar(width=0.62, color=PAGE_BG, size=0.6, show_legend=False)
    + geom_text(
        aes(label=after_stat("count")),
        stat="count",
        color=INK,
        size=8,
        va="bottom",
        nudge_y=10,
        fontweight="bold",
        format_string="{:.0f}",
    )
    + geom_text(
        aes(label=after_stat("prop"), group=1),
        stat="count",
        color=INK_MUTED,
        size=6,
        va="bottom",
        nudge_y=27,
        format_string="{:.0%}",
    )
    + scale_fill_manual(values={"Mode": BRAND, "Other": INK_MUTED})
    + scale_y_continuous(breaks=[0, 100, 200, 300], expand=(0, 0, 0.16, 0))
    + labs(x="Rating", y="Number of Responses", title="count-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK, weight="bold"),
        text=element_text(size=7),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
