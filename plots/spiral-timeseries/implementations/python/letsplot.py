""" anyplot.ai
spiral-timeseries: Spiral Time Series Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 87/100 | Created: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_path,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_color_viridis,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# 5 years of synthetic daily average temperatures (northern hemisphere)
np.random.seed(42)
dates = pd.date_range("2019-01-01", "2023-12-31", freq="D")
n = len(dates)

doy = dates.day_of_year.values
year_num = (dates.year - 2019).values
days_in_yr = np.array([366 if y % 4 == 0 else 365 for y in dates.year])
frac_year = (doy - 1) / days_in_yr

temp = 15.0 * np.sin(2 * np.pi * (doy - 80) / days_in_yr) + 12.0 + np.random.normal(0, 2.0, n)

# Archimedean spiral: clockwise from top (Jan 1 = 12 o'clock)
inner_r = 1.5
spacing = 1.0
angle = np.pi / 2 - 2 * np.pi * (year_num + frac_year)
r = inner_r + spacing * (year_num + frac_year)
df = pd.DataFrame({"x": r * np.cos(angle), "y": r * np.sin(angle), "temp": temp})

# Radial grid lines at each month start
grid_rows = []
for ms in pd.date_range("2019-01-01", "2023-12-01", freq="MS"):
    yr = ms.year - 2019
    frac_m = (ms.day_of_year - 1) / (366 if ms.year % 4 == 0 else 365)
    ang = np.pi / 2 - 2 * np.pi * (yr + frac_m)
    r_end = inner_r + spacing * (yr + frac_m)
    grid_rows.append({"x": 0.0, "y": 0.0, "xend": r_end * np.cos(ang), "yend": r_end * np.sin(ang)})
grid_df = pd.DataFrame(grid_rows)

# Year labels slightly left of the top spoke
ang_lbl = np.pi / 2 + 0.18
year_df = pd.DataFrame(
    [
        {
            "x": (inner_r + spacing * yr) * np.cos(ang_lbl),
            "y": (inner_r + spacing * yr) * np.sin(ang_lbl),
            "label": str(2019 + yr),
        }
        for yr in range(5)
    ]
)

# Month labels on the outer ring using 2020 (leap year) reference angles
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
outer_r = inner_r + spacing * 5 + 0.65
month_rows = []
for i, mname in enumerate(MONTHS):
    mid = pd.Timestamp(2020, i + 1, 15)
    frac_m = (mid.day_of_year - 1) / 366
    ang_m = np.pi / 2 - 2 * np.pi * frac_m
    month_rows.append({"x": outer_r * np.cos(ang_m), "y": outer_r * np.sin(ang_m), "label": mname})
month_df = pd.DataFrame(month_rows)

# Theme: void base + custom chrome
anyplot_theme = theme_void() + theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=16),
)

title = "Daily Temperatures 2019–2023 · spiral-timeseries · letsplot · anyplot.ai"

plot = (
    ggplot()
    + geom_segment(
        data=grid_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK_SOFT, alpha=0.25, size=0.5
    )
    + geom_path(data=df, mapping=aes(x="x", y="y", color="temp"), size=2.5)
    + scale_color_viridis(name="Temp (°C)")
    + geom_text(data=year_df, mapping=aes(x="x", y="y", label="label"), color=INK, size=14)
    + geom_text(data=month_df, mapping=aes(x="x", y="y", label="label"), color=INK_SOFT, size=11)
    + coord_fixed()
    + labs(title=title)
    + anyplot_theme
    + ggsize(900, 900)
)

ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
