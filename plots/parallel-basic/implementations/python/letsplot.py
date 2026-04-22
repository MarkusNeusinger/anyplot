""" pyplots.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_line,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


LetsPlot.setup_html()

# Data - Iris dataset with 4 dimensions
# Using 30 samples (10 per species) for clarity
data = {
    "sepal_length": [
        5.1,
        4.9,
        4.7,
        4.6,
        5.0,
        5.4,
        4.6,
        5.0,
        4.4,
        4.9,
        7.0,
        6.4,
        6.9,
        5.5,
        6.5,
        5.7,
        6.3,
        4.9,
        6.6,
        5.2,
        6.3,
        5.8,
        7.1,
        6.3,
        6.5,
        7.6,
        4.9,
        7.3,
        6.7,
        7.2,
    ],
    "sepal_width": [
        3.5,
        3.0,
        3.2,
        3.1,
        3.6,
        3.9,
        3.4,
        3.4,
        2.9,
        3.1,
        3.2,
        3.2,
        3.1,
        2.3,
        2.8,
        2.8,
        3.3,
        2.4,
        2.9,
        2.7,
        3.3,
        2.7,
        3.0,
        2.9,
        3.0,
        3.0,
        2.5,
        2.9,
        2.5,
        3.6,
    ],
    "petal_length": [
        1.4,
        1.4,
        1.3,
        1.5,
        1.4,
        1.7,
        1.4,
        1.5,
        1.4,
        1.5,
        4.7,
        4.5,
        4.9,
        4.0,
        4.6,
        4.5,
        4.7,
        3.3,
        4.6,
        3.9,
        6.0,
        5.1,
        5.9,
        5.6,
        5.8,
        6.6,
        4.5,
        6.3,
        5.8,
        6.1,
    ],
    "petal_width": [
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.4,
        0.3,
        0.2,
        0.2,
        0.1,
        1.4,
        1.5,
        1.5,
        1.3,
        1.5,
        1.3,
        1.6,
        1.0,
        1.3,
        1.4,
        2.5,
        1.9,
        2.1,
        1.8,
        2.2,
        2.1,
        1.7,
        1.8,
        1.8,
        2.5,
    ],
    "species": ["Setosa"] * 10 + ["Versicolor"] * 10 + ["Virginica"] * 10,
}

df = pd.DataFrame(data)

# Dimensions to plot (shorter labels to avoid overlap)
dimensions = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
dim_labels = ["Sepal\nLength (cm)", "Sepal\nWidth (cm)", "Petal\nLength (cm)", "Petal\nWidth (cm)"]

# Normalize each dimension to 0-1 range for fair comparison
df_normalized = df.copy()
for dim in dimensions:
    min_val = df[dim].min()
    max_val = df[dim].max()
    df_normalized[dim] = (df[dim] - min_val) / (max_val - min_val)

# Convert to long format for parallel coordinates
line_data = []
for idx, row in df_normalized.iterrows():
    obs_id = idx
    species = row["species"]
    for i, dim in enumerate(dimensions):
        line_data.append({"x": i, "y": row[dim], "observation": obs_id, "species": species})

line_df = pd.DataFrame(line_data)

# Create axis lines data (vertical lines at each x position)
axis_data = []
for i in range(len(dimensions)):
    axis_data.append({"x": i, "y": 0, "xend": i, "yend": 1})

axis_df = pd.DataFrame(axis_data)

# Create label data for dimension names at the bottom
label_data = []
for i, label in enumerate(dim_labels):
    label_data.append({"x": i, "y": -0.12, "label": label})

label_df = pd.DataFrame(label_data)

# Create tick labels for each axis (showing original scale) - only min and max
tick_data = []
for i, dim in enumerate(dimensions):
    min_val = df[dim].min()
    max_val = df[dim].max()
    # Bottom tick (min value) - positioned to the left of axis
    tick_data.append({"x": i - 0.08, "y": 0, "label": f"{min_val:.1f}"})
    # Top tick (max value)
    tick_data.append({"x": i - 0.08, "y": 1, "label": f"{max_val:.1f}"})

tick_df = pd.DataFrame(tick_data)

# Plot
plot = (
    ggplot()
    # Vertical axis lines
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=axis_df, color="#333333", size=2)
    # Data lines connecting observations across dimensions
    + geom_line(aes(x="x", y="y", group="observation", color="species"), data=line_df, size=1.5, alpha=0.7)
    # Color scale using Python Blue, Python Yellow, and a complementary red
    + scale_color_manual(values=["#306998", "#FFD43B", "#DC2626"])
    # Dimension labels at the bottom
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=14, color="#222222")
    # Tick value labels on the left side of axes
    + geom_text(aes(x="x", y="y", label="label"), data=tick_df, size=11, color="#555555", hjust=1)
    # Styling
    + scale_x_continuous(limits=(-0.5, len(dimensions) - 0.5))
    + scale_y_continuous(limits=(-0.28, 1.1))
    + labs(title="parallel-basic · letsplot · pyplots.ai", color="Species")
    + ggsize(1600, 900)
    + theme(
        plot_title=element_text(size=28),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_blank(),
    )
)

# Save (path='.' ensures files are saved in current directory)
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
