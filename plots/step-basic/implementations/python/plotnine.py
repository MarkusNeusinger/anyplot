""" pyplots.ai
step-basic: Basic Step Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import pandas as pd
from plotnine import aes, element_line, element_text, geom_point, geom_step, ggplot, labs, theme, theme_minimal


# Data - Monthly cumulative sales figures showing discrete jumps
months = list(range(1, 13))
cumulative_sales = [12, 12, 27, 27, 45, 58, 58, 73, 89, 89, 105, 120]

df = pd.DataFrame({"month": months, "sales": cumulative_sales})

# Plot
plot = (
    ggplot(df, aes(x="month", y="sales"))
    + geom_step(color="#306998", size=1.5, direction="hv")
    + geom_point(color="#FFD43B", size=4, stroke=0.5)
    + labs(x="Month", y="Cumulative Sales (thousands)", title="step-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#eeeeee", size=0.3, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
