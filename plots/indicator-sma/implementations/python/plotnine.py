"""anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: plotnine | Python 3.13
Quality: 91/100 | Updated: 2026-05-19
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - stock price with exponential-decay trend (strong early momentum fading to mild reversion)
np.random.seed(42)
n_days = 300
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")

base_price = 150
returns = np.random.normal(0.0003, 0.015, n_days)
trend = np.exp(-np.linspace(0, 2, n_days)) * 0.003 - 0.0005
returns = returns + trend
close = base_price * np.cumprod(1 + returns)

# Calculate SMAs
df = pd.DataFrame({"date": dates, "close": close})
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Reshape to long format for plotnine
df_long = pd.melt(
    df, id_vars=["date"], value_vars=["close", "sma_20", "sma_50", "sma_200"], var_name="series", value_name="price"
)

series_labels = {"close": "Price", "sma_20": "SMA 20", "sma_50": "SMA 50", "sma_200": "SMA 200"}
df_long["series"] = df_long["series"].map(series_labels)

series_order = ["Price", "SMA 20", "SMA 50", "SMA 200"]
df_long["series"] = pd.Categorical(df_long["series"], categories=series_order, ordered=True)

colors = {"Price": OKABE_ITO[0], "SMA 20": OKABE_ITO[1], "SMA 50": OKABE_ITO[2], "SMA 200": OKABE_ITO[3]}

# Plot
plot = (
    ggplot(df_long, aes(x="date", y="price", color="series"))
    + geom_line(size=1.5, alpha=0.9)
    + scale_color_manual(values=colors)
    + scale_x_datetime(date_breaks="2 months", date_labels="%b %Y")
    + labs(x="Date", y="Price ($)", title="indicator-sma · python · plotnine · anyplot.ai", color="")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=24, weight="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_text_x=element_text(size=16, rotation=30, ha="right", color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_position=(0.02, 0.98),
        legend_direction="vertical",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_major_x=element_line(alpha=0),
        panel_grid_minor=element_line(alpha=0),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
