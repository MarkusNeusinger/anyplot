""" pyplots.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_bar,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data: Energy source mix by country (renewable adoption comparison)
data = {
    "country": ["Germany"] * 5 + ["France"] * 5 + ["UK"] * 5 + ["Spain"] * 5 + ["Italy"] * 5 + ["Poland"] * 5,
    "source": ["Coal", "Natural Gas", "Nuclear", "Renewables", "Other"] * 6,
    "value": [
        # Germany
        26,
        15,
        6,
        46,
        7,
        # France
        2,
        7,
        68,
        21,
        2,
        # UK
        5,
        38,
        15,
        39,
        3,
        # Spain
        3,
        22,
        21,
        50,
        4,
        # Italy
        6,
        42,
        0,
        45,
        7,
        # Poland
        68,
        10,
        0,
        17,
        5,
    ],
}

df = pd.DataFrame(data)

# Set category order for proper stacking
df["country"] = pd.Categorical(
    df["country"], categories=["Germany", "France", "UK", "Spain", "Italy", "Poland"], ordered=True
)
df["source"] = pd.Categorical(
    df["source"], categories=["Coal", "Natural Gas", "Nuclear", "Renewables", "Other"], ordered=True
)

# Colors for energy sources (colorblind-safe palette)
colors = ["#4A4A4A", "#306998", "#9467BD", "#2ECC71", "#95A5A6"]

# Create 100% stacked bar chart with position="fill"
plot = (
    ggplot(df, aes(x="country", y="value", fill="source"))
    + geom_bar(stat="identity", position="fill", width=0.75, alpha=0.9)
    + scale_fill_manual(values=colors)
    + scale_y_continuous(format=".0%")
    + labs(
        title="bar-stacked-percent · letsplot · pyplots.ai", x="Country", y="Share of Energy Mix", fill="Energy Source"
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        legend_title=element_text(size=20),
        legend_text=element_text(size=18),
        legend_position="right",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML (interactive)
ggsave(plot, "plot.html", path=".")
