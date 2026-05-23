"""anyplot.ai
drawdown-basic: Drawdown Chart
Library: letsplot | Python 3.13
Quality: pending | Updated: 2026-05-23
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
    layer_tooltips,
    scale_color_manual,
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

# anyplot palette — semantic exception: loss/down → red, recovery → green
DRAWDOWN_COLOR = "#B71D27"  # palette pos 3
RECOVERY_COLOR = "#009E73"  # palette pos 1

# Data
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

price = 100 * np.cumprod(1 + returns)
running_max = np.maximum.accumulate(price)
drawdown = (price - running_max) / running_max * 100

df = pd.DataFrame({"date": dates, "price": price, "drawdown": drawdown, "day_num": np.arange(n_days)})

max_dd_idx = int(np.argmin(drawdown))
max_dd_value = drawdown[max_dd_idx]

recovery_mask = (drawdown == 0) & (np.roll(drawdown, 1) < 0)
recovery_points = df[recovery_mask].copy()
recovery_points["marker_type"] = "Recovery Point"

max_dd_df = df.iloc[[max_dd_idx]].copy()
max_dd_df["marker_type"] = "Max Drawdown"

markers_df = pd.concat([max_dd_df, recovery_points], ignore_index=True)

# Plot
marker_tooltips = (
    layer_tooltips().format("@drawdown", ".1f").line("@marker_type").line("Day|@day_num").line("Drawdown (%)|@drawdown")
)

plot = (
    ggplot(df, aes(x="day_num", y="drawdown"))
    + geom_area(fill=DRAWDOWN_COLOR, alpha=0.30)
    + geom_line(color=DRAWDOWN_COLOR, size=1.2)
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.8, linetype="dashed")
    + geom_point(
        data=markers_df,
        mapping=aes(x="day_num", y="drawdown", color="marker_type"),
        size=7,
        stroke=2.0,
        shape=21,
        fill=PAGE_BG,
        tooltips=marker_tooltips,
    )
    + scale_color_manual(name="", values={"Max Drawdown": DRAWDOWN_COLOR, "Recovery Point": RECOVERY_COLOR})
    + labs(
        x="Trading Days",
        y="Drawdown (%)",
        title="drawdown-basic · python · letsplot · anyplot.ai",
        caption=f"Max Drawdown: {max_dd_value:.1f}% on Day {max_dd_idx}",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=GRID_COLOR, size=0.5),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        plot_caption=element_text(size=10, color=INK_MUTED),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=10, color=INK),
        legend_position="top",
        axis_line=element_line(color=INK_SOFT),
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
