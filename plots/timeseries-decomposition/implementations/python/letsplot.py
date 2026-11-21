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

# Imprint palette: one color per component panel, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SEASONAL_PERIOD = 12  # observations per seasonal cycle (monthly data, annual cycle)

# Columns: set these to your table's column names
DATE = "Date"  # role: date
VALUE = "Temperature (°C)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("temperature.csv", parse_dates=[DATE])
np.random.seed(42)
n_months = 60
trend_line = np.linspace(15, 18, n_months)  # gradual warming trend
annual_cycle = 12 * np.sin(2 * np.pi * np.arange(n_months) / 12)
noise = np.random.normal(0, 1.5, n_months)
df = pd.DataFrame(
    {DATE: pd.date_range("2019-01-01", periods=n_months, freq="MS"), VALUE: trend_line + annual_cycle + noise}
)

# Plot: reads only df and the constants above
series = df.set_index(DATE)[VALUE]
# seasonal_decompose needs two full cycles and no gaps: shorten the period for short tables, bridge gaps for the fit only
period = min(SEASONAL_PERIOD, len(series) // 2)
decomposition = seasonal_decompose(series.interpolate(limit_direction="both"), model="additive", period=period)
components = {
    "Original": series,
    "Trend": decomposition.trend,
    "Seasonal": decomposition.seasonal,
    "Residual": decomposition.resid,
}

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.2),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=12, face="bold"),
)

# Panel y-label: the unit alone, because the full column name does not fit a short panel
unit = VALUE[VALUE.rfind("(") :].strip("()") if "(" in VALUE else VALUE
panels = []
for i, (name, series) in enumerate(components.items()):
    is_last = i == len(components) - 1
    panel_df = series.dropna().rename(VALUE).rename_axis(DATE).reset_index()
    panel = (
        ggplot(panel_df, aes(x=DATE, y=VALUE))
        + geom_line(color=IMPRINT_PALETTE[i], size=1.0)
        + scale_x_datetime(limits=[df[DATE].min(), df[DATE].max()])
        + labs(x=DATE if is_last else "", y=unit, title=name)
        + anyplot_theme
    )
    if not is_last:
        panel = panel + theme(axis_text_x=element_blank())
    panels.append(panel)

final_plot = (
    gggrid(panels, ncol=1)
    + ggsize(800, 450)
    + ggtitle("timeseries-decomposition · python · letsplot · anyplot.ai")
    + theme(plot_title=element_text(color=INK, size=16, face="bold"))
)

# Save PNG (800x450 at scale 4 = 3200x1800) and interactive HTML
ggsave(final_plot, f"plot-{THEME}.png", scale=4)
ggsave(final_plot, f"plot-{THEME}.html")

# lets-plot writes into a lets-plot-images subdirectory; move the files here
lp_dir = "lets-plot-images"
if os.path.exists(lp_dir):
    for fname in [f"plot-{THEME}.png", f"plot-{THEME}.html"]:
        src = os.path.join(lp_dir, fname)
        if os.path.exists(src):
            shutil.move(src, fname)
    if not os.listdir(lp_dir):
        os.rmdir(lp_dir)
