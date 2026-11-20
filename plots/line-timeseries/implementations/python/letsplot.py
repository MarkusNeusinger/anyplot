"""anyplot.ai
line-timeseries: Time Series Line Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ACCENT_SOFT = "#D4A574" if THEME == "light" else "#8B7355"

# Imprint palette: single series uses position 1
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
TEMPERATURE = "Temperature (°C)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("temperature.csv", parse_dates=["Date"])
np.random.seed(42)
n_days = 365
day_of_year = np.arange(n_days)
df = pd.DataFrame(
    {
        DATE: pd.date_range(start="2024-01-01", periods=n_days, freq="D"),
        TEMPERATURE: 12 + 15 * np.sin(2 * np.pi * (day_of_year - 80) / n_days) + np.random.randn(n_days) * 3,
    }
)

# Plot: reads only df and the constants above
extremes = df.loc[[df[TEMPERATURE].idxmax(), df[TEMPERATURE].idxmin()]]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.25, linetype="solid"),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=12, color=INK, face="bold"),
    axis_text=element_text(size=10, color=INK_SOFT),
    axis_text_x=element_text(angle=45, hjust=1),
    plot_title=element_text(size=16, color=INK, face="bold"),
    axis_line=element_line(color=INK_SOFT, size=0.4),
)

plot = (
    ggplot(df, aes(x=DATE, y=TEMPERATURE))
    + geom_smooth(method="loess", span=0.15, color=ACCENT_SOFT, size=1.2, alpha=0.5, se=False)
    + geom_line(color=BRAND, size=0.8, alpha=0.8)
    + geom_point(color=BRAND, size=1.2, alpha=0.6)
    + geom_point(data=extremes, color=BRAND, size=3.5, alpha=0.95)
    + labs(title="line-timeseries · python · letsplot · anyplot.ai")
    + scale_x_datetime(format="%b %Y")
    + ggsize(800, 450)
    + anyplot_theme
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
