""" pyplots.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import Legend, LegendItem
from bokeh.plotting import figure


# Data - Iris-like dataset for multivariate demonstration
np.random.seed(42)

# Generate realistic iris-like measurements for three species
n_per_species = 50

# Setosa: small petals, moderate sepals
setosa = pd.DataFrame(
    {
        "sepal_length": np.random.normal(5.0, 0.35, n_per_species),
        "sepal_width": np.random.normal(3.4, 0.38, n_per_species),
        "petal_length": np.random.normal(1.5, 0.17, n_per_species),
        "petal_width": np.random.normal(0.25, 0.10, n_per_species),
        "species": "setosa",
    }
)

# Versicolor: medium everything
versicolor = pd.DataFrame(
    {
        "sepal_length": np.random.normal(5.9, 0.52, n_per_species),
        "sepal_width": np.random.normal(2.8, 0.31, n_per_species),
        "petal_length": np.random.normal(4.3, 0.47, n_per_species),
        "petal_width": np.random.normal(1.3, 0.20, n_per_species),
        "species": "versicolor",
    }
)

# Virginica: large petals and sepals
virginica = pd.DataFrame(
    {
        "sepal_length": np.random.normal(6.6, 0.64, n_per_species),
        "sepal_width": np.random.normal(3.0, 0.32, n_per_species),
        "petal_length": np.random.normal(5.5, 0.55, n_per_species),
        "petal_width": np.random.normal(2.0, 0.27, n_per_species),
        "species": "virginica",
    }
)

df = pd.concat([setosa, versicolor, virginica], ignore_index=True)

# Normalize numeric columns to [0, 1] for fair comparison across axes
numeric_cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
df_norm = df.copy()
for col in numeric_cols:
    min_val = df[col].min()
    max_val = df[col].max()
    df_norm[col] = (df[col] - min_val) / (max_val - min_val)

# Create figure (4800x2700 px)
p = figure(
    width=4800,
    height=2700,
    title="parallel-basic · bokeh · pyplots.ai",
    x_axis_label="Dimension",
    y_axis_label="Normalized Value",
    x_range=(-0.3, 3.3),
    y_range=(-0.05, 1.10),
)

# Styling for 4800x2700 px canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Define colors for species (Python Blue, Yellow, and a complementary green)
colors = {"setosa": "#306998", "versicolor": "#FFD43B", "virginica": "#4CAF50"}

# X positions for each dimension
x_coords = list(range(len(numeric_cols)))

# Track renderers for legend
renderers_by_species = {}

# Plot parallel coordinates - each line connects values across axes
for _, row in df_norm.iterrows():
    species = row["species"]
    y_coords = [row[col] for col in numeric_cols]
    renderer = p.line(x_coords, y_coords, line_color=colors[species], line_alpha=0.5, line_width=2)
    # Keep one renderer per species for legend
    if species not in renderers_by_species:
        renderers_by_species[species] = renderer

# Create legend
legend_items = []
for species_name in ["setosa", "versicolor", "virginica"]:
    legend_items.append(LegendItem(label=species_name.capitalize(), renderers=[renderers_by_species[species_name]]))

legend = Legend(items=legend_items, location="top_right")
legend.label_text_font_size = "18pt"
legend.title = "Species"
legend.title_text_font_size = "20pt"
p.add_layout(legend)

# Custom x-axis labels with original scale ranges
axis_labels = [
    f"Sepal Length\n({df['sepal_length'].min():.1f}-{df['sepal_length'].max():.1f} cm)",
    f"Sepal Width\n({df['sepal_width'].min():.1f}-{df['sepal_width'].max():.1f} cm)",
    f"Petal Length\n({df['petal_length'].min():.1f}-{df['petal_length'].max():.1f} cm)",
    f"Petal Width\n({df['petal_width'].min():.1f}-{df['petal_width'].max():.1f} cm)",
]
p.xaxis.ticker = x_coords
p.xaxis.major_label_overrides = dict(enumerate(axis_labels))

# Grid styling - subtle
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="parallel-basic · bokeh · pyplots.ai")
