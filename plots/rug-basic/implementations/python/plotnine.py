"""anyplot.ai
rug-basic: Basic Rug Plot
Library: plotnine 0.15.7 | Python 3.13.13
Quality: 85/100 | Updated: 2026-07-25
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_density,
    geom_rug,
    ggplot,
    labs,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
AMBER = "#DDCC77"  # Imprint semantic anchor — warning / caution, used to flag the outlier region

# Data - simulated response times with realistic clustering and gaps
np.random.seed(42)
cluster1 = np.random.normal(150, 20, 40)
cluster2 = np.random.normal(280, 35, 30)
cluster3 = np.random.normal(450, 50, 20)
outliers = np.array([620, 680, 750, 820])

values = np.concatenate([cluster1, cluster2, cluster3, outliers])
df = pd.DataFrame({"response_time": values})
outlier_start = 550  # visual boundary separating the main mass from the sparse tail

# Plot
anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_blank(),
    panel_grid_minor_x=element_blank(),
    panel_grid_major_y=element_blank(),
    panel_grid_minor_y=element_blank(),
    panel_border=element_blank(),
    axis_line_x=element_line(color=INK_SOFT, size=0.5),
    axis_title_x=element_text(size=10, color=INK),
    axis_title_y=element_blank(),
    axis_text_x=element_text(size=8, color=INK_SOFT),
    axis_text_y=element_blank(),
    axis_ticks_major_y=element_blank(),
    plot_title=element_text(size=12, color=INK),
    plot_subtitle=element_text(size=8, color=INK_SOFT),
)

plot = (
    ggplot(df, aes(x="response_time"))
    # Subtle amber tint calls out the sparse outlier tail against the three-cluster mass
    + annotate(
        "rect",
        xmin=outlier_start,
        xmax=float(values.max()) + 40,
        ymin=-float("inf"),
        ymax=float("inf"),
        fill=AMBER,
        alpha=0.08,
    )
    + annotate(
        "text",
        x=outlier_start + 10,
        y=float("inf"),
        label="outliers",
        color=INK_SOFT,
        size=7,
        ha="left",
        va="top",
        fontstyle="italic",
    )
    + geom_density(fill=BRAND, color=BRAND, alpha=0.3, size=1.0)
    + geom_rug(alpha=0.6, sides="b", size=0.8, color=BRAND)
    + scale_x_continuous(expand=(0.03, 0))
    + labs(
        x="Response Time (ms)",
        y="",
        title="rug-basic · plotnine · anyplot.ai",
        subtitle="94 API calls — three latency clusters with a sparse slow-response tail",
    )
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
