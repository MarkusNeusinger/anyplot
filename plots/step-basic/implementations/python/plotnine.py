"""anyplot.ai
step-basic: Basic Step Plot
Library: plotnine | Python 3.13
Quality: pending | Updated: 2026-04-30
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_step,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"
ACCENT = "#D55E00"

# Data - Monthly cumulative sales figures showing discrete jumps
months = list(range(1, 13))
cumulative_sales = [12, 12, 27, 27, 45, 58, 58, 73, 89, 89, 105, 120]

df = pd.DataFrame({"month": months, "sales": cumulative_sales})

# Plot
plot = (
    ggplot(df, aes(x="month", y="sales"))
    + geom_step(color=BRAND, size=1.5, direction="hv")
    + geom_point(color=ACCENT, size=4, stroke=0.5)
    + labs(x="Month", y="Cumulative Sales (thousands)", title="step-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        text=element_text(size=14, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        axis_line=element_line(color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, width=16, height=9, verbose=False)
