"""anyplot.ai
streamgraph-basic: Basic Stream Graph
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 88/100 | Created: 2026-08-05
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_ribbon,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)
from scipy.interpolate import make_interp_spline


# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data: monthly streaming hours by music genre over two years
np.random.seed(42)

months = np.arange(24)
genres = ["Pop", "Hip-Hop", "Electronic", "Rock", "Jazz"]
n_months = len(months)
n_genres = len(genres)

data_values = {}
for i, genre in enumerate(genres):
    base = 100 + i * 20
    trend = np.sin(np.linspace(0, 4 * np.pi, n_months) + i) * 30
    noise = np.random.randn(n_months) * 10
    data_values[genre] = np.maximum(base + trend + noise, 20)

values_matrix = np.column_stack([data_values[g] for g in genres])
totals = values_matrix.sum(axis=1)
baseline = -totals / 2

y_bottom = np.zeros((n_months, n_genres))
y_top = np.zeros((n_months, n_genres))
for i in range(n_genres):
    y_bottom[:, i] = baseline if i == 0 else y_top[:, i - 1]
    y_top[:, i] = y_bottom[:, i] + values_matrix[:, i]

# Upsample onto a fine grid with a cubic B-spline for the organic, flowing
# streamgraph curve the spec requires (geom_ribbon otherwise draws straight
# segments between the 24 monthly points).
months_fine = np.linspace(months.min(), months.max(), 240)
plot_data = []
for i, genre in enumerate(genres):
    bottom_smooth = make_interp_spline(months, y_bottom[:, i], k=3)(months_fine)
    top_smooth = make_interp_spline(months, y_top[:, i], k=3)(months_fine)
    for month_val, ymin, ymax in zip(months_fine, bottom_smooth, top_smooth, strict=True):
        plot_data.append({"month": month_val, "genre": genre, "ymin": ymin, "ymax": ymax})

df_plot = pd.DataFrame(plot_data)
df_plot["genre"] = pd.Categorical(df_plot["genre"], categories=genres, ordered=True)

title = "streamgraph-basic · python · plotnine · anyplot.ai"

anyplot_theme = theme(
    figure_size=(8, 4.5),
    text=element_text(size=7),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    axis_title_y=element_blank(),
    axis_text_y=element_blank(),
    plot_title=element_text(size=12, color=INK),
    legend_text=element_text(size=8, color=INK_SOFT),
    legend_title=element_text(size=9, color=INK),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    panel_grid=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    legend_background=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
    legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
)

plot = (
    ggplot(df_plot, aes(x="month", ymin="ymin", ymax="ymax", fill="genre"))
    + geom_ribbon(alpha=0.9)
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + scale_x_continuous(breaks=list(range(0, 24, 6)), labels=["Jan '23", "Jul '23", "Jan '24", "Jul '24"])
    + labs(x="Month", y="", title=title, fill="Genre")
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
