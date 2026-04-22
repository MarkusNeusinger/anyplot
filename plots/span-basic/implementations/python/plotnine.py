""" pyplots.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_line,
    geom_rect,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Stock prices over 10 years with highlighted periods
np.random.seed(42)
years = np.linspace(2006, 2016, 100)
# Simulate stock price with random walk
price = 100 + np.cumsum(np.random.randn(100) * 2)
# Add dip during recession period (2008-2009)
recession_mask = (years >= 2008) & (years < 2010)
price[recession_mask] -= np.linspace(0, 25, recession_mask.sum())
price[years >= 2010] -= 25
price = price + np.abs(price.min()) + 50  # Keep positive

df = pd.DataFrame({"year": years, "price": price})

# Get axis limits for span regions
y_min = df["price"].min() - 5
y_max = df["price"].max() + 5
x_min = years.min()
x_max = years.max()

# Span regions data
# Vertical span: recession period (2008-2009)
# Horizontal span: risk zone (price 60-80)
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
    # Span regions (drawn first so line is on top)
    + geom_rect(data=spans, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="label"), alpha=0.25)
    # Line chart
    + geom_line(data=df, mapping=aes(x="year", y="price"), color="#306998", size=1.5)
    # Colors for spans
    + scale_fill_manual(values={"Recession Period": "#FFD43B", "Risk Zone": "#D62728"}, name="Highlighted Region")
    + labs(x="Year", y="Price ($)", title="span-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
