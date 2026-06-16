""" anyplot.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-06
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave  # noqa: F401


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
SECONDARY = "#C475FD"

# Data - Advertising spend vs sales revenue relationship
np.random.seed(42)
n = 100
advertising_spend = np.random.uniform(10, 100, n)
sales_revenue = 2.5 * advertising_spend + 50 + np.random.randn(n) * 25

df = pd.DataFrame({"advertising_spend": advertising_spend, "sales_revenue": sales_revenue})

# Calculate regression statistics
x_mean = np.mean(advertising_spend)
y_mean = np.mean(sales_revenue)
slope = np.sum((advertising_spend - x_mean) * (sales_revenue - y_mean)) / np.sum((advertising_spend - x_mean) ** 2)
intercept = y_mean - slope * x_mean

# Calculate R²
y_pred = slope * advertising_spend + intercept
ss_res = np.sum((sales_revenue - y_pred) ** 2)
ss_tot = np.sum((sales_revenue - y_mean) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Create annotation text
equation_text = f"y = {slope:.2f}x + {intercept:.1f}"
r2_text = f"R² = {r_squared:.3f}"
annotation_text = f"{equation_text}\n{r2_text}"

# Position for annotation
annotation_x = 15
annotation_y = sales_revenue.max() - 10

# Plot
plot = (
    ggplot(df, aes(x="advertising_spend", y="sales_revenue"))  # noqa: F405
    + geom_point(  # noqa: F405
        color=BRAND,
        size=4,
        alpha=0.65,
        tooltips=layer_tooltips()  # noqa: F405
        .line("Ad Spend|$@advertising_spend{.1f}K")
        .line("Sales|$@sales_revenue{.1f}K"),
    )
    + geom_smooth(  # noqa: F405
        method="lm", color=SECONDARY, size=2, se=True, level=0.95, fill=SECONDARY, fill_alpha=0.15
    )
    + geom_text(  # noqa: F405
        x=annotation_x, y=annotation_y, label=annotation_text, size=14, color=INK, hjust=0, vjust=1, family="sans-serif"
    )
    + labs(  # noqa: F405
        x="Advertising Spend ($K)", y="Sales Revenue ($K)", title="scatter-regression-linear · letsplot · anyplot.ai"
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        panel_grid_major=element_line(color=INK_SOFT, size=0.3, linetype="blank"),  # noqa: F405
        axis_text=element_text(size=16, color=INK_SOFT),  # noqa: F405
        axis_title=element_text(size=20, color=INK),  # noqa: F405
        plot_title=element_text(size=24, color=INK),  # noqa: F405
        axis_line=element_line(color=INK_SOFT, size=0.5),  # noqa: F405
    )
)

# Save outputs
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
