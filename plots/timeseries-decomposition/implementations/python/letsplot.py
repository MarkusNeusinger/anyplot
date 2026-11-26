"""anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    ggtitle,
    labs,
    scale_x_datetime,
    theme,
)
from statsmodels.tsa.seasonal import seasonal_decompose


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
# element_line has no alpha argument; lets-plot reads the alpha from an rgba() color
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
PERIOD = 12  # seasonal cycle length in observations (monthly data, annual cycle)

# Columns: set these to your table's column names
DATE = "Date"  # role: date
TEMPERATURE = "Temperature (°C)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("temperature.csv")
np.random.seed(42)
n_months = 60
dates = pd.date_range("2019-01-01", periods=n_months, freq="MS")
trend = np.linspace(15, 15.6, n_months)  # slow warming, about 0.1 °C per year
seasonal = 12 * np.sin(2 * np.pi * np.arange(n_months) / 12)  # annual cycle
noise = np.random.normal(0, 1.5, n_months)
df = pd.DataFrame({DATE: dates, TEMPERATURE: trend + seasonal + noise})

# Plot: reads only df and the constants above
original = df.set_index(DATE)[TEMPERATURE]
period = max(2, min(PERIOD, len(original) // 2))  # the decomposition needs two full cycles
decomposition = seasonal_decompose(original.interpolate(limit_direction="both"), model="additive", period=period)
components = {
    "Original Series": original,
    "Trend": decomposition.trend,
    "Seasonal": decomposition.seasonal,
    "Residual": decomposition.resid,
}

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_line(color=GRID, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=9),
    axis_text=element_text(color=INK_SOFT, size=9),
    axis_line=element_blank(),
    axis_line_x=element_line(color=INK_SOFT),
    axis_line_y=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=12, face="bold"),
)

# One shared date range so a date lines up vertically in every panel
date_limits = [df[DATE].min(), df[DATE].max()]
panels = []
for i, (name, series) in enumerate(components.items()):
    panel_df = series.dropna().rename(TEMPERATURE).rename_axis(DATE).reset_index()
    is_last = i == len(components) - 1
    panel = (
        ggplot(panel_df, aes(x=DATE, y=TEMPERATURE))
        + geom_line(color=IMPRINT_PALETTE[i], size=1.0)
        + scale_x_datetime(limits=date_limits, format="%Y")
        + labs(x=DATE if is_last else "", y=TEMPERATURE, title=name)
        + anyplot_theme
    )
    if not is_last:
        panel = panel + theme(axis_text_x=element_blank(), axis_ticks_x=element_blank())
    panels.append(panel)

final_plot = (
    gggrid(panels, ncol=1)
    + ggsize(800, 450)
    + ggtitle("timeseries-decomposition · python · letsplot · anyplot.ai")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(color=INK, size=16, face="bold"),
    )
)

ggsave(final_plot, f"plot-{THEME}.png", scale=4)
ggsave(final_plot, f"plot-{THEME}.html")

# Move files from the lets-plot subdirectory to the current directory
lp_dir = "lets-plot-images"
if os.path.exists(lp_dir):
    for fname in [f"plot-{THEME}.png", f"plot-{THEME}.html"]:
        src = os.path.join(lp_dir, fname)
        if os.path.exists(src):
            shutil.move(src, fname)
    if not os.listdir(lp_dir):
        os.rmdir(lp_dir)
