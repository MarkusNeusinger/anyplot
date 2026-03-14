"""pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-14
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_equal,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy.spatial.distance import cdist


# Data - Logistic map near onset of chaos (r=3.82)
np.random.seed(42)
n_steps = 300
r = 3.82
x = np.zeros(n_steps)
x[0] = 0.1
for i in range(1, n_steps):
    x[i] = r * x[i - 1] * (1 - x[i - 1])

# Time-delay embedding (dimension=3, delay=1)
embedding_dim = 3
delay = 1
n_embedded = n_steps - (embedding_dim - 1) * delay
embedded = np.array([x[i * delay : i * delay + n_embedded] for i in range(embedding_dim)]).T

# Distance matrix and binary recurrence (Euclidean distance < threshold)
distance_matrix = cdist(embedded, embedded, metric="euclidean")
threshold = 0.15
recurrence_matrix = distance_matrix < threshold

# Build long-form DataFrame from upper triangle + diagonal for symmetric plot
row_idx, col_idx = np.where(recurrence_matrix)
df = pd.DataFrame({"Time_i": row_idx, "Time_j": col_idx})

# Plot
plot = (
    ggplot(df, aes(x="Time_i", y="Time_j"))
    + geom_tile(fill="#1a3a5c", width=1, height=1)
    + scale_x_continuous(name="Time Index", expand=(0, 0), breaks=range(0, n_embedded + 1, 50))
    + scale_y_continuous(name="Time Index", expand=(0, 0), breaks=range(0, n_embedded + 1, 50))
    + coord_equal()
    + labs(title="recurrence-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(10, 10),
        text=element_text(family="sans-serif"),
        plot_title=element_text(size=22, ha="center", weight="bold", margin={"b": 8}),
        axis_title_x=element_text(size=18, margin={"t": 10}),
        axis_title_y=element_text(size=18, margin={"r": 10}),
        axis_text_x=element_text(size=14),
        axis_text_y=element_text(size=14),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#f5f5f0", color="none"),
        plot_background=element_rect(fill="white", color="none"),
        plot_margin=0.02,
    )
)

plot.save("plot.png", dpi=300, verbose=False)
