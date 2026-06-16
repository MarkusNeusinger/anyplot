""" anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 97/100 | Updated: 2026-05-14
"""

import os
import sys

import numpy as np
import pandas as pd


venv_path = "/home/runner/work/anyplot/anyplot/.venv/lib/python3.13/site-packages"
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

from plotnine import (  # noqa: E402
    aes,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_smooth,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
ACCENT = "#C475FD"

# Data - create complex non-linear relationship (crop yield vs temperature)
np.random.seed(42)
n_points = 150

# Temperature range (x) - realistic agricultural context
x = np.linspace(5, 35, n_points)

# Yield (y) - peaks around 20-25°C, drops at extremes (realistic crop response)
# Complex non-linear pattern: quadratic-like with some local variation
y_base = -0.5 * (x - 22) ** 2 + 80  # Peak around 22°C
y_noise = np.random.normal(0, 8, n_points)  # Natural variation
y = y_base + y_noise + 3 * np.sin(x / 3)  # Add subtle local pattern

# Ensure positive yields
y = np.clip(y, 5, None)

# Create DataFrame
df = pd.DataFrame({"temperature": x, "yield": y})

# Theme configuration
anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24),
    text=element_text(size=14),
)

# Create plot with scatter points and LOWESS smooth
plot = (
    ggplot(df, aes(x="temperature", y="yield"))
    + geom_point(color=BRAND, alpha=0.6, size=3)
    + geom_smooth(method="lowess", span=0.4, color=ACCENT, size=2.5, se=False)
    + labs(
        x="Temperature (°C)", y="Crop Yield (tons/hectare)", title="scatter-regression-lowess · plotnine · anyplot.ai"
    )
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
