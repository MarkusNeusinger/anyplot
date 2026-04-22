""" pyplots.ai
bar-error: Bar Chart with Error Bars
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
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

# Data: A/B test results showing conversion rates with 95% CI
categories = ["Control", "Variant A", "Variant B", "Variant C", "Variant D"]
values = [12.3, 14.8, 11.2, 16.5, 13.9]  # Conversion rates (%)
errors_lower = [1.2, 1.5, 1.0, 1.8, 1.4]  # Lower CI bound
errors_upper = [1.4, 1.6, 1.1, 2.0, 1.5]  # Upper CI bound

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
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.25, size=1.5, color="#333333")
    + scale_fill_manual(values=["#306998", "#FFD43B", "#306998", "#FFD43B", "#306998"])
    + labs(
        title="bar-error · letsplot · pyplots.ai",
        x="Test Group",
        y="Conversion Rate (%)",
        caption="Error bars show 95% CI",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_caption=element_text(size=14),
        panel_grid_major_x=None,
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
