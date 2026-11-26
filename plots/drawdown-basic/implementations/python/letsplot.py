"""anyplot.ai
drawdown-basic: Drawdown Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-26
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
    geom_hline,
    geom_line,
    geom_point,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_shape_manual,
    scale_size_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID_COLOR = "#4A4A4433" if THEME == "light" else "#B8B7B033"

# Imprint palette — semantic exception: loss/down → red, recovery → green
DRAWDOWN_COLOR = "#AE3030"  # palette pos 3
RECOVERY_COLOR = "#009E73"  # palette pos 1

# Constants
MAX_LABEL = "Max Drawdown"
RECOVERY_LABEL = "Recovery Point"

# Columns: set these to your table's column names
DATE = "Date"  # role: date
PRICE = "Price"  # role: price
DRAWDOWN = "Drawdown (%)"  # role: extra
MARKER = "Marker"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 500
dates = pd.date_range(start="2022-01-01", periods=n_days, freq="B")

returns = np.random.normal(0.0005, 0.012, n_days)
returns[40:70] = np.random.normal(-0.008, 0.015, 30)
returns[70:120] = np.random.normal(0.012, 0.01, 50)
returns[180:230] = np.random.normal(-0.006, 0.018, 50)
returns[230:300] = np.random.normal(0.008, 0.012, 70)
returns[350:400] = np.random.normal(-0.007, 0.016, 50)
returns[400:450] = np.random.normal(0.009, 0.01, 50)

df = pd.DataFrame({DATE: dates, PRICE: 100 * np.cumprod(1 + returns)})

# Plot
df[DRAWDOWN] = (df[PRICE] / df[PRICE].cummax() - 1) * 100

max_dd_idx = int(df[DRAWDOWN].idxmin())
max_dd_value = df[DRAWDOWN].iloc[max_dd_idx]
peak_idx = int(df.index[(df[DRAWDOWN] == 0) & (df.index <= max_dd_idx)][-1])
after_trough = df.index[(df[DRAWDOWN] == 0) & (df.index > max_dd_idx)]
duration_days = (df[DATE].iloc[max_dd_idx] - df[DATE].iloc[peak_idx]).days
if len(after_trough):
    recovery_text = f"{(df[DATE].iloc[after_trough[0]] - df[DATE].iloc[max_dd_idx]).days} days to recover"
else:
    recovery_text = "not yet recovered"
caption = (
    f"Max Drawdown: {max_dd_value:.1f}% | Duration: {duration_days} days peak to trough | Recovery: {recovery_text}"
)

recovery_points = df[(df[DRAWDOWN] == 0) & (df[DRAWDOWN].shift(1) < 0)].copy()
recovery_points[MARKER] = RECOVERY_LABEL
max_dd_point = df.iloc[[max_dd_idx]].copy()
max_dd_point[MARKER] = MAX_LABEL
markers = pd.concat([max_dd_point, recovery_points], ignore_index=True)

plot = (
    ggplot(df, aes(x=DATE, y=DRAWDOWN))
    + geom_area(fill=DRAWDOWN_COLOR, alpha=0.30)
    + geom_line(color=DRAWDOWN_COLOR, size=1.2)
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.8, linetype="dashed")
    + geom_point(
        data=markers,
        mapping=aes(x=DATE, y=DRAWDOWN, color=MARKER, shape=MARKER, size=MARKER),
        stroke=1.5,
        fill=PAGE_BG,
        alpha=0.8,
    )
    + scale_color_manual(name="", values={MAX_LABEL: DRAWDOWN_COLOR, RECOVERY_LABEL: RECOVERY_COLOR})
    + scale_shape_manual(name="", values={MAX_LABEL: 16, RECOVERY_LABEL: 21})
    + scale_size_manual(name="", values={MAX_LABEL: 6, RECOVERY_LABEL: 3})
    + scale_x_datetime(format="%b %Y")
    + labs(x=DATE, y=DRAWDOWN, title="drawdown-basic · python · letsplot · anyplot.ai", caption=caption)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=GRID_COLOR, size=0.5),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        plot_caption=element_text(size=10, color=INK_MUTED),
        legend_background=element_rect(fill=ELEVATED_BG),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=10, color=INK),
        legend_position="top",
        axis_line=element_line(color=INK_SOFT),
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
