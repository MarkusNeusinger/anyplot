"""anyplot.ai
bar-basic: Basic Bar Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-28
"""

import os

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

# Data - Quarterly revenue by department, sorted descending
categories = ["Electronics", "Clothing", "Sports", "Home & Garden", "Toys & Games", "Books"]
values = [45200, 32800, 31400, 28500, 19800, 18900]
df = pd.DataFrame({"category": categories, "value": values})

mean_val = sum(values) / len(values)
mean_label_df = pd.DataFrame({"x": ["Toys & Games"], "y": [mean_val + 1500], "label": [f"Avg: ${int(mean_val):,}"]})

anyplot_theme = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
    panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
    panel_grid_major_x=element_blank(),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
    panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),  # noqa: F405
    axis_title=element_text(color=INK, size=12),  # noqa: F405
    axis_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
    axis_text_x=element_text(angle=30, hjust=1, color=INK_SOFT, size=10),  # noqa: F405
    axis_line=element_line(color=INK_SOFT),  # noqa: F405
    plot_title=element_text(color=INK, size=16),  # noqa: F405
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
    legend_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
    legend_title=element_text(color=INK),  # noqa: F405
)

plot = (
    ggplot(df, aes(x="category", y="value"))  # noqa: F405
    + geom_bar(  # noqa: F405
        fill=BRAND,
        stat="identity",
        width=0.7,
        tooltips=layer_tooltips()  # noqa: F405
        .title("@category")
        .line("Revenue|$@{value}"),
    )
    + geom_text(  # noqa: F405
        aes(label="value"),  # noqa: F405
        position=position_nudge(y=2000),  # noqa: F405
        size=4,
        label_format="${,d}",
        color=INK,
        fontface="bold",
    )
    + geom_hline(yintercept=mean_val, color=INK_MUTED, size=0.7, linetype="dashed")  # noqa: F405
    + geom_text(  # noqa: F405
        data=mean_label_df,
        mapping=aes(x="x", y="y", label="label"),  # noqa: F405
        color=INK_MUTED,
        size=3,
        hjust=0.5,
        fontface="italic",
    )
    + labs(  # noqa: F405
        x="Department", y="Quarterly Revenue ($)", title="bar-basic · python · letsplot · anyplot.ai"
    )
    + scale_x_discrete(limits=categories)  # noqa: F405
    + scale_y_continuous(limits=[0, 52000], format="${,.0f}", expand=[0, 0, 0.08, 0])  # noqa: F405
    + anyplot_theme
    + ggsize(800, 450)  # noqa: F405
)

ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
