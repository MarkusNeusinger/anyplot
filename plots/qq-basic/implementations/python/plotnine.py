"""anyplot.ai
qq-basic: Basic Q-Q Plot
Library: plotnine | Python 3.13
Quality: pending | Updated: 2026-04-27
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    ggplot,
    labs,
    stat_qq,
    stat_qq_line,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - sample with slight right skew to demonstrate Q-Q diagnostic capability
np.random.seed(42)
sample = np.concatenate([np.random.randn(80) * 15 + 50, np.random.randn(20) * 10 + 75])
df = pd.DataFrame({"sample": sample})

# Plot
plot = (
    ggplot(df, aes(sample="sample"))
    + stat_qq_line(color=INK_SOFT, size=1.2, linetype="dashed")
    + stat_qq(color=BRAND, alpha=0.7, size=4)
    + labs(x="Theoretical Quantiles (Standard Normal)", y="Sample Quantiles", title="qq-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        axis_title=element_text(color=INK, size=20),
        axis_text=element_text(color=INK_SOFT, size=16),
        plot_title=element_text(color=INK, size=24),
        axis_line=element_line(color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
