"""anyplot.ai
line-basic: Basic Line Plot
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 88/100 | Updated: 2026-06-03
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
    geom_area,
    geom_line,
    geom_point,
    geom_smooth,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_x_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens (Imprint palette, theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"
AREA_ALPHA = 0.15 if THEME == "light" else 0.28  # stronger fill in dark for readability

MONTH_NAMES = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}

# Data — monthly temperature readings over a year
np.random.seed(42)
months = np.arange(1, 13)
base_temp = 15 + 12 * np.sin((months - 4) * np.pi / 6)
temperature = base_temp + np.random.randn(12) * 1.5

df = pd.DataFrame({"month": months, "temperature": temperature})
df_peak = df.nlargest(1, "temperature").copy()
df_peak["label"] = df_peak.apply(lambda r: f"{MONTH_NAMES[int(r['month'])]}: {r['temperature']:.1f}°C", axis=1)

# Plot
title = "line-basic · python · letsplot · anyplot.ai"

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=RULE, size=0.5),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16),
)

# Richer tooltip: header title + formatted temperature value
tooltips = (
    layer_tooltips()
    .title("Monthly Temperature")
    .format("@temperature", ".1f")
    .line("Month: @month")
    .line("Temp: @temperature °C")
)

plot = (
    ggplot(df, aes(x="month", y="temperature"))
    + geom_area(fill=BRAND, alpha=AREA_ALPHA)
    # letsplot-distinctive: LOESS smooth shows the seasonal trend independent of the raw line
    + geom_smooth(method="loess", color=INK_SOFT, size=0.8, linetype="dashed", se=False)
    + geom_line(color=BRAND, size=1.5)
    + geom_point(color=BRAND, size=4, alpha=0.9, tooltips=tooltips)
    # Peak marker emphasis
    + geom_point(data=df_peak, mapping=aes(x="month", y="temperature"), color=BRAND, size=7)
    # Peak annotation label — makes the data narrative explicit
    + geom_text(
        data=df_peak,
        mapping=aes(x="month", y="temperature", label="label"),
        color=INK,
        size=4,
        nudge_x=0.4,
        nudge_y=0.9,
    )
    + labs(x="Month", y="Temperature (°C)", title=title)
    + scale_x_continuous(breaks=list(range(1, 13)))
    + ggsize(800, 450)
    + theme_minimal()
    + anyplot_theme
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
