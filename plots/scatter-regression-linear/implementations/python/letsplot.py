""" pyplots.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-24
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Simulating advertising spend vs sales revenue relationship
np.random.seed(42)
n = 100
advertising_spend = np.random.uniform(10, 100, n)
# Linear relationship with noise: sales = 2.5 * spend + 50 + noise
sales_revenue = 2.5 * advertising_spend + 50 + np.random.randn(n) * 25

df = pd.DataFrame({"advertising_spend": advertising_spend, "sales_revenue": sales_revenue})

# Calculate regression statistics manually using numpy
x_mean = np.mean(advertising_spend)
y_mean = np.mean(sales_revenue)
slope = np.sum((advertising_spend - x_mean) * (sales_revenue - y_mean)) / np.sum((advertising_spend - x_mean) ** 2)
intercept = y_mean - slope * x_mean

# Calculate R² (coefficient of determination)
y_pred = slope * advertising_spend + intercept
ss_res = np.sum((sales_revenue - y_pred) ** 2)
ss_tot = np.sum((sales_revenue - y_mean) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Create regression equation and R² text
equation_text = f"y = {slope:.2f}x + {intercept:.1f}"
r2_text = f"R² = {r_squared:.3f}"
annotation_text = f"{equation_text}\n{r2_text}"

# Position for annotation (top-left area)
annotation_x = 15
annotation_y = sales_revenue.max() - 10

# Plot with scatter points, regression line, and confidence band
plot = (
    ggplot(df, aes(x="advertising_spend", y="sales_revenue"))  # noqa: F405
    + geom_point(  # noqa: F405
        color="#306998",
        size=5,
        alpha=0.65,
        tooltips=layer_tooltips()  # noqa: F405
        .line("Ad Spend|$@advertising_spend{.1f}K")
        .line("Sales|$@sales_revenue{.1f}K"),
    )
    + geom_smooth(  # noqa: F405
        method="lm", color="#FFD43B", size=2, se=True, level=0.95, fill="#FFD43B", fill_alpha=0.25
    )
    + geom_text(  # noqa: F405
        x=annotation_x,
        y=annotation_y,
        label=annotation_text,
        size=14,
        color="#333333",
        hjust=0,
        vjust=1,
        family="sans-serif",
    )
    + labs(  # noqa: F405
        x="Advertising Spend ($K)", y="Sales Revenue ($K)", title="scatter-regression-linear · letsplot · pyplots.ai"
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        panel_grid=element_line(color="#CCCCCC", size=0.5, linetype="dashed"),  # noqa: F405
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename="plot.html", path=".")
