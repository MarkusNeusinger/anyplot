""" anyplot.ai
range-interval: Range Interval Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-18
"""

import os
import pathlib

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
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#E69F00"  # Okabe-Ito position 5

# Data - Monthly temperature ranges (high/low) for a weather station
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
min_temps = [2, 3, 7, 11, 15, 19, 22, 21, 17, 12, 7, 3]
max_temps = [8, 10, 14, 18, 23, 27, 30, 29, 25, 19, 12, 9]

df = pd.DataFrame({"month": months, "min_temp": min_temps, "max_temp": max_temps})
df["month"] = pd.Categorical(df["month"], categories=months, ordered=True)

# Plot - Range interval chart showing temperature ranges
plot = (
    ggplot(df, aes(x="month", ymin="min_temp", ymax="max_temp"))
    + geom_linerange(size=8, color=BRAND, alpha=0.8)
    + geom_point(aes(y="max_temp"), size=5, color=ACCENT, stroke=0.8)
    + geom_point(aes(y="min_temp"), size=5, color=ACCENT, stroke=0.8)
    + labs(x="Month", y="Temperature (°C)", title="range-interval · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        legend_position="none",
    )
)

# Save
output_dir = pathlib.Path(__file__).parent
output_dir.mkdir(parents=True, exist_ok=True)
plot.save(str(output_dir / f"plot-{THEME}.png"), dpi=300)
