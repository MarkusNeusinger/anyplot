""" pyplots.ai
bar-error: Bar Chart with Error Bars
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-27
"""

import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_col,
    geom_errorbar,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Survey results showing average satisfaction scores with 95% CI
categories = ["Product Quality", "Customer Service", "Delivery Speed", "Price Value", "Website UX", "Return Policy"]
values = [4.2, 3.8, 4.5, 3.5, 4.0, 4.3]
errors = [0.3, 0.4, 0.2, 0.5, 0.35, 0.25]  # 95% CI half-widths

df = pd.DataFrame(
    {
        "category": categories,
        "value": values,
        "error_lower": [v - e for v, e in zip(values, errors, strict=True)],
        "error_upper": [v + e for v, e in zip(values, errors, strict=True)],
    }
)

# Preserve category order
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="category", y="value"))
    + geom_col(aes(fill="category"), width=0.7, show_legend=False)
    + geom_errorbar(aes(ymin="error_lower", ymax="error_upper"), width=0.25, size=1.2, color="#333333")
    + scale_fill_manual(values=["#306998", "#FFD43B", "#306998", "#FFD43B", "#306998", "#FFD43B"])
    + labs(
        x="Survey Category",
        y="Satisfaction Score (1-5)",
        title="bar-error \u00b7 plotnine \u00b7 pyplots.ai",
        caption="Error bars represent 95% CI",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=14, angle=25, ha="right"),
        axis_text_y=element_text(size=16),
        plot_caption=element_text(size=14, style="italic"),
        panel_grid_major_x=element_line(alpha=0),
        panel_grid_minor=element_line(alpha=0),
        panel_grid_major_y=element_line(alpha=0.3),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
