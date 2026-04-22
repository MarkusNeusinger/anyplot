""" pyplots.ai
streamgraph-basic: Basic Stream Graph
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - monthly streaming hours by music genre over two years
np.random.seed(42)
n_months = 24
genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz"]
n_genres = len(genres)

# Generate smooth trends for each genre with distinct patterns
raw_values = {}
for i, genre in enumerate(genres):
    base = 100 + 50 * np.sin(np.linspace(0, 4 * np.pi, n_months) + i * 0.7)
    trend = np.linspace(0, 25, n_months) * (1 if i % 2 == 0 else -0.6)
    noise = np.random.randn(n_months) * 8
    raw_values[genre] = np.clip(base + trend + noise, 25, None)

# Compute streamgraph positions (centered around baseline)
values_matrix = np.array([raw_values[g] for g in genres])
total_per_month = values_matrix.sum(axis=0)
baseline_offset = -total_per_month / 2

# Build dataframe with ymin/ymax for ribbon geometry
data = []
for month_idx in range(n_months):
    cumulative = baseline_offset[month_idx]
    for genre_idx, genre in enumerate(genres):
        ymin = cumulative
        ymax = cumulative + values_matrix[genre_idx, month_idx]
        data.append({"month": month_idx, "genre": genre, "ymin": ymin, "ymax": ymax})
        cumulative = ymax

df = pd.DataFrame(data)

# Create streamgraph using geom_ribbon for precise ymin/ymax control
plot = (
    ggplot(df, aes(x="month", fill="genre"))  # noqa: F405
    + geom_ribbon(aes(ymin="ymin", ymax="ymax"), alpha=0.9)  # noqa: F405
    + scale_fill_manual(  # noqa: F405
        values=["#306998", "#FFD43B", "#38BDF8", "#A78BFA", "#FB923C"]
    )
    + scale_x_continuous(  # noqa: F405
        breaks=[0, 6, 12, 18, 23], labels=["Jan '23", "Jul '23", "Jan '24", "Jul '24", "Dec '24"]
    )
    + labs(  # noqa: F405
        x="Month", y="Streaming Hours", fill="Genre", title="streamgraph-basic · lets-plot · pyplots.ai"
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_title=element_text(size=18),  # noqa: F405
        axis_text_y=element_blank(),  # noqa: F405
        axis_ticks_y=element_blank(),  # noqa: F405
        panel_grid_major_y=element_blank(),  # noqa: F405
        panel_grid_minor_y=element_blank(),  # noqa: F405
        panel_grid_major_x=element_line(  # noqa: F405
            color="#CCCCCC", size=0.5, linetype="dashed"
        ),
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename="plot.html", path=".")
