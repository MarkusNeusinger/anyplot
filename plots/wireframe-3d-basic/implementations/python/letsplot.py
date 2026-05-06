""" anyplot.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 94/100 | Created: 2026-05-06
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# First series color
BRAND = "#009E73"

# Generate 3D surface data (ripple function)
np.random.seed(42)
x = np.linspace(-6, 6, 28)
y = np.linspace(-6, 6, 28)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2))


# Isometric projection from 3D to 2D
def isometric_project(x_3d, y_3d, z_3d):
    x_iso = x_3d - y_3d
    y_iso = (x_3d + y_3d) * 0.5 + z_3d
    return x_iso, y_iso


# Create wireframe line segments
lines = []

# X-direction lines (constant y index)
for j in range(X.shape[1]):
    x_2d, y_2d = isometric_project(X[:, j], Y[:, j], Z[:, j])
    for i in range(len(x_2d)):
        lines.append({"x": x_2d[i], "y": y_2d[i], "line": f"x_{j}", "order": i})

# Y-direction lines (constant x index)
for i in range(X.shape[0]):
    x_2d, y_2d = isometric_project(X[i, :], Y[i, :], Z[i, :])
    for j in range(len(x_2d)):
        lines.append({"x": x_2d[j], "y": y_2d[j], "line": f"y_{i}", "order": j})

df = pd.DataFrame(lines)

# Create plot with wireframe lines
plot = (
    ggplot(df, aes(x="x", y="y", group="line"))
    + geom_path(color=BRAND, size=1.2, alpha=0.85)
    + ggsize(1600, 900)
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=24, color=INK, hjust=0.5),
    )
    + labs(title="wireframe-3d-basic · letsplot · anyplot.ai")
)

# Setup and save
LetsPlot.setup_html()

ggsave(plot, f"plot-{THEME}.png", scale=3)
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images to current directory
for ext in ["png", "html"]:
    src = f"lets-plot-images/plot-{THEME}.{ext}"
    dst = f"plot-{THEME}.{ext}"
    if os.path.exists(src):
        shutil.move(src, dst)
