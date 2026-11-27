"""anyplot.ai
box-basic: Basic Box Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os
import sys


# Prevent this file from shadowing the plotnine package (script is named plotnine.py)
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    ggplot,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    stat_summary,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
DEPARTMENT = "Department"  # role: category
SALARY = "Salary ($)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("salaries.csv")
np.random.seed(42)
records = []
for cat in ["Engineering", "Marketing", "Sales", "Support", "Research"]:
    n = np.random.randint(60, 120)
    if cat == "Engineering":
        values = np.random.normal(95000, 15000, n)
    elif cat == "Marketing":
        values = np.random.normal(75000, 12000, n)
    elif cat == "Sales":
        base = np.random.normal(68000, 18000, n)
        outliers = np.random.normal(135000, 6000, 4)
        values = np.concatenate([base, outliers])
    elif cat == "Support":
        values = np.random.normal(55000, 8000, n)
    else:  # Research
        values = np.random.normal(85000, 20000, n)
    records.extend({DEPARTMENT: cat, SALARY: v} for v in values)
df = pd.DataFrame(records)

# Plot
dept_order = df.groupby(DEPARTMENT)[SALARY].median().sort_values().index.tolist()
df[DEPARTMENT] = pd.Categorical(df[DEPARTMENT], categories=dept_order, ordered=True)

plot = (
    ggplot(df, aes(x=DEPARTMENT, y=SALARY, fill=DEPARTMENT))
    + geom_boxplot(
        outlier_size=2.5, outlier_alpha=0.65, outlier_colour=INK_SOFT, size=0.5, alpha=0.85, width=0.6, color=INK_SOFT
    )
    + stat_summary(fun_y=np.median, geom="point", size=4, shape="D", color=INK, fill=INK)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=dept_order)
    + scale_y_continuous(labels=lambda vals: [f"${v / 1000:.0f}k" for v in vals])
    + labs(title="box-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        plot_title=element_text(size=12, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        axis_ticks_major_x=element_blank(),
        axis_ticks_major_y=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_blank(),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
