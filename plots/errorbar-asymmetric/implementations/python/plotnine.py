""" pyplots.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_text, geom_errorbar, geom_point, ggplot, labs, theme, theme_minimal


# Data - Quarterly revenue projections with asymmetric confidence intervals
np.random.seed(42)
quarters = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025", "Q2 2025"]
central_values = [120, 135, 128, 155, 142, 160]
# Asymmetric intervals: downside risk tends to be larger (conservative projections)
error_lower = [15, 18, 12, 22, 16, 20]
error_upper = [10, 12, 8, 15, 11, 14]

df = pd.DataFrame(
    {
        "quarter": pd.Categorical(quarters, categories=quarters, ordered=True),
        "revenue": central_values,
        "ymin": [c - lo for c, lo in zip(central_values, error_lower, strict=True)],
        "ymax": [c + up for c, up in zip(central_values, error_upper, strict=True)],
    }
)

# Create plot with asymmetric error bars
plot = (
    ggplot(df, aes(x="quarter", y="revenue"))
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.3, size=1.5, color="#306998")
    + geom_point(size=6, color="#306998")
    + labs(
        x="Quarter",
        y="Revenue (Million USD)",
        title="errorbar-asymmetric · plotnine · pyplots.ai",
        caption="Error bars show 10th-90th percentile forecast range",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=0),
        plot_title=element_text(size=24, ha="center"),
        plot_caption=element_text(size=14, ha="right"),
        panel_grid_major=element_line(alpha=0.3),
        panel_grid_minor=element_line(alpha=0.15),
    )
)

# Save
plot.save("plot.png", dpi=300)
