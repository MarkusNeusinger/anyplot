"""anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-13
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_errorbar,
    geom_point,
    ggplot,
    labs,
    scale_x_discrete,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single series uses position 1
BRAND = "#009E73"

# Columns: set these to your table's column names
FERTILIZER = "Fertilizer"  # role: x
CROP_YIELD = "Wheat yield (t/ha)"  # role: y
ERROR_LOWER = "Error below (t/ha)"  # role: error_lower
ERROR_UPPER = "Error above (t/ha)"  # role: error_upper

# Data: replace this block with your own table, for example df = pd.read_csv("yields.csv")
# Field trial: wheat yield per fertilizer with a skewed 95% interval
df = pd.DataFrame(
    {
        FERTILIZER: ["Control", "Compost", "Urea", "NPK blend", "Slow-release"],
        CROP_YIELD: [3.2, 4.6, 6.1, 7.4, 6.6],
        ERROR_LOWER: [0.5, 0.7, 1.1, 0.8, 0.4],
        ERROR_UPPER: [0.9, 0.5, 0.6, 1.4, 0.9],
    }
)

# Plot: reads only df and the constants above
df["ymin"] = df[CROP_YIELD] - df[ERROR_LOWER]
df["ymax"] = df[CROP_YIELD] + df[ERROR_UPPER]

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(alpha=0.0),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=12, color=INK),
    plot_caption=element_text(size=8, color=INK_SOFT),
)

plot = (
    ggplot(df, aes(x=FERTILIZER, y=CROP_YIELD))
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.25, size=1.0, color=BRAND)
    + geom_point(size=3, color=BRAND)
    + scale_x_discrete(limits=df[FERTILIZER].unique().tolist())
    + labs(
        title="errorbar-asymmetric · python · plotnine · anyplot.ai",
        caption="Points: mean yield. Bars: asymmetric 95% confidence interval.",
    )
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
