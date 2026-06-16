""" anyplot.ai
box-notched: Notched Box Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

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

# Create notched box plot with Okabe-Ito palette
plot = (
    ggplot(df, aes(x="Department", y="Salary", fill="Department", color="Department"))
    + geom_boxplot(notch=True, outlier_size=4, outlier_alpha=0.8, size=1.2, alpha=0.85)
    + scale_fill_manual(values=IMPRINT)
    + scale_color_manual(values=IMPRINT)
    + labs(title="box-notched · letsplot · anyplot.ai", x="Department", y="Annual Salary (USD)")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_y=element_line(color=INK, size=0.3, linetype="solid"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text_x=element_text(size=16, color=INK_SOFT),
        axis_text_y=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_title=element_text(size=24, color=INK, hjust=0.5),
        legend_position="none",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, f"plot-{THEME}.html", path=".")
