"""pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-13
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_color_gradient,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


# Data - US unemployment rate vs inflation rate (stylized Phillips curve), 1990-2020
np.random.seed(42)
years = np.arange(1990, 2021)
n = len(years)

unemployment = np.array(
    [
        5.6,
        6.8,
        7.5,
        6.9,
        6.1,
        5.6,
        5.4,
        4.9,
        4.5,
        4.2,
        4.0,
        4.7,
        5.8,
        6.0,
        5.5,
        5.1,
        4.6,
        4.6,
        5.8,
        9.3,
        9.6,
        8.9,
        8.1,
        7.4,
        6.2,
        5.3,
        4.9,
        4.4,
        3.9,
        3.7,
        8.1,
    ]
)
inflation = np.array(
    [
        5.4,
        4.2,
        3.0,
        3.0,
        2.6,
        2.8,
        3.0,
        2.3,
        1.6,
        2.2,
        3.4,
        2.8,
        1.6,
        2.3,
        2.7,
        3.4,
        3.2,
        2.8,
        3.8,
        -0.4,
        1.6,
        3.2,
        2.1,
        1.5,
        1.6,
        0.1,
        1.3,
        2.1,
        2.4,
        1.8,
        1.2,
    ]
)

df = pd.DataFrame(
    {"Unemployment": unemployment, "Inflation": inflation, "Year": years, "Year_num": np.arange(n, dtype=float)}
)

label_years = [1990, 1995, 2000, 2005, 2009, 2015, 2020]
df_labels = df[df["Year"].isin(label_years)].copy()
df_labels["Label"] = df_labels["Year"].astype(str)

# Plot
plot = (
    ggplot(df, aes(x="Unemployment", y="Inflation"))
    + geom_line(aes(color="Year_num"), size=1.2, show_legend=False)
    + geom_point(aes(fill="Year_num"), size=5, color="white", stroke=0.8, show_legend=False)
    + geom_text(aes(label="Label"), data=df_labels, size=12, nudge_y=0.45, fontweight="bold", color="#333333")
    + scale_color_gradient(low="#a8c4e0", high="#1a3a5c")
    + scale_fill_gradient(low="#a8c4e0", high="#1a3a5c")
    + labs(
        x="Unemployment Rate (%)",
        y="Inflation Rate (%)",
        title="Phillips Curve Dynamics (1990-2020) · scatter-connected-temporal · plotnine · pyplots.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=20, fontweight="bold"),
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.2),
        panel_grid_minor=element_blank(),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
