""" pyplots.ai
box-notched: Notched Box Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from lets_plot import *

LetsPlot.setup_html()

# Data - department salaries with different distributions for statistical comparison
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Finance", "Operations"]
data = []

# Engineering: higher salaries, moderate spread
eng_salaries = np.random.normal(95000, 12000, 80)
data.extend([{"Department": "Engineering", "Salary": s} for s in eng_salaries])

# Marketing: medium salaries, wider spread with some outliers
mkt_salaries = np.concatenate(
    [
        np.random.normal(72000, 15000, 70),
        np.array([120000, 125000, 35000]),  # outliers
    ]
)
data.extend([{"Department": "Marketing", "Salary": s} for s in mkt_salaries])

# Sales: variable salaries with commission-based outliers
sales_salaries = np.concatenate(
    [
        np.random.normal(68000, 10000, 65),
        np.array([130000, 140000, 145000, 30000, 28000]),  # high and low outliers
    ]
)
data.extend([{"Department": "Sales", "Salary": s} for s in sales_salaries])

# Finance: similar to engineering but slightly lower (overlapping notches expected)
fin_salaries = np.random.normal(90000, 11000, 75)
data.extend([{"Department": "Finance", "Salary": s} for s in fin_salaries])

# Operations: lower salaries, tight distribution
ops_salaries = np.random.normal(58000, 8000, 85)
data.extend([{"Department": "Operations", "Salary": s} for s in ops_salaries])

df = pd.DataFrame(data)

# Create notched box plot
plot = (
    ggplot(df, aes(x="Department", y="Salary", fill="Department"))
    + geom_boxplot(notch=True, outlier_size=4, outlier_alpha=0.7, size=1.2, alpha=0.85)
    + scale_fill_manual(values=["#306998", "#FFD43B", "#2ECC71", "#E74C3C", "#9B59B6"])
    + labs(title="box-notched · letsplot · pyplots.ai", x="Department", y="Annual Salary (USD)")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, hjust=0.5),
        axis_title_x=element_text(size=22),
        axis_title_y=element_text(size=22),
        axis_text_x=element_text(size=18),
        axis_text_y=element_text(size=18),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html")
