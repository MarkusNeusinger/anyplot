""" anyplot.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: letsplot 4.9.0 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-27
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
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

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]

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
    label_data.append({"x": i, "y": -0.15, "label": label})

label_df = pd.DataFrame(label_data)

# Create tick labels for each axis (showing original scale) - only min and max
tick_data = []
for i, dim in enumerate(dimensions):
    min_val = df[dim].min()
    max_val = df[dim].max()
    tick_data.append({"x": i - 0.08, "y": 0, "label": f"{min_val:.1f}"})
    tick_data.append({"x": i - 0.08, "y": 1, "label": f"{max_val:.1f}"})

tick_df = pd.DataFrame(tick_data)

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.2),
    panel_grid_minor=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    panel_grid=element_blank(),
    plot_title=element_text(color=INK, size=28),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=18),
    legend_title=element_text(color=INK, size=20),
)

# Plot
plot = (
    ggplot()
    # Vertical axis lines (theme-adaptive color)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=axis_df, color=INK_SOFT, size=2)
    # Data lines connecting observations across dimensions
    + geom_line(aes(x="x", y="y", group="observation", color="species"), data=line_df, size=1.5, alpha=0.7)
    # Okabe-Ito palette — first series is brand green
    + scale_color_manual(values=OKABE_ITO)
    # Dimension labels at the bottom (theme-adaptive color, size >=20pt)
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=20, color=INK)
    # Tick value labels on the left side of axes (theme-adaptive color, size >=16pt)
    + geom_text(aes(x="x", y="y", label="label"), data=tick_df, size=16, color=INK_SOFT, hjust=1)
    # Styling
    + scale_x_continuous(limits=(-0.5, len(dimensions) - 0.5))
    + scale_y_continuous(limits=(-0.32, 1.1))
    + labs(title="parallel-basic · letsplot · anyplot.ai", color="Species")
    + ggsize(1600, 900)
    + anyplot_theme
)

# Save with theme-named output files
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
