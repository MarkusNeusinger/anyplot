"""anyplot.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: plotnine | Python 3.13
Quality: pending | Updated: 2026-04-30
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
    geom_rect,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data - Stock prices over 10 years with highlighted periods
np.random.seed(42)
years = np.linspace(2006, 2016, 100)
price = 100 + np.cumsum(np.random.randn(100) * 2)
recession_mask = (years >= 2008) & (years < 2010)
price[recession_mask] -= np.linspace(0, 25, recession_mask.sum())
price[years >= 2010] -= 25
price = price + np.abs(price.min()) + 50

df = pd.DataFrame({"year": years, "price": price})

y_min = df["price"].min() - 5
y_max = df["price"].max() + 5
x_min = years.min()
x_max = years.max()

spans = pd.DataFrame(
    {
        "xmin": [2008, x_min],
        "xmax": [2009, x_max],
        "ymin": [y_min, 60],
        "ymax": [y_max, 80],
        "label": ["Recession Period", "Risk Zone"],
    }
)

# Plot
plot = (
    ggplot()
    + geom_rect(data=spans, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="label"), alpha=0.25)
    + geom_line(data=df, mapping=aes(x="year", y="price"), color=OKABE_ITO[0], size=1.5)
    + scale_fill_manual(values={"Recession Period": OKABE_ITO[1], "Risk Zone": OKABE_ITO[4]}, name="Highlighted Region")
    + labs(x="Year", y="Price ($)", title="span-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=24, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
