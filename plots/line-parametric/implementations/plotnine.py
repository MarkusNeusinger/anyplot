"""pyplots.ai
line-parametric: Parametric Curve Plot
Library: plotnine 0.15.3 | Python 3.14.3
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
    guide_legend,
    guides,
    labs,
    scale_color_gradientn,
    scale_fill_manual,
    scale_shape_manual,
    theme,
    theme_void,
)


# Data
n_points = 1000
t_lissajous = np.linspace(0, 1.92 * np.pi, n_points)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

t_spiral = np.linspace(0, 4 * np.pi, n_points)
x_spiral = t_spiral * np.cos(t_spiral) / (4 * np.pi)
y_spiral = t_spiral * np.sin(t_spiral) / (4 * np.pi)

df = pd.concat(
    [
        pd.DataFrame(
            {"x": x_lissajous, "y": y_lissajous, "t": t_lissajous, "curve": "Lissajous · x = sin(3t), y = sin(2t)"}
        ),
        pd.DataFrame({"x": x_spiral, "y": y_spiral, "t": t_spiral, "curve": "Spiral · x = t·cos(t), y = t·sin(t)"}),
    ],
    ignore_index=True,
)

# Start and end markers with distinct colors
start_pts = pd.DataFrame(
    {
        "x": [x_lissajous[0], x_spiral[0]],
        "y": [y_lissajous[0], y_spiral[0]],
        "t": [t_lissajous[0], t_spiral[0]],
        "curve": ["Lissajous · x = sin(3t), y = sin(2t)", "Spiral · x = t·cos(t), y = t·sin(t)"],
        "endpoint": ["Start", "Start"],
    }
)

end_pts = pd.DataFrame(
    {
        "x": [x_lissajous[-1], x_spiral[-1]],
        "y": [y_lissajous[-1], y_spiral[-1]],
        "t": [t_lissajous[-1], t_spiral[-1]],
        "curve": ["Lissajous · x = sin(3t), y = sin(2t)", "Spiral · x = t·cos(t), y = t·sin(t)"],
        "endpoint": ["End", "End"],
    }
)

markers = pd.concat([start_pts, end_pts], ignore_index=True)

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", color="t"))
    + geom_path(aes(group="curve"), size=2.2, alpha=0.92)
    + geom_point(
        aes(shape="endpoint", fill="endpoint"), data=markers, color="#1a1a2e", size=7, stroke=1.0, show_legend=True
    )
    + scale_shape_manual(name="Direction", values={"Start": "o", "End": "D"})
    + scale_fill_manual(name="Direction", values={"Start": "#306998", "End": "#ef476f"})
    + facet_wrap("curve", scales="free")
    + scale_color_gradientn(
        name="Parameter t", colors=["#0d1b2a", "#1b4965", "#5fa8d3", "#bee9e8", "#ffd166", "#ef476f"]
    )
    + coord_equal()
    + labs(title="line-parametric · plotnine · pyplots.ai", x="Horizontal Position  x(t)", y="Vertical Position  y(t)")
    + guides(shape=guide_legend(order=2), fill=guide_legend(order=2))
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#1a1a2e", margin={"b": 12}),
        axis_title_x=element_text(size=20, color="#444444", margin={"t": 10}),
        axis_title_y=element_text(size=20, color="#444444", margin={"r": 10}),
        axis_text=element_text(size=15, color="#666666"),
        axis_ticks=element_blank(),
        legend_title=element_text(size=17, weight="bold", color="#1a1a2e"),
        legend_text=element_text(size=14, color="#333333"),
        legend_key=element_rect(fill="white", color="white"),
        legend_background=element_rect(fill="#fafafa", color="#e0e0e0", size=0.5),
        legend_box_margin=8,
        strip_text=element_text(size=16, weight="bold", color="#1a1a2e", margin={"b": 8}),
        strip_background=element_rect(fill="#f5f5f5", color="none"),
        panel_spacing_x=0.25,
        panel_grid_major=element_line(color="#ececec", size=0.3, linetype="dashed"),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="white", color="none"),
        plot_background=element_rect(fill="white", color="none"),
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
