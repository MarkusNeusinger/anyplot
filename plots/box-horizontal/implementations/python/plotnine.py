"""anyplot.ai
box-horizontal: Horizontal Box Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SERVICE = "Service type"  # role: categories
RESPONSE_TIME = "Response time (ms)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
services = {
    "Authentication Service": (120, 25, []),
    "Database Query Handler": (85, 40, [220, 250, 280]),
    "File Storage API": (200, 50, []),
    "Email Notification": (150, 30, []),
    "Payment Gateway": (180, 60, [350, 380]),
}
rows = []
for service, (mean, spread, extremes) in services.items():
    draws = np.append(np.random.normal(mean, spread, 80), extremes)
    rows += [{SERVICE: service, RESPONSE_TIME: max(10, v)} for v in draws]
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
order = df.groupby(SERVICE, sort=False)[RESPONSE_TIME].median().sort_values().index.tolist()
df[SERVICE] = pd.Categorical(df[SERVICE], categories=order, ordered=True)

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.04),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=12, color=INK),
    legend_position="none",
)

plot = (
    ggplot(df, aes(x=SERVICE, y=RESPONSE_TIME, fill=SERVICE))
    + geom_boxplot(color=INK, alpha=0.85, size=0.5, outlier_size=1.8, outlier_alpha=0.8)
    + coord_flip()
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=order)
    + labs(title="box-horizontal · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
