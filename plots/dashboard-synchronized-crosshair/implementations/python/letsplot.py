""" anyplot.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-23
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
    geom_hline,
    geom_line,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    gggrid,
    ggplot,
    ggsize,
    ggtitle,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "#E1DFD9" if THEME == "light" else "#32322F"

ANYPLOT_PALETTE = ["#009E73", "#9418DB", "#B71D27", "#16B8F3", "#99B314", "#D359A7", "#BA843E"]
CROSSHAIR_COLOR = ANYPLOT_PALETTE[5]  # #D359A7 pink — visually distinct from all 3 series

# Data — stock dashboard: price, volume, RSI over 200 trading days
np.random.seed(42)
n_points = 200

dates = pd.date_range("2024-01-01", periods=n_points, freq="B")
returns = np.random.normal(0.001, 0.02, n_points)
price = 100 * np.cumprod(1 + returns)
base_volume = 1_000_000
volume = base_volume * (1 + 2 * np.abs(returns)) * np.random.uniform(0.8, 1.2, n_points)
rsi = 50 + 20 * np.sin(np.linspace(0, 8 * np.pi, n_points)) + np.random.normal(0, 5, n_points)
rsi = np.clip(rsi, 0, 100)

df = pd.DataFrame({"date": dates, "price": price, "volume": volume / 1e6, "rsi": rsi, "zero": 0.0})

# Crosshair position at index 100 (mid-point)
crosshair_idx = 100
crosshair_date = df["date"].iloc[crosshair_idx]
crosshair_price = df["price"].iloc[crosshair_idx]
crosshair_volume = df["volume"].iloc[crosshair_idx]
crosshair_rsi = df["rsi"].iloc[crosshair_idx]

# Annotation data for each chart
crosshair_price_df = pd.DataFrame(
    {"date": [crosshair_date], "price": [crosshair_price], "label": [f"${crosshair_price:.2f}"]}
)
crosshair_volume_df = pd.DataFrame(
    {"date": [crosshair_date], "volume": [crosshair_volume], "label": [f"{crosshair_volume:.2f}M"]}
)
crosshair_rsi_df = pd.DataFrame({"date": [crosshair_date], "rsi": [crosshair_rsi], "label": [f"{crosshair_rsi:.1f}"]})

# Vertical crosshair line data (geom_path needs two points per line)
vline_price_df = pd.DataFrame(
    {
        "date": [crosshair_date, crosshair_date],
        "y": [df["price"].min() * 0.98, df["price"].max() * 1.02],
        "series": ["Crosshair", "Crosshair"],
    }
)
vline_volume_df = pd.DataFrame(
    {
        "date": [crosshair_date, crosshair_date],
        "y": [0.0, df["volume"].max() * 1.1],
        "series": ["Crosshair", "Crosshair"],
    }
)
vline_rsi_df = pd.DataFrame(
    {"date": [crosshair_date, crosshair_date], "y": [0.0, 100.0], "series": ["Crosshair", "Crosshair"]}
)

# Shared theme for all sub-charts
common_theme = theme(
    axis_title=element_text(size=18, color=INK),
    axis_text=element_text(size=14, color=INK_SOFT),
    plot_title=element_text(size=20, color=INK),
    legend_text=element_text(size=14, color=INK_SOFT),
    legend_title=element_text(size=14, color=INK),
    axis_line=element_line(color=INK_SOFT, size=1),
    panel_grid_major=element_line(color=GRID_COLOR, size=0.4),
    panel_grid_minor=element_blank(),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
)

# Chart 1: Price
price_chart = (
    ggplot(df, aes(x="date", y="price"))
    + geom_line(color=ANYPLOT_PALETTE[0], size=1.5, tooltips=layer_tooltips().line("@date").line("Price|$@price"))
    + geom_path(data=vline_price_df, mapping=aes(x="date", y="y", color="series"), size=1.2, alpha=0.85)
    + geom_point(data=crosshair_price_df, mapping=aes(x="date", y="price"), color=CROSSHAIR_COLOR, size=6)
    + geom_text(
        data=crosshair_price_df,
        mapping=aes(x="date", y="price", label="label"),
        hjust=-0.15,
        vjust=0.5,
        color=CROSSHAIR_COLOR,
        size=12,
    )
    + scale_color_manual(values={"Crosshair": CROSSHAIR_COLOR}, name="")
    + labs(x="", y="Price ($)", title="Price")
    + theme_minimal()
    + common_theme
)

# Chart 2: Volume — geom_segment renders color= reliably vs geom_bar fill= quirk
volume_chart = (
    ggplot(df, aes(x="date", xend="date", y="zero", yend="volume"))
    + geom_segment(
        color=ANYPLOT_PALETTE[1], size=2.0, alpha=0.85, tooltips=layer_tooltips().line("@date").line("Volume|@volume M")
    )
    + geom_path(data=vline_volume_df, mapping=aes(x="date", y="y", color="series"), size=1.2, alpha=0.85)
    + geom_point(data=crosshair_volume_df, mapping=aes(x="date", y="volume"), color=CROSSHAIR_COLOR, size=6)
    + geom_text(
        data=crosshair_volume_df,
        mapping=aes(x="date", y="volume", label="label"),
        hjust=-0.15,
        vjust=0.5,
        color=CROSSHAIR_COLOR,
        size=12,
    )
    + scale_color_manual(values={"Crosshair": CROSSHAIR_COLOR}, name="")
    + labs(x="", y="Volume (M)", title="Volume")
    + theme_minimal()
    + common_theme
)

# Chart 3: RSI Indicator
rsi_chart = (
    ggplot(df, aes(x="date", y="rsi"))
    + geom_line(color=ANYPLOT_PALETTE[2], size=1.5, tooltips=layer_tooltips().line("@date").line("RSI|@rsi"))
    + geom_hline(yintercept=70, linetype="dashed", color=INK_SOFT, size=0.8)
    + geom_hline(yintercept=30, linetype="dashed", color=INK_SOFT, size=0.8)
    + geom_path(data=vline_rsi_df, mapping=aes(x="date", y="y", color="series"), size=1.2, alpha=0.85)
    + geom_point(data=crosshair_rsi_df, mapping=aes(x="date", y="rsi"), color=CROSSHAIR_COLOR, size=6)
    + geom_text(
        data=crosshair_rsi_df,
        mapping=aes(x="date", y="rsi", label="label"),
        hjust=-0.15,
        vjust=0.5,
        color=CROSSHAIR_COLOR,
        size=12,
    )
    + scale_color_manual(values={"Crosshair": CROSSHAIR_COLOR}, name="")
    + scale_y_continuous(limits=[0, 100])
    + labs(x="Date", y="RSI", title="RSI Indicator")
    + theme_minimal()
    + common_theme
)

# Combine into stacked dashboard with 2:1:1 height ratio
TITLE = "dashboard-synchronized-crosshair · python · letsplot · anyplot.ai"
n = len(TITLE)
title_fontsize = round(16 * (67 / n)) if n > 67 else 16

combined = (
    gggrid([price_chart, volume_chart, rsi_chart], ncol=1, heights=[2, 1, 1])
    + ggsize(800, 450)
    + ggtitle(TITLE)
    + theme(
        plot_title=element_text(size=title_fontsize, color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

# Save PNG (scale=4 → 3200×1800 px) and HTML
ggsave(combined, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(combined, filename=f"plot-{THEME}.html", path=".")
