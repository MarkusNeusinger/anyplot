""" anyplot.ai
count-basic: Basic Count Plot
Library: letsplot 4.11.0 | Python 3.13.14
Quality: 85/100 | Updated: 2026-08-11
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
    scale_fill_manual,
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
# Fixed white-blend tint (not composited against the theme background) so the
# soft bars render as the exact same hex on light and dark surfaces -- only
# the modal bar uses full-strength BRAND. A real alpha/opacity would instead
# blend with PAGE_BG and produce two different visible colors per theme.
BRAND_SOFT = "#66C4A9"

# Data - raw per-observation customer satisfaction survey responses (one row
# per respondent). Likert order is kept (Excellent -> Very Poor) rather than
# sorted by frequency: a reader's mental model of the scale matters more
# here than a strict count ranking.
response_order = ["Excellent", "Good", "Average", "Poor", "Very Poor"]
counts = {"Excellent": 45, "Good": 78, "Average": 52, "Poor": 23, "Very Poor": 12}
modal_response = max(counts, key=counts.get)
responses = [r for r, n in counts.items() for _ in range(n)]
df = pd.DataFrame({"Response": pd.Categorical(responses, categories=response_order, ordered=True)})
df["Modal"] = df["Response"] == modal_response

total = len(df)
avg_count = total / len(response_order)

# Create count plot - geom_bar()'s default stat='count' tallies the raw
# observations directly (no manual pre-aggregation). The modal response
# ("Good") renders in full-strength brand green while the rest use a fixed
# lighter tint of the same hue -- a second layer of visual emphasis beyond
# bar height alone, without introducing a second Imprint hue or a legend.
# Two geom_text(stat='count') layers annotate each bar with its count (bold,
# larger) and share of the total (lighter, smaller), giving the in-bar
# labels a deliberate typographic hierarchy instead of one flat style.
plot = (
    ggplot(df, aes(x="Response"))
    + geom_hline(yintercept=avg_count, linetype="dashed", color=INK_SOFT, size=0.6, alpha=0.8)
    + geom_text(x=4.6, y=avg_count, label="avg", color=INK_SOFT, size=3.8, fontface="bold", vjust=-0.6, hjust=0)
    + geom_bar(aes(fill="Modal"), width=0.62, color=PAGE_BG, size=0.6, show_legend=False)
    + geom_text(
        aes(y="..count..", label="..count.."),
        stat="count",
        color="white",
        size=4.3,
        fontface="bold",
        vjust=1,
        nudge_y=-3.5,
    )
    + geom_text(
        aes(y="..count..", label="..sumpct.."),
        stat="count",
        label_format="{.0f}%",
        color="white",
        alpha=0.85,
        size=3.0,
        vjust=1,
        nudge_y=-8,
    )
    + scale_fill_manual(values={True: BRAND, False: BRAND_SOFT}, guide="none")
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
