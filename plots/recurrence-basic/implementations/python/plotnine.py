""" anyplot.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: plotnine 0.15.5 | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-10
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_equal,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    guide_colorbar,
    guides,
    labs,
    scale_fill_gradient,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy.spatial.distance import cdist


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data — Logistic map near onset of chaos (r=3.82)
np.random.seed(42)
n_steps = 200
r = 3.82
x = np.zeros(n_steps)
x[0] = 0.1
for i in range(1, n_steps):
    x[i] = r * x[i - 1] * (1 - x[i - 1])

# Time-delay embedding (dimension=3, delay=2) — wider delay reveals more structure
embedding_dim = 3
delay = 2
n_embedded = n_steps - (embedding_dim - 1) * delay
embedded = np.array([x[i * delay : i * delay + n_embedded] for i in range(embedding_dim)]).T

# Distance matrix (Euclidean distance in embedding space) and proximity for color mapping
distance_matrix = cdist(embedded, embedded, metric="euclidean")
threshold = 0.12

row_idx, col_idx = np.where(distance_matrix < threshold)
distances = distance_matrix[row_idx, col_idx]
proximity = 1.0 - distances / threshold

df = pd.DataFrame({"Time_i": row_idx, "Time_j": col_idx, "Proximity": proximity})

# Laminar region (vertical/horizontal clusters near t=118-152)
laminar_start, laminar_end = 118, 152

# Plot — color-mapped recurrence plot with Imprint sequential colormap (imprint_seq)
plot = (
    ggplot(df, aes(x="Time_i", y="Time_j", fill="Proximity"))
    + geom_tile(width=1.1, height=1.1)
    + scale_fill_gradient(
        low="#009E73",
        high="#4467A3",
        name="Recurrence\nStrength",
        limits=(0, 1),
        breaks=[0.0, 0.5, 1.0],
        labels=["Weak", "Medium", "Strong"],
    )
    + guides(fill=guide_colorbar(nbin=200))
    + annotate(
        "rect",
        xmin=laminar_start,
        xmax=laminar_end,
        ymin=laminar_start,
        ymax=laminar_end,
        fill="none",
        color="#AE3030",
        size=1.2,
        linetype="dashed",
    )
    + annotate(
        "text",
        x=laminar_end + 5,
        y=laminar_end + 5,
        label="Laminar\nregime",
        ha="left",
        va="bottom",
        size=3.5,
        color="#AE3030",
        fontstyle="italic",
    )
    + scale_x_continuous(
        name="Time Index  (Logistic Map, r = 3.82)", expand=(0.01, 0), breaks=range(0, n_embedded + 1, 40)
    )
    + scale_y_continuous(
        name="Time Index  (Logistic Map, r = 3.82)", expand=(0.01, 0), breaks=range(0, n_embedded + 1, 40)
    )
    + coord_equal(ratio=1)
    + labs(
        title="recurrence-basic · python · plotnine · anyplot.ai",
        subtitle="Diagonal lines → determinism  ·  Dense blocks → regime changes",
    )
    + theme_minimal(base_size=8, base_family="sans-serif")
    + theme(
        figure_size=(6, 6),
        text=element_text(color=INK),
        plot_title=element_text(size=12, ha="center", weight="bold", margin={"b": 4}),
        plot_subtitle=element_text(size=9, ha="center", color=INK_SOFT, margin={"b": 10}),
        axis_title_x=element_text(size=10, margin={"t": 8}),
        axis_title_y=element_text(size=10, margin={"r": 8}),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        axis_text_y=element_text(size=8, color=INK_SOFT),
        axis_ticks_major=element_line(color=INK_SOFT, size=0.4),
        axis_ticks_length=3,
        legend_title=element_text(size=8, weight="bold", color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.3),
        plot_background=element_rect(fill=PAGE_BG, color="none"),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
