"""pyplots.ai
line-parametric: Parametric Curve Plot
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_equal,
    element_blank,
    element_text,
    facet_wrap,
    geom_path,
    geom_point,
    ggplot,
    labs,
    scale_color_gradientn,
    theme,
    theme_minimal,
)


# Data
n_points = 1000
t_lissajous = np.linspace(0, 2 * np.pi, n_points)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

t_spiral = np.linspace(0, 4 * np.pi, n_points)
x_spiral = t_spiral * np.cos(t_spiral) / (4 * np.pi)
y_spiral = t_spiral * np.sin(t_spiral) / (4 * np.pi)

df = pd.concat(
    [
        pd.DataFrame(
            {"x": x_lissajous, "y": y_lissajous, "t": t_lissajous, "curve": "Lissajous: x = sin(3t), y = sin(2t)"}
        ),
        pd.DataFrame({"x": x_spiral, "y": y_spiral, "t": t_spiral, "curve": "Spiral: x = t·cos(t), y = t·sin(t)"}),
    ],
    ignore_index=True,
)

# Start and end markers
markers = pd.concat(
    [
        pd.DataFrame(
            {
                "x": [x_lissajous[0], x_lissajous[-1]],
                "y": [y_lissajous[0], y_lissajous[-1]],
                "t": [t_lissajous[0], t_lissajous[-1]],
                "curve": "Lissajous: x = sin(3t), y = sin(2t)",
                "label": ["start", "end"],
            }
        ),
        pd.DataFrame(
            {
                "x": [x_spiral[0], x_spiral[-1]],
                "y": [y_spiral[0], y_spiral[-1]],
                "t": [t_spiral[0], t_spiral[-1]],
                "curve": "Spiral: x = t·cos(t), y = t·sin(t)",
                "label": ["start", "end"],
            }
        ),
    ],
    ignore_index=True,
)

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", color="t"))
    + geom_path(aes(group="curve"), size=1.5, alpha=0.85)
    + geom_point(data=markers[markers["label"] == "start"], color="#306998", size=5, shape="o")
    + geom_point(data=markers[markers["label"] == "end"], color="#c0392b", size=5, shape="s")
    + facet_wrap("curve", scales="free")
    + scale_color_gradientn(colors=["#306998", "#5b9bd5", "#f0c040", "#e07b39", "#c0392b"])
    + coord_equal()
    + labs(title="line-parametric · plotnine · pyplots.ai", x="x(t)", y="y(t)", color="Parameter t")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        strip_text=element_text(size=16),
        panel_spacing_x=0.5,
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
