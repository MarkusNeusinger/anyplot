""" anyplot.ai
count-basic: Basic Count Plot
Library: letsplot 4.11.0 | Python 3.13.14
Quality: 83/100 | Updated: 2026-08-11
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
    geom_text,
    ggplot,
    ggsize,
    labs,
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

# Data - customer satisfaction survey responses. Likert order is kept
# (Excellent -> Very Poor) rather than sorted by frequency: a reader's
# mental model of the scale matters more here than a strict count ranking.
responses = ["Excellent"] * 45 + ["Good"] * 78 + ["Average"] * 52 + ["Poor"] * 23 + ["Very Poor"] * 12
response_order = ["Excellent", "Good", "Average", "Poor", "Very Poor"]

df = pd.DataFrame({"Response": pd.Categorical(responses, categories=response_order, ordered=True)})

counts = df["Response"].value_counts().reindex(response_order)
total = int(counts.sum())
summary = pd.DataFrame(
    {
        "Response": pd.Categorical(response_order, categories=response_order, ordered=True),
        "Count": counts.values,
        "Label": [f"{c}\n{c / total:.0%}" for c in counts.values],
    }
)

# Create count plot (pre-aggregated so the label can carry count + share)
plot = (
    ggplot(summary, aes(x="Response", y="Count"))
    + geom_bar(stat="identity", fill=BRAND, alpha=0.9, width=0.62, color=PAGE_BG, size=0.6)
    + geom_text(aes(label="Label"), size=4.2, vjust=-0.55, lineheight=1.05, color=INK)
    + labs(
        x="Customer Satisfaction Rating",
        y="Number of Responses",
        title="count-basic · letsplot · anyplot.ai",
        caption=f"n = {total} survey respondents",
    )
    + scale_y_continuous(expand=[0, 0, 0.16, 0], limits=[0, 90])
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
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
