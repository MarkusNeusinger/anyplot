""" pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-13
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_text,
    geom_path,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_color_gradient,
    scale_fill_gradient,
    scale_x_continuous,
    scale_y_continuous,
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

# Labels with custom offsets to avoid crowding
label_config = {
    1990: (0.25, 0.45),
    1995: (-0.35, -0.45),
    2000: (0.25, 0.45),
    2005: (0.3, -0.45),
    2015: (-0.3, -0.45),
    2020: (0.35, 0.45),
}

label_rows = []
for yr, (dx, dy) in label_config.items():
    row = df[df["Year"] == yr].iloc[0]
    label_rows.append({"x_label": row["Unemployment"] + dx, "y_label": row["Inflation"] + dy, "Label": str(yr)})
df_labels = pd.DataFrame(label_rows)

# Highlight the 2008-2009 recession (peak unemployment)
recession_point = df[df["Year"] == 2009].copy()

# Plot - using geom_path for correct temporal ordering (not geom_line which sorts by x)
plot = (
    ggplot(df, aes(x="Unemployment", y="Inflation"))
    + geom_path(aes(color="Year_num"), size=1.2)
    + geom_point(aes(fill="Year_num"), size=4.5, color="white", stroke=0.8, show_legend=False)
    # Highlight recession peak with a larger red-outlined marker
    + geom_point(
        data=recession_point,
        mapping=aes(x="Unemployment", y="Inflation"),
        size=8,
        color="#c0392b",
        fill="none",
        stroke=1.5,
    )
    + annotate(
        "text",
        x=recession_point["Unemployment"].values[0] - 0.6,
        y=recession_point["Inflation"].values[0] + 0.5,
        label="2009 Recession",
        size=13,
        fontweight="bold",
        color="#c0392b",
    )
    # Year labels (positioned with per-label offsets)
    + geom_text(
        aes(x="x_label", y="y_label", label="Label"),
        data=df_labels,
        size=13,
        fontweight="bold",
        color="#444444",
        inherit_aes=False,
    )
    + scale_color_gradient(
        low="#6a9bc5", high="#1a3a5c", name="Year", breaks=[0, 10, 20, 30], labels=["1990", "2000", "2010", "2020"]
    )
    + scale_fill_gradient(low="#6a9bc5", high="#1a3a5c")
    + scale_x_continuous(breaks=range(3, 11), expand=(0.05, 0.3))
    + scale_y_continuous(breaks=range(-1, 7), expand=(0.05, 0.3))
    + labs(
        x="Unemployment Rate (%)",
        y="Inflation Rate (%)",
        title="Phillips Curve (1990\u20132020) \u00b7 scatter-connected-temporal \u00b7 plotnine \u00b7 pyplots.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, fontweight="bold"),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.2),
        panel_grid_minor=element_blank(),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
