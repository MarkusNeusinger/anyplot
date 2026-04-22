""" pyplots.ai
streamgraph-basic: Basic Stream Graph
Library: plotnine 0.15.1 | Python 3.13.11
Quality: 98/100 | Created: 2025-12-14
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_text,
    geom_ribbon,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Data: Monthly streaming hours by music genre over two years
np.random.seed(42)

months = np.arange(24)
genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz"]
n_months = len(months)
n_genres = len(genres)

# Generate realistic streaming data with trends
data_values = {}
for i, genre in enumerate(genres):
    base = 100 + i * 20
    trend = np.sin(np.linspace(0, 4 * np.pi, n_months) + i) * 30
    noise = np.random.randn(n_months) * 10
    data_values[genre] = np.maximum(base + trend + noise, 20)

# Create wide dataframe first
df_wide = pd.DataFrame({"month": months})
for genre in genres:
    df_wide[genre] = data_values[genre]

# Calculate streamgraph positions (centered baseline)
# Stack values and compute symmetric baseline
values_matrix = df_wide[genres].values
totals = values_matrix.sum(axis=1)
baseline = -totals / 2

# Compute y positions for each genre (cumulative)
y_bottom = np.zeros((n_months, n_genres))
y_top = np.zeros((n_months, n_genres))

for i in range(n_genres):
    if i == 0:
        y_bottom[:, i] = baseline
    else:
        y_bottom[:, i] = y_top[:, i - 1]
    y_top[:, i] = y_bottom[:, i] + values_matrix[:, i]

# Create long-form dataframe for plotting
plot_data = []
for i, genre in enumerate(genres):
    for j, month in enumerate(months):
        plot_data.append({"month": month, "genre": genre, "ymin": y_bottom[j, i], "ymax": y_top[j, i]})

df_plot = pd.DataFrame(plot_data)
df_plot["genre"] = pd.Categorical(df_plot["genre"], categories=genres, ordered=True)

# Colors - harmonious palette for adjacent areas
colors = ["#306998", "#FFD43B", "#FF6B6B", "#4ECDC4", "#9B59B6"]

# Create streamgraph using geom_ribbon
plot = (
    ggplot(df_plot, aes(x="month", ymin="ymin", ymax="ymax", fill="genre"))
    + geom_ribbon(alpha=0.85)
    + scale_fill_manual(values=colors)
    + scale_x_continuous(breaks=list(range(0, 24, 6)), labels=["Jan '23", "Jul '23", "Jan '24", "Jul '24"])
    + labs(x="Month", y="Streaming Hours", title="streamgraph-basic · plotnine · pyplots.ai", fill="Genre")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
    )
)

plot.save("plot.png", dpi=300)
