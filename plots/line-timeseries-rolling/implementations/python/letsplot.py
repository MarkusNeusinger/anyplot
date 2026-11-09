""" anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: the rolling average takes the brand green, the raw readings the next position
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WINDOW = 14  # rolling window in days

# Columns: set these to your table's column names
DATE = "Date"  # role: date
TEMPERATURE = "Temperature (°C)"  # role: value
ROLLING = "14-Day Rolling Average"  # role: rolling_avg

# Data: replace this block with your own table, for example df = pd.read_csv("sensor.csv")
np.random.seed(42)
n_days = 180
days = np.arange(n_days)
temperature = 15 + 10 * np.sin(2 * np.pi * days / 365) + np.random.normal(0, 3, n_days) + np.linspace(0, 2, n_days)
df = pd.DataFrame({DATE: pd.date_range("2024-01-01", periods=n_days, freq="D"), TEMPERATURE: temperature})
df[ROLLING] = df[TEMPERATURE].rolling(window=WINDOW).mean()

# Plot: reads only df and the constants above
raw_label = "Raw Data"
series = "Series"
long_df = pd.concat(
    [
        df[[DATE, TEMPERATURE]].assign(**{series: raw_label}),
        df[[DATE, ROLLING]].rename(columns={ROLLING: TEMPERATURE}).assign(**{series: ROLLING}),
    ],
    ignore_index=True,
).dropna(subset=[TEMPERATURE])

plot = (
    ggplot(long_df, aes(x=DATE, y=TEMPERATURE, color=series))
    + geom_line(
        aes(alpha=series, size=series), tooltips=layer_tooltips().line("@" + series).line("@{" + TEMPERATURE + "}")
    )
    + scale_color_manual(values={ROLLING: IMPRINT_PALETTE[0], raw_label: IMPRINT_PALETTE[1]}, name="")
    + scale_alpha_manual(values={ROLLING: 1.0, raw_label: 0.55}, name="")
    + scale_size_manual(values={ROLLING: 1.6, raw_label: 0.5}, name="")
    + scale_x_datetime(format="%b %Y")
    + labs(title="line-timeseries-rolling · python · letsplot · anyplot.ai", x=DATE, y=TEMPERATURE)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=GRID, size=0.3),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.6),
        axis_line_y=element_line(color=INK_SOFT, size=0.6),
        axis_ticks=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_position="top",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
