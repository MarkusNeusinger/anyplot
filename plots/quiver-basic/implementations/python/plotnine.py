"""anyplot.ai
quiver-basic: Basic Quiver Plot
Library: plotnine 0.15.3 | Python 3.13.13
Quality: 84/100 | Updated: 2026-04-29
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    arrow,
    coord_equal,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_segment,
    ggplot,
    labs,
    scale_color_cmap,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: 15x15 grid rotation flow field (u = -y, v = x)
grid_size = 15
x_vals = np.linspace(-3, 3, grid_size)
y_vals = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x_vals, y_vals)
x = X.flatten()
y = Y.flatten()

# Rotation field: u = -y, v = x (counter-clockwise rotation)
u = -y
v = x

# Magnitude for color encoding
magnitude = np.sqrt(u**2 + v**2)

# Scale arrows for visibility without overlap
scale = 0.25
u_scaled = u / (magnitude + 0.1) * scale * magnitude
v_scaled = v / (magnitude + 0.1) * scale * magnitude

# DataFrame with segment start/end and magnitude
df = pd.DataFrame({"x": x, "y": y, "xend": x + u_scaled, "yend": y + v_scaled, "magnitude": magnitude})

# Plot
anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=16),
)

plot = (
    ggplot(df, aes(x="x", y="y", xend="xend", yend="yend", color="magnitude"))
    + geom_segment(arrow=arrow(length=0.15, type="closed"), size=1.2)
    + scale_color_cmap(cmap_name="viridis", name="Magnitude")
    + labs(x="East (km)", y="North (km)", title="quiver-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + coord_equal()
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
