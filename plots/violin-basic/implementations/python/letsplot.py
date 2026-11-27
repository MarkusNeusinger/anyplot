"""anyplot.ai
violin-basic: Basic Violin Plot
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    geom_violin,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_x_discrete,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: category
SALARY = "Salary"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("salaries.csv")
np.random.seed(42)

# Engineering: bimodal (junior ~$70k + senior ~$115k) — showcases violin strength
eng_junior = np.random.normal(70000, 8000, 80)
eng_senior = np.random.normal(115000, 12000, 120)
eng_values = np.concatenate([eng_junior, eng_senior])

# Design: moderate spread, roughly normal
design_values = np.random.normal(80000, 18000, 120)

# Marketing: narrower with a small cluster of high earners
mkt_values = np.concatenate([np.random.normal(72000, 12000, 130), np.random.normal(105000, 8000, 20)])

# Sales: right-skewed (many moderate earners, few top performers)
sales_values = np.random.exponential(20000, 180) + 45000

groups = {"Engineering": eng_values, "Design": design_values, "Marketing": mkt_values, "Sales": sales_values}
df = pd.DataFrame(
    {
        DEPARTMENT: [name for name, values in groups.items() for _ in values],
        SALARY: np.clip(np.concatenate(list(groups.values())), 30000, 200000),
    }
)

# Plot
title = "violin-basic · python · letsplot · anyplot.ai"

# Departments ordered by descending median salary
dept_order = df.groupby(DEPARTMENT)[SALARY].median().sort_values(ascending=False).index.tolist()

# Violins colored by Imprint palette, thin boxplot overlay for clear quartile markers
plot = (
    ggplot(df, aes(x=DEPARTMENT, y=SALARY, fill=DEPARTMENT))
    + geom_violin(
        alpha=0.82,
        trim=True,
        color=INK_SOFT,
        size=0.8,
        tooltips=layer_tooltips().line("^fill").line(f"{SALARY}|@{{{SALARY}}}"),
    )
    + geom_boxplot(
        width=0.10,
        fill=PAGE_BG,
        color=INK,
        size=1.2,
        outlier_color=PAGE_BG,
        outlier_fill=PAGE_BG,
        tooltips=layer_tooltips().line("^fill").line("Median|@{..middle..}").line("IQR|@{..lower..} – @{..upper..}"),
    )
    + scale_x_discrete(limits=dept_order)
    + scale_fill_manual(values=dict(zip(dept_order, IMPRINT_PALETTE, strict=False)))
    + scale_y_continuous(format="${,.0f}")
    + labs(title=title)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.2),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title=element_text(color=INK, size=12),
        axis_text=element_text(color=INK_SOFT, size=10),
        plot_title=element_text(color=INK, size=16),
        legend_position="none",
        axis_ticks=element_blank(),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
