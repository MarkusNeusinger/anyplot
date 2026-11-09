"""anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: plotnine 0.15.8 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_ribbon,
    ggplot,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_size_manual,
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

# Imprint palette: price first, then one position per EMA
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
EMA_SPANS = [12, 26]  # short and long EMA periods
SERIES = "Series"
VALUE = "Value"
SIGNAL = "Signal"
PRICE_WIDTH = 1.0
EMA_WIDTH = 0.6

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price (USD)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 120
returns = np.random.normal(0.0008, 0.018, n_days)
df = pd.DataFrame(
    {DATE: pd.date_range(start="2024-01-02", periods=n_days, freq="B"), CLOSE: 150.0 * np.cumprod(1 + returns)}
)

# Plot: reads only df and the constants above
ema_labels = [f"EMA-{span}" for span in EMA_SPANS]
wide = df.copy()
for span, label in zip(EMA_SPANS, ema_labels, strict=True):
    wide[label] = wide[CLOSE].ewm(span=span, adjust=False).mean()
short_label, long_label = ema_labels[0], ema_labels[-1]

series_order = [CLOSE, *ema_labels]
long = wide.melt(id_vars=DATE, value_vars=series_order, var_name=SERIES, value_name=VALUE)

# Crossovers: dates where the short EMA changes side of the long EMA
crossover_indices = np.flatnonzero(np.diff(np.sign(wide[short_label] - wide[long_label])) != 0) + 1
crossovers = wide.iloc[crossover_indices].assign(**{SIGNAL: "EMA crossover"})

plot = (
    ggplot(long, aes(x=DATE, y=VALUE, color=SERIES, size=SERIES))
    + geom_ribbon(
        wide, aes(x=DATE, ymin=short_label, ymax=long_label), fill=IMPRINT_PALETTE[2], alpha=0.12, inherit_aes=False
    )
    + geom_line(alpha=0.95)
    + geom_point(
        crossovers, aes(x=DATE, y=short_label, fill=SIGNAL), color=PAGE_BG, size=2.6, stroke=0.4, inherit_aes=False
    )
    + scale_color_manual(values=IMPRINT_PALETTE, limits=series_order)
    + scale_size_manual(values=[PRICE_WIDTH] + [EMA_WIDTH] * len(ema_labels), limits=series_order)
    + scale_fill_manual(values=[IMPRINT_PALETTE[3]])
    + guides(size=None)
    + scale_x_datetime(date_breaks="1 month", date_labels="%b %Y")
    + labs(title="indicator-ema · python · plotnine · anyplot.ai", x=DATE, y=CLOSE)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=12, weight="bold", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
