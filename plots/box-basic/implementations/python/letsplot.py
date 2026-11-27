"""anyplot.ai
box-basic: Basic Box Plot
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-28
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    as_discrete,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_classic,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: category
SALARY = "Annual Salary (USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("salaries.csv")
np.random.seed(42)
distributions = {
    "Engineering": (85000, 15000),
    "Marketing": (65000, 12000),
    "Sales": (70000, 20000),
    "HR": (55000, 10000),
    "Finance": (75000, 14000),
}

data = []
for cat, (mean, std) in distributions.items():
    n = np.random.randint(50, 100)
    values = np.random.normal(mean, std, n)
    outliers = np.array([mean + 2.5 * std, mean + 3.0 * std, mean + 3.5 * std])
    values = np.concatenate([values, outliers])
    data.extend([(cat, v) for v in values])

df = pd.DataFrame(data, columns=[DEPARTMENT, SALARY])

# Plot
title = "box-basic · python · letsplot · anyplot.ai"

plot = (
    ggplot(df, aes(x=as_discrete(DEPARTMENT, order=1, order_by="..middle.."), y=SALARY, fill=DEPARTMENT))
    + geom_boxplot(
        alpha=0.85,
        size=1.2,
        fatten=1.5,
        outlier_size=2.5,
        outlier_shape=21,
        outlier_color=INK_SOFT,
        width=0.78,
        color=INK,
        tooltips=layer_tooltips()
        .title(f"@{{{DEPARTMENT}}}")
        .line("Median|$@{..middle..}")
        .line("Q1|$@{..lower..}")
        .line("Q3|$@{..upper..}")
        .line("Min|$@{..ymin..}")
        .line("Max|$@{..ymax..}"),
    )
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + scale_y_continuous(format="${,.0f}", expand=[0.06, 0])
    + labs(title=title, subtitle="Salary distributions by department, ordered by median")
    + theme_classic()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color="transparent"),
        plot_title=element_text(size=16, color=INK, face="bold"),
        plot_subtitle=element_text(size=12, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        axis_line_x=element_line(color=INK_SOFT),
        axis_line_y=element_line(color=INK_SOFT),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
        panel_border=element_blank(),
        legend_position="none",
        plot_margin=[10, 10, 10, 10],
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
