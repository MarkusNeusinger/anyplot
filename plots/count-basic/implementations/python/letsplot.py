""" anyplot.ai
count-basic: Basic Count Plot
Library: letsplot 4.11.0 | Python 3.13.14
Quality: 89/100 | Updated: 2026-08-11
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
    geom_hline,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_labels,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Imprint palette position 1 — always first series

# Data - raw per-observation customer satisfaction survey responses (one row
# per respondent). Likert order is kept (Excellent -> Very Poor) rather than
# sorted by frequency: a reader's mental model of the scale matters more
# here than a strict count ranking.
response_order = ["Excellent", "Good", "Average", "Poor", "Very Poor"]
responses = ["Excellent"] * 45 + ["Good"] * 78 + ["Average"] * 52 + ["Poor"] * 23 + ["Very Poor"] * 12
df = pd.DataFrame({"Response": pd.Categorical(responses, categories=response_order, ordered=True)})

total = len(df)
avg_count = total / len(response_order)

# Create count plot - geom_bar()'s default stat='count' tallies the raw
# observations directly (no manual pre-aggregation), and layer_labels()
# reads the same computed ..count../..sumpct.. variables to annotate each
# bar with its count and share of the total.
plot = (
    ggplot(df, aes(x="Response"))
    + geom_hline(yintercept=avg_count, linetype="dashed", color=INK_SOFT, size=0.6, alpha=0.8)
    + geom_text(x=4.6, y=avg_count, label="avg", color=INK_SOFT, size=3.0, vjust=-0.6, hjust=0)
    + geom_bar(
        fill=BRAND,
        alpha=0.9,
        width=0.62,
        color=PAGE_BG,
        size=0.6,
        labels=layer_labels().format("..sumpct..", ".0f").line("@{..count..}").line("@{..sumpct..}%"),
    )
    + labs(
        x="Customer Satisfaction Rating",
        y="Number of Responses",
        title="count-basic · letsplot · anyplot.ai",
        caption=f"n = {total} survey respondents",
    )
    + scale_y_continuous(expand=[0, 0, 0.16, 0], limits=[0, 90])
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_caption=element_text(size=9, color=INK_SOFT),
    )
    + ggsize(800, 450)
)

# Save as PNG (scale 4x for 3200 x 1800 px) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
