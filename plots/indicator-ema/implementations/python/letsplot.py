""" anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-19
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito colors for Close Price, EMA 12, EMA 26
COLORS = {"Close Price": "#009E73", "EMA 12": "#D55E00", "EMA 26": "#0072B2"}

# Data
np.random.seed(42)
dates = pd.date_range("2024-01-02", periods=120, freq="B")
returns = np.random.normal(0.001, 0.015, 120)
price = 100 * np.cumprod(1 + returns)

price_series = pd.Series(price)
ema_12 = price_series.ewm(span=12, adjust=False).mean().values
ema_26 = price_series.ewm(span=26, adjust=False).mean().values

df = pd.DataFrame({"date_num": range(120), "close": price, "ema_12": ema_12, "ema_26": ema_26})

df_price = df[["date_num", "close"]].rename(columns={"close": "value"}).copy()
df_price["series"] = "Close Price"

df_ema12 = df[["date_num", "ema_12"]].rename(columns={"ema_12": "value"}).copy()
df_ema12["series"] = "EMA 12"

df_ema26 = df[["date_num", "ema_26"]].rename(columns={"ema_26": "value"}).copy()
df_ema26["series"] = "EMA 26"

df_ema_only = pd.concat([df_ema12, df_ema26], ignore_index=True)

date_labels = {i: dates[i].strftime("%b %d") for i in range(0, 120, 20)}

# Theme — separate geom_line calls avoid duplicate color+size legend (VQ-07 fix)
anyplot_theme = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
    panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
    panel_grid_major=element_line(color=RULE, size=0.5),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
    axis_title=element_text(size=20, color=INK),  # noqa: F405
    axis_text=element_text(size=16, color=INK_SOFT),  # noqa: F405
    axis_line=element_line(color=INK_SOFT),  # noqa: F405
    plot_title=element_text(size=24, color=INK),  # noqa: F405
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
    legend_text=element_text(size=16, color=INK_SOFT),  # noqa: F405
    legend_title=element_text(size=18, color=INK),  # noqa: F405
    legend_position="right",
)

# Plot — price line thicker; EMA lines thinner; single color legend only
plot = (
    ggplot(mapping=aes(x="date_num", y="value", color="series"))  # noqa: F405
    + geom_line(data=df_price, size=2.5, alpha=0.85)  # noqa: F405
    + geom_line(data=df_ema_only, size=1.5)  # noqa: F405
    + scale_color_manual(values=COLORS, name="Series")  # noqa: F405
    + scale_x_continuous(  # noqa: F405
        breaks=list(date_labels.keys()), labels=list(date_labels.values())
    )
    + labs(  # noqa: F405
        x="Date", y="Price (USD)", title="indicator-ema · python · letsplot · anyplot.ai"
    )
    + theme_minimal()  # noqa: F405
    + anyplot_theme
    + ggsize(1600, 900)  # noqa: F405
)

# Save
export_ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
export_ggsave(plot, f"plot-{THEME}.html", path=".")
