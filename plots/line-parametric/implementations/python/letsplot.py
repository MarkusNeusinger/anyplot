""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Lissajous figure: x = sin(3t), y = sin(2t)
t_lissajous = np.linspace(0, 2 * np.pi, 1000)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

df_lissajous = pd.DataFrame({"x": x_lissajous, "y": y_lissajous, "t": t_lissajous})

# Data - Spiral: x = t*cos(t), y = t*sin(t)
t_spiral = np.linspace(0, 4 * np.pi, 1000)
x_spiral = t_spiral * np.cos(t_spiral)
y_spiral = t_spiral * np.sin(t_spiral)

df_spiral = pd.DataFrame({"x": x_spiral, "y": y_spiral, "t": t_spiral})

# Refined theme - remove spines, subtle grid, generous whitespace
refined_theme = theme(
    axis_text=element_text(size=16, color="#555555"),
    axis_title=element_text(size=20, color="#333333"),
    plot_title=element_text(size=22, face="bold", color="#1a1a2e"),
    legend_text=element_text(size=16),
    legend_title=element_text(size=16, face="bold"),
    panel_grid_major=element_line(color="#e8e8e8", size=0.5),
    panel_grid_minor=element_blank(),
    axis_line=element_blank(),
    axis_ticks=element_blank(),
    plot_background=element_rect(fill="white", color="white"),
    panel_background=element_rect(fill="#fcfcfc", color="#e0e0e0", size=0.5),
    legend_background=element_rect(fill="white", color="#e0e0e0", size=0.5),
)

# Colorblind-safe markers: dark blue (start) and orange (end)
start_color = "#084C4C"
end_color = "#C0392B"

# Plot - Lissajous figure (closed, self-intersecting - the "complex" curve)
plot_lissajous = (
    ggplot(df_lissajous, aes(x="x", y="y", color="t"))
    + geom_path(size=2.0, alpha=0.85, tooltips=layer_tooltips().line("t = @t").format("t", ".2f"))
    + geom_point(data=df_lissajous.iloc[[0]], mapping=aes(x="x", y="y"), color=start_color, size=8, shape=16)
    + geom_point(data=df_lissajous.iloc[[-1]], mapping=aes(x="x", y="y"), color=end_color, size=8, shape=17)
    + scale_color_gradient(low="#0D6E6E", high="#D4A017", name="t (rad)", format=".1f")
    + coord_fixed()
    + labs(x="x(t) = sin(3t)", y="y(t) = sin(2t)", title="Lissajous Figure  ·  closed, self-intersecting")
    + refined_theme
)

# Plot - Archimedean spiral (open, expanding - the "growth" curve)
plot_spiral = (
    ggplot(df_spiral, aes(x="x", y="y", color="t"))
    + geom_path(size=1.8, alpha=0.85, tooltips=layer_tooltips().line("t = @t").format("t", ".2f"))
    + geom_point(data=df_spiral.iloc[[0]], mapping=aes(x="x", y="y"), color=start_color, size=8, shape=16)
    + geom_point(data=df_spiral.iloc[[-1]], mapping=aes(x="x", y="y"), color=end_color, size=8, shape=17)
    + scale_color_gradient(low="#0D6E6E", high="#D4A017", name="t (rad)", format=".1f")
    + coord_fixed()
    + scale_x_continuous(limits=[-14, 14])
    + scale_y_continuous(limits=[-14, 14])
    + labs(x="x(t) = t·cos(t)", y="y(t) = t·sin(t)", title="Archimedean Spiral  ·  expanding outward")
    + refined_theme
)

# Combine with gggrid - letsplot's distinctive multi-plot layout
grid_plot = gggrid([plot_lissajous, plot_spiral], ncol=2)

final_plot = (
    grid_plot
    + ggsize(1600, 900)
    + ggtitle("line-parametric · letsplot · pyplots.ai")
    + theme(plot_title=element_text(size=24, face="bold", color="#1a1a2e"))
)

# Save
ggsave(final_plot, "plot.png", path=".", scale=3)
ggsave(final_plot, "plot.html", path=".")
