"""anyplot.ai
range-interval: Range Interval Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_linerange,
    geom_point,
    ggplot,
    labs,
    scale_x_discrete,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1
ACCENT = "#AE3030"  # Imprint palette position 5

# Columns: set these to your table's column names
MONTH = "Month"  # role: category
LOW = "Lowest temperature (°C)"  # role: min_value
HIGH = "Highest temperature (°C)"  # role: max_value

# Data: replace this block with your own table, for example df = pd.read_csv("temperatures.csv")
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        LOW: [2, 3, 7, 11, 15, 19, 22, 21, 17, 12, 7, 3],
        HIGH: [8, 10, 14, 18, 23, 27, 30, 29, 25, 19, 12, 9],
    }
)

# Plot: reads only df and the constants above
plot = (
    ggplot(df, aes(x=MONTH, ymin=LOW, ymax=HIGH))
    + geom_linerange(size=5, color=BRAND, alpha=0.8)
    + geom_point(aes(y=HIGH), size=3, color=ACCENT, stroke=0.5)
    + geom_point(aes(y=LOW), size=3, color=ACCENT, stroke=0.5)
    + scale_x_discrete(limits=df[MONTH].unique().tolist())
    + labs(y="Temperature (°C)", title="range-interval · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
