""" anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 82/100 | Created: 2026-05-16
"""

import os
import sys


# Workaround for import conflict when script name matches package name
sys.path = [p for p in sys.path if not p.endswith("implementations/python")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    element_line,
    element_rect,
    element_text,
    geom_col,
    geom_hline,
    geom_line,
    ggplot,
    ggsave,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"
OCHRE = "#BD8233"  # imprint ochre - categorical contrast against BRAND green
BLUE = "#4467A3"
RED = "#D62728"
GREEN = "#2CA02C"

np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=150, freq="D")
prices = 100 + np.cumsum(np.random.randn(150) * 1.5)

df_prices = pd.DataFrame({"date": dates, "close": prices})

df_prices["ema_12"] = df_prices["close"].ewm(span=12, adjust=False).mean()
df_prices["ema_26"] = df_prices["close"].ewm(span=26, adjust=False).mean()
df_prices["macd"] = df_prices["ema_12"] - df_prices["ema_26"]
df_prices["signal"] = df_prices["macd"].ewm(span=9, adjust=False).mean()
df_prices["histogram"] = df_prices["macd"] - df_prices["signal"]

df_plot = df_prices[["date", "macd", "signal", "histogram"]].copy()
df_plot["histogram_color"] = df_plot["histogram"].apply(lambda x: "positive" if x >= 0 else "negative")

df_lines = pd.DataFrame(
    {
        "date": list(df_plot["date"]) * 2,
        "value": list(df_plot["macd"]) + list(df_plot["signal"]),
        "line": ["MACD"] * len(df_plot) + ["Signal"] * len(df_plot),
    }
)

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24, weight="medium"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=16),
)

color_map = {"MACD": BLUE, "Signal": OCHRE}
fill_map = {"positive": GREEN, "negative": RED}

plot = (
    ggplot(df_plot, aes(x="date"))
    + geom_col(aes(y="histogram", fill="histogram_color"), alpha=0.7, show_legend=False)
    + geom_line(data=df_lines, mapping=aes(x="date", y="value", color="line"), size=1.2)
    + geom_hline(yintercept=0, color=INK_SOFT, linetype="solid", size=0.5, alpha=0.5)
    + labs(x="Date", y="Value", title="indicator-macd · plotnine · anyplot.ai", color="Line")
    + scale_color_manual(values=color_map)
    + scale_fill_manual(values=fill_map)
    + anyplot_theme
    + theme(figure_size=(16, 9), legend_position=(0.15, 0.85))
)

ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=16, height=9)
