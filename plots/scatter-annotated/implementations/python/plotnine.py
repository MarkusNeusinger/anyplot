""" pyplots.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_text,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Company performance metrics (fewer points to avoid label overlap)
np.random.seed(42)

companies = [
    "TechCorp",
    "DataFlow",
    "CloudNet",
    "AI Labs",
    "InfoSys",
    "AppWorks",
    "SoftCore",
    "CodeBase",
    "SmartSys",
    "WebDev",
]

# Revenue (millions) and Profit Margin (percentage) - spread out to avoid overlap
revenue = np.array([35, 95, 140, 200, 65, 170, 110, 55, 125, 80])
profit_margin = np.array([6, 12, 18, 23, 9, 20, 15, 8, 16, 11])

# Add small variation
revenue = revenue + np.random.uniform(-3, 3, len(companies))
profit_margin = profit_margin + np.random.uniform(-0.5, 0.5, len(companies))

df = pd.DataFrame({"company": companies, "revenue": revenue, "profit_margin": profit_margin})

# Create plot
plot = (
    ggplot(df, aes(x="revenue", y="profit_margin"))
    + geom_point(size=6, alpha=0.7, color="#306998")
    + geom_text(aes(label="company"), size=11, nudge_y=0.9, color="#333333", va="bottom")
    + labs(x="Annual Revenue ($ Millions)", y="Profit Margin (%)", title="scatter-annotated · plotnine · pyplots.ai")
    + scale_x_continuous(limits=(20, 220))
    + scale_y_continuous(limits=(4, 26))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
