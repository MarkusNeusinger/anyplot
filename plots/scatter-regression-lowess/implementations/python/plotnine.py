"""anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 97/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SPAN = 0.4  # LOWESS bandwidth (fraction of points per local fit), within the spec's 0.3-0.5

# Columns: set these to your table's column names
DOSE = "Drug dose (log10 mg/L)"  # role: x
RESPONSE = "Cell viability inhibited (%)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("dose_response.csv")
rng = np.random.default_rng(7)
n_points = 220
dose = rng.uniform(-2, 2, n_points)
# Sigmoidal (Hill-type) dose-response with a shallow plateau bump and noise that peaks mid-curve
hill = 100 / (1 + 10 ** (1.6 * (0.15 - dose)))
noise = rng.normal(0, 4 + 8 * np.exp(-((dose - 0.15) ** 2)), n_points)
response = np.clip(hill + noise + 3 * np.sin(2.5 * dose), 0, 100)
df = pd.DataFrame({DOSE: dose, RESPONSE: response})

# Plot: reads only df and the constants above
anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=12),
)

plot = (
    ggplot(df, aes(x=DOSE, y=RESPONSE))
    + geom_point(color=IMPRINT_PALETTE[0], alpha=0.6, size=2.5)
    + geom_smooth(method="lowess", span=SPAN, color=IMPRINT_PALETTE[1], size=1.4, se=False)
    + labs(title="LOWESS dose-response · scatter-regression-lowess · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
