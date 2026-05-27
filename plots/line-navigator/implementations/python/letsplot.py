""" anyplot.ai
line-navigator: Line Chart with Mini Navigator
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-27
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
    geom_rect,
    geom_text,
    gggrid,
    ggplot,
    ggsize,
    ggtitle,
    labs,
    layer_tooltips,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
RULE_FAINT = "rgba(26,26,23,0.08)" if THEME == "light" else "rgba(240,239,232,0.08)"

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = ANYPLOT_PALETTE[0]

# Data — 3 years of daily temperature sensor readings
np.random.seed(42)
n_days = 1095
dates = pd.date_range(start="2023-01-01", periods=n_days, freq="D")

trend = np.linspace(20, 35, n_days)
seasonality = 10 * np.sin(2 * np.pi * np.arange(n_days) / 365)
noise = np.random.normal(0, 2, n_days)
temperature = trend + seasonality + noise

df_full = pd.DataFrame({"date": dates, "temperature": temperature})

# Selected range — last 6 months shown in detail
selected_days = 180
range_start_idx = len(df_full) - selected_days
df_selected = df_full.iloc[range_start_idx:].copy()

# Y-axis limits for main chart
main_y_min = df_selected["temperature"].min()
main_y_max = df_selected["temperature"].max()
main_y_range = main_y_max - main_y_min
main_y_lower = main_y_min - main_y_range * 0.05
main_y_upper = main_y_max + main_y_range * 0.12

# Y-axis limits for navigator (full data extent)
nav_y_min = df_full["temperature"].min() - 2
nav_y_max = df_full["temperature"].max() + 2

# Date range for selection window
select_xmin = df_full["date"].iloc[range_start_idx]
select_xmax = df_full["date"].iloc[-1]
start_label = select_xmin.strftime("%b %d, %Y")
end_label = select_xmax.strftime("%b %d, %Y")

range_label_df = pd.DataFrame(
    {
        "x": [select_xmin + (select_xmax - select_xmin) / 2],
        "y": [main_y_upper - main_y_range * 0.06],
        "label": [f"Selected: {start_label} – {end_label}"],
    }
)

# Navigator selection rectangle (highlights the visible range)
selection_rect = pd.DataFrame({"xmin": [select_xmin], "xmax": [select_xmax], "ymin": [nav_y_min], "ymax": [nav_y_max]})

# Tooltips for main chart
main_tooltips = (
    layer_tooltips()
    .title("Temperature Reading")
    .line("Date: @date")
    .line("Temp: @{temperature}°C")
    .format("temperature", ".1f")
)

# Shared theme settings
main_theme = theme_minimal() + theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    panel_grid_major=element_line(color=RULE, size=0.5),
    panel_grid_minor=element_blank(),
    axis_line=element_line(color=INK_SOFT),
)

nav_theme = theme_minimal() + theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    panel_grid_major=element_line(color=RULE_FAINT, size=0.3),
    panel_grid_minor=element_blank(),
    axis_line=element_line(color=INK_SOFT),
)

# Main chart — detailed view of the selected range
main_chart = (
    ggplot(df_selected, aes(x="date", y="temperature"))
    + geom_area(fill=BRAND, alpha=0.15)
    + geom_line(color=BRAND, size=1.5, tooltips=main_tooltips)
    + geom_text(
        aes(x="x", y="y", label="label"), data=range_label_df, inherit_aes=False, size=3.5, color=BRAND, fontface="bold"
    )
    + labs(x="", y="Temperature (°C)")
    + scale_x_datetime(format="%b %Y")
    + scale_y_continuous(limits=[main_y_lower, main_y_upper])
    + main_theme
    + ggsize(800, 360)
)

# Navigator mini chart — full data overview with selection window
navigator = (
    ggplot(df_full, aes(x="date", y="temperature"))
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=selection_rect,
        inherit_aes=False,
        fill=BRAND,
        alpha=0.2,
        color=BRAND,
        linetype="solid",
        size=2.5,
    )
    + geom_area(fill=BRAND, alpha=0.12, tooltips="none")
    + geom_line(color=BRAND, size=0.8, tooltips="none")
    + labs(x="Date", y="")
    + scale_x_datetime(format="%Y")
    + scale_y_continuous(limits=[nav_y_min, nav_y_max])
    + nav_theme
    + ggsize(800, 90)
)

# Combine main chart and navigator — navigator is ~18% of main chart height
combined = gggrid([main_chart, navigator], ncol=1, heights=[5.5, 1], align=True)

title = "line-navigator · python · letsplot · anyplot.ai"
combined = (
    combined
    + ggtitle(title)
    + ggsize(800, 450)
    + theme(
        plot_title=element_text(size=16, color=INK, face="bold"),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

# Save PNG (scale 4x → 3200 × 1800 px) and interactive HTML
ggsave(combined, f"plot-{THEME}.png", path=".", scale=4)
ggsave(combined, f"plot-{THEME}.html", path=".")
