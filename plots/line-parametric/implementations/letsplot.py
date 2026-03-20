"""pyplots.ai
line-parametric: Parametric Curve Plot
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-20
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

# Common theme
common_theme = theme_minimal() + theme(
    axis_text=element_text(size=14),
    axis_title=element_text(size=18),
    plot_title=element_text(size=20, face="bold"),
    legend_text=element_text(size=14),
    legend_title=element_text(size=16),
)

# Plot - Lissajous figure
plot_lissajous = (
    ggplot(df_lissajous, aes(x="x", y="y", color="t"))
    + geom_path(size=1.5, alpha=0.9)
    + geom_point(data=df_lissajous.iloc[[0]], mapping=aes(x="x", y="y"), color="#2D6A4F", size=6, shape=16)
    + geom_point(data=df_lissajous.iloc[[-1]], mapping=aes(x="x", y="y"), color="#E63946", size=6, shape=16)
    + scale_color_gradient(low="#306998", high="#FFD43B", name="t")
    + coord_fixed()
    + labs(x="x(t) = sin(3t)", y="y(t) = sin(2t)", title="Lissajous Figure")
    + common_theme
)

# Plot - Archimedean spiral
plot_spiral = (
    ggplot(df_spiral, aes(x="x", y="y", color="t"))
    + geom_path(size=1.5, alpha=0.9)
    + geom_point(data=df_spiral.iloc[[0]], mapping=aes(x="x", y="y"), color="#2D6A4F", size=6, shape=16)
    + geom_point(data=df_spiral.iloc[[-1]], mapping=aes(x="x", y="y"), color="#E63946", size=6, shape=16)
    + scale_color_gradient(low="#306998", high="#FFD43B", name="t")
    + coord_fixed()
    + labs(x="x(t) = t·cos(t)", y="y(t) = t·sin(t)", title="Archimedean Spiral")
    + common_theme
)

# Combine into side-by-side layout
grid_plot = gggrid([plot_lissajous, plot_spiral], ncol=2)

final_plot = (
    grid_plot
    + ggsize(1600, 900)
    + ggtitle("line-parametric · letsplot · pyplots.ai")
    + theme(plot_title=element_text(size=24, face="bold"))
)

# Save
ggsave(final_plot, "plot.png", path=".", scale=3)
ggsave(final_plot, "plot.html", path=".")
