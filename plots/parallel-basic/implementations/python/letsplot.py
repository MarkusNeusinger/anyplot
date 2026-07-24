"""anyplot.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: letsplot 4.9.0 | Python 3.14.4
Quality: pending | Updated: 2026-07-24
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
    scale_alpha_identity,
    scale_color_manual,
    scale_size_identity,
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

# Imprint palette positions 1-3 — first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

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

# Fix the Imprint color order explicitly (Setosa always gets brand green,
# regardless of row/draw order) — see default-style-guide.md "First series
# is ALWAYS #009E73"
species_order = ["Setosa", "Versicolor", "Virginica"]
line_df["species"] = pd.Categorical(line_df["species"], categories=species_order, ordered=True)

# Setosa shows the sharpest separation on petal dimensions — rendered heavier
# and more opaque than the other species, and drawn last (on top), so it
# reads as the visual focal point.
focus_species = "Setosa"
line_df["line_size"] = (line_df["species"] == focus_species).map({True: 1.3, False: 0.65})
line_df["line_alpha"] = (line_df["species"] == focus_species).map({True: 0.9, False: 0.5})
line_df = pd.concat([line_df[line_df["species"] != focus_species], line_df[line_df["species"] == focus_species]])

# Create axis lines data (vertical lines at each x position)
axis_data = []
for i in range(len(dimensions)):
    axis_data.append({"x": i, "y": 0, "xend": i, "yend": 1})

axis_df = pd.DataFrame(axis_data)

# Horizontal rules tying the axis tops and bottoms together into one frame
frame_df = pd.DataFrame(
    {"x": [-0.3, -0.3], "y": [0, 1], "xend": [len(dimensions) - 0.7, len(dimensions) - 0.7], "yend": [0, 1]}
)

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
    plot_title=element_text(color=INK, size=14),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=9),
    legend_title=element_text(color=INK, size=10),
)

# Plot
plot = (
    ggplot()
    # Vertical axis lines (theme-adaptive color)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=axis_df, color=INK_SOFT, size=1)
    # Subtle top/bottom rule tying all axes into one frame
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=frame_df, color=INK_SOFT, size=0.5, alpha=0.3)
    # Data lines connecting observations across dimensions — Setosa rendered
    # heavier/more opaque (line_size, line_alpha) as the storytelling focal point
    + geom_line(
        aes(x="x", y="y", group="observation", color="species", size="line_size", alpha="line_alpha"), data=line_df
    )
    # Imprint palette — first series is brand green; size/alpha are literal
    # values already computed above, not separate legend-worthy aesthetics
    + scale_color_manual(values=IMPRINT)
    + scale_size_identity()
    + scale_alpha_identity()
    # Dimension labels at the bottom (theme-adaptive color, size matched to base ggsize(800,450))
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=10, color=INK)
    # Tick value labels on the left side of axes (theme-adaptive color)
    + geom_text(aes(x="x", y="y", label="label"), data=tick_df, size=8, color=INK_SOFT, hjust=1)
    # Styling
    + scale_x_continuous(limits=(-0.5, len(dimensions) - 0.5))
    + scale_y_continuous(limits=(-0.32, 1.1))
    + labs(title="parallel-basic · python · letsplot · anyplot.ai", color="Species")
    + ggsize(800, 450)
    + anyplot_theme
)

# Save with theme-named output files
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
