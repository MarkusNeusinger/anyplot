"""anyplot.ai
line-basic: Basic Line Plot
Library: plotnine 0.15.3 | Python 3.13.13
Quality: 89/100 | Updated: 2026-04-29
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
PASSENGERS = "Passengers (thousands)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("passengers.csv")
# Monthly passenger counts at a regional airport: steady growth, a summer peak, random noise
rng = np.random.default_rng(42)
months = pd.date_range("2021-01-01", periods=48, freq="MS")
trend = np.linspace(420, 640, len(months))
seasonal = 1 + 0.18 * np.sin(2 * np.pi * (months.month.to_numpy() - 4) / 12)
df = pd.DataFrame({MONTH: months, PASSENGERS: trend * seasonal + rng.normal(0, 14, len(months))})

# Plot
plot = (
    ggplot(df, aes(x=MONTH, y=PASSENGERS))
    + geom_line(size=1.2, color=BRAND)
    + geom_point(size=2.5, color=BRAND)
    + scale_x_datetime(date_breaks="6 months", date_labels="%b %Y")
    + labs(title="line-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.08),
        panel_grid_minor=element_blank(),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
