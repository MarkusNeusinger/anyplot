""" pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-14
"""

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
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy.spatial.distance import cdist


# Data - Logistic map near onset of chaos (r=3.82)
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

# Distance matrix (Euclidean distance in embedding space)
distance_matrix = cdist(embedded, embedded, metric="euclidean")
threshold = 0.12

# Build long-form DataFrame with proximity for color mapping
row_idx, col_idx = np.where(distance_matrix < threshold)
distances = distance_matrix[row_idx, col_idx]
proximity = 1.0 - distances / threshold

df = pd.DataFrame({"Time_i": row_idx, "Time_j": col_idx, "Proximity": proximity})

# Identify laminar region (vertical/horizontal clusters near t=120-150)
laminar_start, laminar_end = 118, 152

# Plot - color-mapped recurrence plot with storytelling
plot = (
    ggplot(df, aes(x="Time_i", y="Time_j", fill="Proximity"))
    + geom_tile(width=1.1, height=1.1)
    + scale_fill_gradientn(
        colors=["#d1e5f0", "#67a9cf", "#2166ac", "#053061"],
        name="Recurrence\nStrength",
        limits=(0, 1),
        breaks=[0.0, 0.5, 1.0],
        labels=["Weak", "Medium", "Strong"],
    )
    + guides(fill=guide_colorbar(nbin=200))
    # Highlight laminar region with a subtle rectangle
    + annotate(
        "rect",
        xmin=laminar_start,
        xmax=laminar_end,
        ymin=laminar_start,
        ymax=laminar_end,
        fill="none",
        color="#d6604d",
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
        size=13,
        color="#d6604d",
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
        title="recurrence-basic · plotnine · pyplots.ai",
        subtitle="Diagonal lines → determinism  ·  Dense blocks → regime changes",
    )
    + theme_minimal(base_size=14, base_family="sans-serif")
    + theme(
        figure_size=(14, 12),
        text=element_text(color="#2d2d2d"),
        plot_title=element_text(size=24, ha="center", weight="bold", margin={"b": 4}),
        plot_subtitle=element_text(size=15, ha="center", color="#555555", margin={"b": 14}),
        axis_title_x=element_text(size=20, margin={"t": 10}),
        axis_title_y=element_text(size=20, margin={"r": 10}),
        axis_text_x=element_text(size=16, color="#444444"),
        axis_text_y=element_text(size=16, color="#444444"),
        axis_ticks_major=element_line(color="#aaaaaa", size=0.4),
        axis_ticks_length=5,
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_background=element_rect(fill="#fafaf7", color="none"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="white", color="#999999", size=0.3),
        plot_background=element_rect(fill="#fafaf7", color="none"),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
