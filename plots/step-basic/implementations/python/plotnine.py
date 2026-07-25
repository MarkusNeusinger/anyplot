"""anyplot.ai
step-basic: Basic Step Plot
Library: plotnine 0.15.3 | Python 3.13.13
Quality: 90/100 | Updated: 2026-07-25
"""

import os

import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_point,
    geom_step,
    ggplot,
    labs,
    scale_x_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_TERTIARY = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"
ACCENT = "#C475FD"

# Data - Monthly cumulative sales figures showing discrete jumps, vs. an annual target
months = list(range(1, 13))
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
cumulative_sales = [12, 12, 27, 27, 45, 58, 58, 73, 89, 89, 105, 120]
target = 100

df = pd.DataFrame({"month": months, "sales": cumulative_sales})

# Plot
plot = (
    ggplot(df, aes(x="month", y="sales"))
    + geom_hline(yintercept=target, color=INK_SOFT, size=0.6, linetype="dashed")
    + annotate("text", x=1, y=target + 5, label=f"Annual target: {target}k", color=INK_TERTIARY, size=6, ha="left")
    + geom_step(color=BRAND, size=1.0, direction="hv")
    + geom_point(color=ACCENT, size=2.5, stroke=0.4)
    + scale_x_continuous(breaks=months, labels=month_labels)
    + labs(x="Month", y="Cumulative Sales (thousands)", title="step-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK, weight="bold"),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
