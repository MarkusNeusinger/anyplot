"""anyplot.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: plotnine 0.15.5 | Python 3.13.13
Quality: 89/100 | Updated: 2026-06-09
"""

import os
import sys


# This file is named after the library it imports — remove its directory from
# sys.path so Python finds the installed plotnine package, not this script.
_here = os.path.dirname(os.path.abspath(__file__))
if sys.path and os.path.abspath(sys.path[0]) == _here:
    sys.path.pop(0)

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    arrow,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
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


# Theme-adaptive chrome tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential gradient: brand green → blue (temporal progression low→high)
SEQ_LOW = "#009E73"
SEQ_HIGH = "#4467A3"
RECESSION_COLOR = "#AE3030"  # Imprint matte red — semantic bad/crisis anchor

# Data: US unemployment rate vs inflation rate (Phillips curve), 1990-2020
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

# Four well-separated key years to anchor temporal reading (avoids central congestion)
label_config = {1990: (-0.42, 0.55), 2000: (0.32, 0.55), 2010: (0.42, -0.60), 2020: (0.42, 0.55)}

label_rows = []
for yr, (dx, dy) in label_config.items():
    row = df[df["Year"] == yr].iloc[0]
    label_rows.append({"x_label": row["Unemployment"] + dx, "y_label": row["Inflation"] + dy, "Label": str(yr)})
df_labels = pd.DataFrame(label_rows)

recession_point = df[df["Year"] == 2009].copy()

# Directional arrow segments at inflection points to reinforce temporal flow
arrow_years = [1992, 1997, 2011, 2017]
arrow_rows = []
for yr in arrow_years:
    r1 = df[df["Year"] == yr].iloc[0]
    r2 = df[df["Year"] == yr + 1].iloc[0]
    arrow_rows.append(
        {
            "x": r1["Unemployment"],
            "y": r1["Inflation"],
            "xend": r2["Unemployment"],
            "yend": r2["Inflation"],
            "Year_num": r1["Year_num"],
        }
    )
df_arrows = pd.DataFrame(arrow_rows)

# Plot — geom_path preserves temporal ordering (not geom_line which sorts by x)
plot = (
    ggplot(df, aes(x="Unemployment", y="Inflation"))
    + geom_path(aes(color="Year_num"), size=1.2)
    + geom_segment(
        data=df_arrows,
        mapping=aes(x="x", y="y", xend="xend", yend="yend", color="Year_num"),
        arrow=arrow(length=0.1, type="open"),
        show_legend=False,
        size=1.2,
    )
    + geom_point(aes(fill="Year_num"), size=4.0, color=PAGE_BG, stroke=0.6, show_legend=False)
    + geom_point(
        data=recession_point,
        mapping=aes(x="Unemployment", y="Inflation"),
        size=7.5,
        color=RECESSION_COLOR,
        fill="none",
        stroke=1.8,
    )
    + annotate(
        "text",
        x=recession_point["Unemployment"].values[0] - 0.9,
        y=recession_point["Inflation"].values[0] + 0.75,
        label="2009 Recession",
        size=3.5,
        fontweight="bold",
        color=RECESSION_COLOR,
    )
    + geom_text(
        aes(x="x_label", y="y_label", label="Label"),
        data=df_labels,
        size=3.5,
        fontweight="bold",
        color=INK_SOFT,
        inherit_aes=False,
    )
    + scale_color_gradient(
        low=SEQ_LOW, high=SEQ_HIGH, name="Year", breaks=[0, 10, 20, 30], labels=["1990", "2000", "2010", "2020"]
    )
    + scale_fill_gradient(low=SEQ_LOW, high=SEQ_HIGH)
    + scale_x_continuous(breaks=range(3, 11), expand=(0.05, 0.3))
    + scale_y_continuous(breaks=range(-1, 7), expand=(0.05, 0.3))
    + labs(
        x="Unemployment Rate (%)",
        y="Inflation Rate (%)",
        title="scatter-connected-temporal · python · plotnine · anyplot.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, fontweight="bold", color=INK),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_line=element_blank(),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
