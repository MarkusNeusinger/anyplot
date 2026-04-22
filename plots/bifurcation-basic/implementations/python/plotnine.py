""" pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bin2d,
    geom_segment,
    ggplot,
    guides,
    labs,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — logistic map: x(n+1) = r * x(n) * (1 - x(n))
r_values = np.linspace(2.5, 4.0, 3000)
n_discard = 200
n_keep = 100

parameter = []
state = []

x0 = 0.5
for r in r_values:
    x = x0
    for _ in range(n_discard):
        x = r * x * (1.0 - x)
    for _ in range(n_keep):
        x = r * x * (1.0 - x)
        parameter.append(r)
        state.append(x)

df = pd.DataFrame({"parameter": parameter, "state": state})

# Key bifurcation points
bifurcation_r = [3.0, 3.449, 3.544]

# Plot — uses geom_bin2d (2D histogram) for density-based visualization,
# a distinctive plotnine/ggplot2 feature that naturally reveals structure
plot = (
    ggplot(df, aes(x="parameter", y="state"))
    + geom_bin2d(bins=(250, 150), na_rm=True)
    + scale_fill_gradientn(
        colors=["#0d1117", "#306998", "#4a8db7", "#e3a835", "#f5d576", "#fffbe6"], values=[0, 0.1, 0.3, 0.6, 0.85, 1.0]
    )
    + geom_segment(
        aes(x="x", xend="x", y="y", yend="yend"),
        data=pd.DataFrame({"x": bifurcation_r, "y": [0.0] * 3, "yend": [1.0] * 3}),
        linetype="dashed",
        color="#c44e52",
        alpha=0.7,
        size=0.6,
    )
    + annotate(
        "text", x=2.98, y=0.92, label="Period-2\nr ≈ 3.0", size=12, color="#c44e52", ha="right", fontweight="bold"
    )
    + annotate(
        "text", x=3.44, y=0.92, label="Period-4\nr ≈ 3.449", size=12, color="#c44e52", ha="right", fontweight="bold"
    )
    + annotate(
        "text", x=3.56, y=0.08, label="Period-8\nr ≈ 3.544", size=12, color="#c44e52", ha="left", fontweight="bold"
    )
    + annotate(
        "label", x=3.82, y=0.15, label="Chaos", size=12, color="#e3a835", fontweight="bold", fill="#ffffff", alpha=0.85
    )
    + annotate(
        "label",
        x=2.7,
        y=0.72,
        label="Stable\nFixed Point",
        size=12,
        color="#306998",
        fontweight="bold",
        fill="#ffffff",
        alpha=0.85,
    )
    + labs(x="Growth Rate (r)", y="Steady-State Population (x)", title="bifurcation-basic · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=np.arange(2.5, 4.1, 0.25))
    + scale_y_continuous(breaks=np.arange(0, 1.1, 0.2))
    + coord_cartesian(xlim=(2.5, 4.0), ylim=(0, 1.0))
    + guides(fill=False)
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#2d2d2d"),
        axis_title=element_text(size=20, color="#444444"),
        axis_text=element_text(size=16, color="#666666"),
        panel_grid_major=element_line(color="#2a2a4e", size=0.3),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="#fafafa", color="none"),
        panel_background=element_rect(fill="#0d1117", color="none"),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
