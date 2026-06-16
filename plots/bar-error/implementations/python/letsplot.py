""" anyplot.ai
bar-error: Bar Chart with Error Bars
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-10
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
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "rgba(26,26,23,0.08)" if THEME == "light" else "rgba(240,239,232,0.08)"

# Okabe-Ito palette - first series is brand green
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

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

# Create bar chart with error bars and enhanced design
plot = (
    ggplot(df, aes(x="category", y="value", fill="category"))
    + geom_bar(stat="identity", width=0.68, show_legend=False, alpha=0.92)
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.23, size=1.3, color=INK_SOFT, alpha=0.85)
    + scale_fill_manual(values=IMPRINT)
    + labs(
        title="bar-error · letsplot · anyplot.ai",
        x="Test Group",
        y="Conversion Rate (%)",
        caption="Error bars show 95% CI | Interactive HTML export available",
    )
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=GRID_COLOR, size=0.22),
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
