""" pyplots.ai
violin-basic: Basic Violin Plot
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-21
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data
np.random.seed(42)

# Ordered by median salary (high → low) for visual storytelling
dept_order = ["Engineering", "Design", "Marketing", "Sales"]
palette = ["#306998", "#2E8B57", "#E8A317", "#E07A5F"]

data = []

# Engineering: bimodal (junior ~$70k + senior ~$115k) — showcases violin strength
eng_junior = np.random.normal(70000, 8000, 80)
eng_senior = np.random.normal(115000, 12000, 120)
eng_values = np.clip(np.concatenate([eng_junior, eng_senior]), 30000, 200000)
for v in eng_values:
    data.append({"Department": "Engineering", "Salary": v})

# Design: moderate spread, roughly normal
design_values = np.random.normal(80000, 18000, 120)
design_values = np.clip(design_values, 30000, 200000)
for v in design_values:
    data.append({"Department": "Design", "Salary": v})

# Marketing: narrower with a small cluster of high earners
mkt_base = np.random.normal(72000, 12000, 130)
mkt_high = np.random.normal(105000, 8000, 20)
mkt_values = np.clip(np.concatenate([mkt_base, mkt_high]), 30000, 200000)
for v in mkt_values:
    data.append({"Department": "Marketing", "Salary": v})

# Sales: right-skewed (many moderate earners, few top performers)
sales_values = np.random.exponential(20000, 180) + 45000
sales_values = np.clip(sales_values, 30000, 200000)
for v in sales_values:
    data.append({"Department": "Sales", "Salary": v})

df = pd.DataFrame(data)

# Plot
plot = (
    ggplot(df, aes(x="Department", y="Salary", fill="Department"))  # noqa: F405
    + geom_violin(  # noqa: F405
        quantiles=[0.25, 0.5, 0.75], quantile_lines=True, size=1.2, alpha=0.85, trim=False, color="#2C3E50"
    )
    + scale_x_discrete(limits=dept_order)  # noqa: F405
    + scale_fill_manual(values=dict(zip(dept_order, palette, strict=True)))  # noqa: F405
    + scale_y_continuous(  # noqa: F405
        format="${,.0f}"
    )
    + labs(  # noqa: F405
        x="Department", y="Salary", title="violin-basic \u00b7 letsplot \u00b7 pyplots.ai"
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        legend_position="none",
        panel_grid_major_x=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
