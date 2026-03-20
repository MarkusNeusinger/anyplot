"""pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_vline,
    ggplot,
    labs,
    scale_color_gradient,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — logistic map: x(n+1) = r * x(n) * (1 - x(n))
r_values = np.linspace(2.5, 4.0, 2000)
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

# Compute number of unique steady states per r-value to encode regime as color
unique_counts = df.groupby("parameter")["state"].transform("nunique")
df["regime"] = unique_counts.clip(upper=20).astype(float)

# Key bifurcation points
bifurcation_r = [3.0, 3.449, 3.544]
bifurcation_labels = ["Period-2\nr ≈ 3.0", "Period-4\nr ≈ 3.449", "Period-8\nr ≈ 3.544"]
bifurcation_df = pd.DataFrame({"xintercept": bifurcation_r})

# Plot
plot = (
    ggplot(df, aes(x="parameter", y="state", color="regime"))
    + geom_point(size=0.1, alpha=0.6, stroke=0)
    + scale_color_gradient(low="#306998", high="#e3a835")
    + geom_vline(
        aes(xintercept="xintercept"), data=bifurcation_df, linetype="dashed", color="#c44e52", alpha=0.7, size=0.6
    )
    + annotate(
        "text", x=3.0, y=0.97, label=bifurcation_labels[0], size=9, color="#c44e52", ha="right", fontweight="bold"
    )
    + annotate(
        "text", x=3.44, y=0.97, label=bifurcation_labels[1], size=9, color="#c44e52", ha="right", fontweight="bold"
    )
    + annotate(
        "text", x=3.55, y=0.97, label=bifurcation_labels[2], size=9, color="#c44e52", ha="left", fontweight="bold"
    )
    + annotate(
        "label", x=3.82, y=0.15, label="Chaos", size=11, color="#e3a835", fontweight="bold", fill="#ffffff", alpha=0.8
    )
    + annotate(
        "label",
        x=2.7,
        y=0.72,
        label="Stable\nFixed Point",
        size=11,
        color="#306998",
        fontweight="bold",
        fill="#ffffff",
        alpha=0.8,
    )
    + labs(x="Growth Rate (r)", y="Steady-State Population (x)", title="bifurcation-basic · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=np.arange(2.5, 4.1, 0.25))
    + scale_y_continuous(breaks=np.arange(0, 1.1, 0.2))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#2d2d2d"),
        axis_title=element_text(size=20, color="#444444"),
        axis_text=element_text(size=16, color="#666666"),
        panel_grid_major=element_line(color="#e0e0e0", size=0.4),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="#fafafa", color="none"),
        panel_background=element_rect(fill="#fafafa", color="none"),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
