"""anyplot.ai
line-timeseries: Time Series Line Plot
Library: plotnine | Python 3.13
Quality: 92/100 | Updated: 2025-05-09
"""

import os

import numpy as np
import pandas as pd
from mizani.breaks import breaks_date
from mizani.labels import label_date
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_x_datetime,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data: Bitcoin prices over one year with explicit trend and volatility
np.random.seed(42)
dates = pd.date_range(start="2023-01-01", periods=365, freq="D")
price = 16500.0
prices = []
for i in range(365):
    # Trend component: upward over the year, with mid-year dip
    trend = 20000 + 15000 * np.sin(i / 365 * np.pi * 2) + i * 5
    # Volatility: crypto is more volatile than stocks
    volatility = price * (1 + np.random.randn() * 0.035)
    # Mix trend and volatility
    price = 0.7 * trend + 0.3 * volatility
    prices.append(price)

df = pd.DataFrame({"date": dates, "price": prices})

# Plot
plot = (
    ggplot(df, aes(x="date", y="price"))
    + geom_line(color=BRAND, size=1.5, alpha=0.9)
    + geom_point(color=BRAND, size=0.8, alpha=0.5)
    + scale_x_datetime(breaks=breaks_date(30), labels=label_date("%b"))
    + labs(title="line-timeseries · plotnine · anyplot.ai", x="Date", y="Bitcoin Price (USD)")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        text=element_text(size=14, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_text_x=element_text(angle=45, hjust=1),
        plot_title=element_text(size=24, color=INK),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
