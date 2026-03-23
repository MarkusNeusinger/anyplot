""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_equal,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_path,
    geom_point,
    ggplot,
    guide_colorbar,
    guide_legend,
    guides,
    labs,
    scale_color_gradientn,
    scale_fill_manual,
    scale_shape_manual,
    theme,
    theme_void,
)


# Data — normalize t to [0, 1] per curve so both panels use the full color gradient
n_points = 1000
t_lissajous = np.linspace(0, 2 * np.pi, n_points)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)
t_norm_liss = np.linspace(0, 1, n_points)

t_spiral = np.linspace(0, 4 * np.pi, n_points)
x_spiral = t_spiral * np.cos(t_spiral) / (4 * np.pi)
y_spiral = t_spiral * np.sin(t_spiral) / (4 * np.pi)
t_norm_spiral = np.linspace(0, 1, n_points)

df = pd.concat(
    [
        pd.DataFrame(
            {"x": x_lissajous, "y": y_lissajous, "t_norm": t_norm_liss, "curve": "Lissajous · x = sin(3t), y = sin(2t)"}
        ),
        pd.DataFrame(
            {"x": x_spiral, "y": y_spiral, "t_norm": t_norm_spiral, "curve": "Spiral · x = t·cos(t), y = t·sin(t)"}
        ),
    ],
    ignore_index=True,
)

# Start and end markers
start_pts = pd.DataFrame(
    {
        "x": [x_lissajous[0], x_spiral[0]],
        "y": [y_lissajous[0], y_spiral[0]],
        "t_norm": [0.0, 0.0],
        "curve": ["Lissajous · x = sin(3t), y = sin(2t)", "Spiral · x = t·cos(t), y = t·sin(t)"],
        "endpoint": ["Start (t = 0)", "Start (t = 0)"],
    }
)

end_pts = pd.DataFrame(
    {
        "x": [x_lissajous[-1], x_spiral[-1]],
        "y": [y_lissajous[-1], y_spiral[-1]],
        "t_norm": [1.0, 1.0],
        "curve": ["Lissajous · x = sin(3t), y = sin(2t)", "Spiral · x = t·cos(t), y = t·sin(t)"],
        "endpoint": ["End (t = tmax)", "End (t = tmax)"],
    }
)

markers = pd.concat([start_pts, end_pts], ignore_index=True)

# Gradient palette — deep navy through teal, gold, to vivid rose
gradient_colors = ["#0d1b2a", "#1b4965", "#5fa8d3", "#bee9e8", "#ffd166", "#ef476f"]

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", color="t_norm"))
    + geom_path(aes(group="curve"), size=2.5, alpha=0.94)
    + geom_point(
        aes(shape="endpoint", fill="endpoint"), data=markers, color="#1a1a2e", size=8, stroke=1.2, show_legend=True
    )
    + scale_shape_manual(name="Direction", values={"Start (t = 0)": "o", "End (t = tmax)": "D"})
    + scale_fill_manual(name="Direction", values={"Start (t = 0)": "#306998", "End (t = tmax)": "#ef476f"})
    + facet_wrap("curve", scales="free")
    + scale_color_gradientn(
        name="Parameter t",
        colors=gradient_colors,
        guide=guide_colorbar(nbin=200),
        labels=["0", "¼", "½", "¾", "tmax"],
        breaks=[0.0, 0.25, 0.5, 0.75, 1.0],
    )
    + coord_equal()
    + labs(title="line-parametric · plotnine · pyplots.ai", x="Horizontal Position  x(t)", y="Vertical Position  y(t)")
    + guides(shape=guide_legend(order=2), fill=guide_legend(order=2))
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=26, weight="bold", color="#0d1b2a", margin={"b": 14}),
        axis_title_x=element_text(size=20, color="#333333", margin={"t": 10}),
        axis_title_y=element_text(size=20, color="#333333", margin={"r": 10}),
        axis_text=element_text(size=16, color="#555555"),
        axis_ticks=element_blank(),
        legend_title=element_text(size=17, weight="bold", color="#0d1b2a"),
        legend_text=element_text(size=16, color="#333333"),
        legend_key=element_rect(fill="white", color="white"),
        legend_background=element_rect(fill="#fafafa", color="#e0e0e0", size=0.5),
        legend_box_margin=6,
        strip_text=element_text(size=17, weight="bold", color="#0d1b2a", margin={"b": 8}),
        strip_background=element_rect(fill="#f0f4f8", color="none"),
        panel_spacing_x=0.15,
        panel_grid_major=element_line(color="#e8e8e8", size=0.3, linetype="dashed"),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="white", color="none"),
        plot_background=element_rect(fill="white", color="none"),
        plot_margin=0.01,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
