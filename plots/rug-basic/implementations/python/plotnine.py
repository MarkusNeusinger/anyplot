"""anyplot.ai
rug-basic: Basic Rug Plot
Library: plotnine | Python 3.13
Quality: pending | Updated: 2026-04-30
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rug,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - simulated response times with realistic clustering and gaps
np.random.seed(42)
cluster1 = np.random.normal(150, 20, 40)
cluster2 = np.random.normal(280, 35, 30)
cluster3 = np.random.normal(450, 50, 20)
outliers = np.array([620, 680, 750, 820])

values = np.concatenate([cluster1, cluster2, cluster3, outliers])
df = pd.DataFrame({"response_time": values})

# Plot
anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_blank(),
    panel_grid_minor_x=element_blank(),
    panel_grid_major_y=element_blank(),
    panel_grid_minor_y=element_blank(),
    panel_border=element_blank(),
    axis_line_x=element_line(color=INK_SOFT, size=0.8),
    axis_title_x=element_text(size=20, color=INK),
    axis_title_y=element_blank(),
    axis_text_x=element_text(size=16, color=INK_SOFT),
    axis_text_y=element_blank(),
    axis_ticks_major_y=element_blank(),
    plot_title=element_text(size=24, color=INK),
)

plot = (
    ggplot(df, aes(x="response_time"))
    + geom_rug(alpha=0.6, sides="b", size=1.5, color=BRAND)
    + labs(x="Response Time (ms)", y="", title="rug-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
