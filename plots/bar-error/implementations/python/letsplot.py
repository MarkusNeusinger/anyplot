""" anyplot.ai
bar-error: Bar Chart with Error Bars
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-10
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_errorbar,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
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

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Data: A/B test results showing conversion rates with 95% CI
categories = ["Control", "Variant A", "Variant B", "Variant C", "Variant D"]
values = [12.3, 14.8, 11.2, 16.5, 13.9]
errors_lower = [1.2, 1.5, 1.0, 1.8, 1.4]
errors_upper = [1.4, 1.6, 1.1, 2.0, 1.5]

df = pd.DataFrame(
    {
        "category": categories,
        "value": values,
        "ymin": [v - el for v, el in zip(values, errors_lower, strict=True)],
        "ymax": [v + eu for v, eu in zip(values, errors_upper, strict=True)],
    }
)

# Create bar chart with error bars
plot = (
    ggplot(df, aes(x="category", y="value", fill="category"))
    + geom_bar(stat="identity", width=0.7, show_legend=False)
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.25, size=1.5, color=INK_SOFT)
    + scale_fill_manual(values=OKABE_ITO)
    + labs(
        title="bar-error · letsplot · anyplot.ai",
        x="Test Group",
        y="Conversion Rate (%)",
        caption="Error bars show 95% CI",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
        panel_grid_major_x=element_line(color="transparent"),
        panel_grid_minor=element_line(color="transparent"),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        plot_caption=element_text(size=14, color=INK_SOFT),
    )
    + ggsize(1600, 900)
)

# Save as PNG and HTML with theme suffix
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
